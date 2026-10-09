# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""

import importlib.util
import os
from unittest.mock import MagicMock, patch

from sqlalchemy.dialects import postgresql

from weko_workflow.models import Activity

from .helpers_proxy import create_proxy_activity


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_models.py::test_activity_shared_role_ids_column -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_activity_shared_role_ids_column(app, db, users, workflow):
    """Activity.shared_role_ids カラムが nullable で、既定値が設定されない."""
    from invenio_accounts.models import User
    user = User.query.get(users[0]["id"])

    def fetch(activity):
        db.session.expire_all()
        return Activity.query.filter_by(activity_id=activity.activity_id).one()

    # 1. 指定せずに保存して再取得: 既定値を設定しない(None)
    activity = create_proxy_activity(workflow, user)
    assert fetch(activity).shared_role_ids is None

    # 2. shared_role_ids を指定して保存して再取得
    activity = create_proxy_activity(workflow, user, shared_role_ids=["12", "35"])
    assert fetch(activity).shared_role_ids == ["12", "35"]

    # 3. カラム定義: nullable で、PostgreSQL のバリアントが JSONB
    column = Activity.__table__.columns["shared_role_ids"]
    assert column.nullable is True
    assert isinstance(column.type.mapping["postgresql"], postgresql.JSONB)
    assert column.default is None or column.default.arg is None


# alembic マイグレーション bc235a22266e の upgrade/downgrade
# ここでは DB を使わずに、呼び出す操作のみを確認する
def _load_migration():
    path = os.path.join(
        os.path.dirname(__file__), os.pardir, "weko_workflow", "alembic",
        "bc235a22266e_add_shared_role_ids_to_activity.py")
    spec = importlib.util.spec_from_file_location("bc235a22266e", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_models.py::test_alembic_shared_role_ids_upgrade_downgrade -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_alembic_shared_role_ids_upgrade_downgrade():
    """alembic マイグレーション bc235a22266e の upgrade/downgrade."""
    migration = _load_migration()
    assert migration.revision == "bc235a22266e"
    assert migration.down_revision == "b1f5618360f5"

    # upgrade: カラムが無ければ nullable な JSONB カラムを追加する
    with patch.object(migration, "op") as mock_op, \
            patch.object(migration.sa, "inspect") as mock_inspect:
        mock_inspect.return_value.get_columns.return_value = [{"name": "id"}]
        migration.upgrade()
        mock_op.add_column.assert_called_once()
        table_name, column = mock_op.add_column.call_args[0]
        assert table_name == "workflow_activity"
        assert column.name == "shared_role_ids"
        assert column.nullable is True
        assert isinstance(column.type, postgresql.JSONB)

    # upgrade: DDL 等で先行適用済みの場合は何もしない
    with patch.object(migration, "op") as mock_op, \
            patch.object(migration.sa, "inspect") as mock_inspect:
        mock_inspect.return_value.get_columns.return_value = [
            {"name": "id"}, {"name": "shared_role_ids"}]
        migration.upgrade()
        mock_op.add_column.assert_not_called()

    # downgrade: カラムを削除する
    with patch.object(migration, "op") as mock_op:
        migration.downgrade()
        mock_op.drop_column.assert_called_once_with(
            "workflow_activity", "shared_role_ids")
