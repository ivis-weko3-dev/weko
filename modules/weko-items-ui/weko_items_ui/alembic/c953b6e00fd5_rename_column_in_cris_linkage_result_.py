#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Rename column in cris_linkage_result table"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c953b6e00fd5'
down_revision = '61ac7d4b0c06'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Rename column `failed_log` to `message` in `cris_linkage_result` table
    op.alter_column('cris_linkage_result', 'failed_log', new_column_name='message')
    


def downgrade():
    """Downgrade database."""
    # Rename column `message` to `failed_log` in `cris_linkage_result` table
    op.alter_column('cris_linkage_result', 'message', new_column_name='failed_log')
