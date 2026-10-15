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

import pytest
from marshmallow import ValidationError

from weko_workflow.schema.marshmallow import SaveActivitySchema


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_schema.py::test_save_activity_schema_shared_role_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_schema_shared_role_ids(app):
    """SaveActivitySchema の shared_role_ids."""
    base = {"activity_id": "A-1", "title": "t"}

    # 1. 文字列配列の受信(shared_user_ids の定義は変更しない)
    data = SaveActivitySchema().load(dict(
        base, shared_user_ids=[{"user": 1}], shared_role_ids=["12"])).data
    assert data["shared_role_ids"] == ["12"]
    assert data["shared_user_ids"] == [{"user": 1}]

    # 2. None は ValidationError とならない(allow_none=True)
    data = SaveActivitySchema().load(dict(
        base, shared_user_ids=[], shared_role_ids=None)).data
    assert data["shared_role_ids"] is None

    # 3. 未送信は ValidationError とならない(missing=None)
    data = SaveActivitySchema().load(dict(base, shared_user_ids=[])).data
    assert data["shared_role_ids"] is None

    # 4. 文字列以外の要素は ValidationError(marshmallow 既定の文言)
    with pytest.raises(ValidationError) as excinfo:
        SaveActivitySchema().load(dict(
            base, shared_user_ids=[], shared_role_ids=[12]))
    assert "Not a valid string." in str(excinfo.value)
