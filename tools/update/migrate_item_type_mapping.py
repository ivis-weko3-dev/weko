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

from contextlib import contextmanager

from flask import current_app
from flask_sqlalchemy.model import DefaultMeta as Meta
from sqlalchemy import func

from invenio_db import db
from weko_records.models import (
    timestamp_before_update, Timestamp, ItemTypeMapping
)


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
    return bool(duplicate_count > 0)


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
        print("Versioned table for ItemTypeMapping not found.")
        return

    if has_duplicate_item_type_ids():
        print("Not need to migrate item_type_mapping.")
        return
    print("Migrating item_type_mapping to versioning...")

    with without_before_update_timestamp():
        pass


if __name__ == "__main__":
    main()
