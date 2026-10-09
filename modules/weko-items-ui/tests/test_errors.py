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

"""Tests of weko_items_ui.errors."""

import json

from invenio_rest.errors import RESTException

from weko_items_ui.errors import SharedRoleValidationError


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_errors.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

# class SharedRoleValidationError(RESTException):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_errors.py::test_shared_role_validation_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_shared_role_validation_error(app):
    """RESTException を継承し code=400、description に拒否の文言を保持する."""
    description = "Specified group is not allowed as a proxy posting group."
    error = SharedRoleValidationError(description=description)

    assert issubclass(SharedRoleValidationError, RESTException)
    assert error.code == 400
    assert error.description == description

    response = error.get_response()
    assert response.status_code == 400
    assert json.loads(response.get_data(as_text=True)) == {
        "status": 400,
        "message": description,
    }
