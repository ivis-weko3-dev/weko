# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test deposit UI views."""
# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_ui.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
import json
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_deposit.api import Deposit
from invenio_db import db


def test_index_new_guest(app):
    """Test index view."""
    with app.test_request_context():
        index_url = url_for('invenio_deposit_ui.index')
        new_url = url_for('invenio_deposit_ui.new')
    with app.test_client() as client:
        for u in [index_url, new_url]:
            res = client.get(u)
            assert res.status_code == 302
            assert '/login/' in res.location

def test_index(app, users):
    """Test index view."""
    app.jinja_env.filters["format_sortoptions"] = (
        lambda x: json.dumps({"options": x})
    )
    with app.test_request_context():
        url = url_for('invenio_deposit_ui.index')
    with app.test_client() as client:
        login_user_via_session(client, email=users[0]['email'])
        res = client.get(url)
        assert res.status_code == 200

def test_index_new(app, users):
    """Test index view."""
    app.jinja_env.filters["format_sortoptions"] = (
        lambda x: json.dumps({"options": x})
    )
    with app.test_request_context():
        url = url_for('invenio_deposit_ui.new')
    with app.test_client() as client:
        login_user_via_session(client, email=users[0]['email'])
        res = client.get(url)
        assert res.status_code == 200

def test_edit(app, users, deposit):
    """Test edit view."""
    deposit_id = deposit.id
    with app.test_request_context():
        edit_url = url_for(
            'invenio_deposit_ui.depid', pid_value=deposit.pid.pid_value)
    with app.test_client() as client:
        res = client.get(edit_url)
        assert res.status_code == 200


def test_edit_deleted_pid(app, users, deposit):
    """Test edit view."""
    deposit_id = deposit.id
    with app.test_request_context():
        edit_url = url_for(
            'invenio_deposit_ui.depid', pid_value=deposit.pid.pid_value)
    with app.test_client() as client:
        # Test tombstone
        deposit = Deposit.get_record(deposit_id)
        deposit.pid.delete()
        db.session.commit()
        res = client.get(edit_url)
        assert res.status_code == 410