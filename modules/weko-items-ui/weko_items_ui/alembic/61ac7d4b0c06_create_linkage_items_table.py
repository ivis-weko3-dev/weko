#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create linkage_items table"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '61ac7d4b0c06'
down_revision = '9dc005064658'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'linkage_items',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('item_id', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('external_item_id', sa.Text(), nullable=False),
        sa.Column('external_system', sa.Text(), nullable=False),
        sa.Column('permalink', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=1), nullable=False, server_default="R"),

        sa.UniqueConstraint('item_id', 'external_item_id', 'external_system')
    )


def downgrade():
    """Downgrade database."""
    op.drop_table('linkage_items')
