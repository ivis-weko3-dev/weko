#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""make_stats_bookmark_type_nullable"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0109e99b50da'
down_revision = '5e6f25bbf456'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column(
        'stats_events',
        'type',
        existing_type=sa.String(length=50),
        nullable=True,
    )

    op.alter_column(
        'stats_aggregation',
        'type',
        existing_type=sa.String(length=50),
        nullable=True,
    )

    op.alter_column(
        'stats_bookmark',
        'type',
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade():
    """Downgrade database."""
    stats_events = sa.sql.table(
        'stats_events',
        sa.Column('type', sa.String(length=50)),
    )

    op.execute(
        stats_events.update()
        .where(stats_events.c.type.is_(None))
        .values(type='')
    )

    op.alter_column(
        'stats_events',
        'type',
        existing_type=sa.String(length=50),
        nullable=False,
    )

    stats_aggregation = sa.sql.table(
        'stats_aggregation',
        sa.Column('type', sa.String(length=50)),
    )

    op.execute(
        stats_aggregation.update()
        .where(stats_aggregation.c.type.is_(None))
        .values(type='')
    )

    op.alter_column(
        'stats_aggregation',
        'type',
        existing_type=sa.String(length=50),
        nullable=False,
    )

    stats_bookmark = sa.sql.table(
        'stats_bookmark',
        sa.Column('type', sa.String(length=50)),
    )

    op.execute(
        stats_bookmark.update()
        .where(stats_bookmark.c.type.is_(None))
        .values(type='')
    )

    op.alter_column(
        'stats_bookmark',
        'type',
        existing_type=sa.String(length=50),
        nullable=False,
    )
