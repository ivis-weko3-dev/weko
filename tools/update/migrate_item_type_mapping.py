# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 National Institute of Informatics.
# WEKO is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Migrate item_type_mapping table to versioning.

This script is used to migrate the `item_type_mapping` table and
`item_type_mapping_version`.

>>> invenio shell tools/update/migrate_item_type_mapping.py

"""

import traceback
from contextlib import contextmanager

from flask import current_app
from flask_sqlalchemy.model import DefaultMeta as Meta
from sqlalchemy import func, text

from invenio_db import db
from weko_records.models import (
    timestamp_before_update, Timestamp, ItemTypeMapping
)


def info(msg):
    print(f"[INFO]  {msg}")

def warn(msg):
    print(f"\033[43m[WARN]\033[0m {msg}")

def error(msg):
    print(f"\033[41m[ERROR]\033[0m {msg}")


def get_versioned_model(master):
    """Get the versioned table for the given master table."""
    manager = current_app.extensions["invenio-db"].versioning_manager
    if not manager.transaction_cls:
        return None

    versioned_table = manager.version_class_map.get(master, None)
    return versioned_table if isinstance(versioned_table, Meta) else None


def has_duplicate_item_type_ids():
    """Check if there are duplicate item_type_id values in ItemTypeMapping."""
    duplicate_count = (
        db.session.query(func.count(ItemTypeMapping.item_type_id))
        .group_by(ItemTypeMapping.item_type_id)
        .having(func.count(ItemTypeMapping.item_type_id) > 1)
        .count()
    )
    info(f"{duplicate_count} Item Type Mapping needs to be migrated.")
    return bool(duplicate_count > 0)


@contextmanager
def atomic_migration_stream(*models):
    """Context manager to create temporary tables for migration."""
    for model in models:
        info(f"Creating temporary table for {model.__tablename__}...")
        db.session.execute(text(f"""
            CREATE TABLE {model.__tablename__}_tmp AS
            SELECT * FROM {model.__tablename__};
        """))

    db.session.commit()

    try:
        stream = db.engine.execute(
            text(f"SELECT * FROM {models[0].__tablename__}_tmp ORDER BY id ASC"),
            execution_options={"stream_results": True})
        yield stream
    except Exception as e:
        error("Failed to process.")
        traceback.print_exc()

        for model in models:
            db.session.execute(text(f"""
                TRUNCATE TABLE {model.__tablename__};
                INSERT INTO {model.__tablename__}
                SELECT * FROM {model.__tablename__}_tmp;
            """))
        db.session.commit()
        warn("Rolled back changes.")

    finally:
        stream.close()
        for model in models:
            db.session.execute(text(f"""
                DROP TABLE IF EXISTS {model.__tablename__}_tmp;
            """))
        db.session.commit()


@contextmanager
def without_before_update_timestamp():
    """Context manager to temporarily disable the before_update timestamp."""
    db.event.remove(Timestamp, "before_update", timestamp_before_update)
    try:
        yield
    finally:
        db.event.listen(
            Timestamp, "before_update", timestamp_before_update, propagate=True
        )


def main():
    """Main function to migrate item_type_mapping."""

    ItemTypeMappingVersion = get_versioned_model(ItemTypeMapping)
    if not ItemTypeMappingVersion:
        error("Versioned table for ItemTypeMapping not found.")
        return

    if not has_duplicate_item_type_ids():
        info("Not need to migrate item_type_mapping.")
        return


    with without_before_update_timestamp(), \
        atomic_migration_stream(ItemTypeMapping, ItemTypeMappingVersion) as tmp_record_stream:

        db.session.execute(text(f"""
            TRUNCATE TABLE {ItemTypeMapping.__tablename__};
            TRUNCATE TABLE {ItemTypeMappingVersion.__tablename__};
        """))
        db.session.commit()
        info("Cleared original tables.")


if __name__ == "__main__":
    main()
