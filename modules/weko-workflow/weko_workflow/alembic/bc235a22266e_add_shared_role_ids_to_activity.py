# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add shared_role_ids to workflow_activity."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bc235a22266e'
down_revision = 'b1f5618360f5'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # DDL等で先行適用済みの場合は何もしない
    columns = [
        column['name'] for column in
        sa.inspect(op.get_bind()).get_columns('workflow_activity')
    ]
    if 'shared_role_ids' not in columns:
        op.add_column(
            'workflow_activity',
            sa.Column(
                'shared_role_ids',
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True
            )
        )


def downgrade():
    """Downgrade database.

    The proxy posting groups saved in the column are lost.
    """
    op.drop_column('workflow_activity', 'shared_role_ids')
