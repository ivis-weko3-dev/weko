# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Delete record tests."""

from flask import url_for
from helpers import get_json, record_url
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from mock import patch
from sqlalchemy.exc import SQLAlchemyError


def test_valid_delete(app, indexed_records):
    """Test VALID record delete request (DELETE .../records/<record_id>)."""
    records = [
        (pid.pid_value, pid.object_uuid, record_url(pid))
        for pid, record in indexed_records
    ]
    # Test with and without headers
    for i, headers in enumerate([[], [("Accept", "video/mp4")]]):
        pid_value, object_uuid, url = records[i]
        with app.test_client() as client:
            assert (
                PersistentIdentifier.query.filter_by(pid_value=pid_value).first().status
                == PIDStatus.REGISTERED
            )
            res = client.delete(url, headers=headers)
            assert res.status_code == 204
            assert (
                PersistentIdentifier.query.filter_by(pid_value=pid_value).first().status
                == PIDStatus.DELETED
            )
            assert RecordMetadata.query.filter_by(id=object_uuid).first().json is None

            res = client.get(url)
            assert res.status_code == 410


def test_delete_deleted(app, indexed_records):
    """Test deleting a perviously deleted record."""
    pid, record = indexed_records[0]
    url = record_url(pid)

    with app.test_client() as client:
        res = client.delete(url)
        assert res.status_code == 204
        res = client.delete(url)
        assert res.status_code == 410
        data = get_json(res)
        assert "message" in data
        assert data["status"] == 410


def test_delete_notfound(app, indexed_records):
    """Test INVALID record delete request (DELETE .../records/<record_id>)."""
    with app.test_client() as client:
        # Check that GET with non existing id will return 404
        res = client.delete(url_for("invenio_records_rest.recid_item", pid_value=0))
        assert res.status_code == 404


def test_delete_with_sqldatabase_error(app, indexed_records):
    """Test VALID record delete request (GET .../records/<record_id>)."""
    pid, record = indexed_records[0]
    url = record_url(pid)
    object_uuid = pid.object_uuid

    with app.test_client() as client:

        def raise_error():
            raise SQLAlchemyError()

        # Force an SQLAlchemy error that will rollback the transaction.
        assert (
            PersistentIdentifier.query.filter_by(pid_value="1").first().status
            == PIDStatus.REGISTERED
        )
        with patch.object(PersistentIdentifier, "delete", side_effect=raise_error):
            res = client.delete(url)
            assert res.status_code == 204
            assert (
                PersistentIdentifier.query.filter_by(pid_value="1").first().status
                == PIDStatus.REGISTERED
            )
            assert (
                RecordMetadata.query.filter_by(id=object_uuid).first().json is not None
            )

    with app.test_client() as client:
        res = client.get(url)
        assert res.status_code == 200
