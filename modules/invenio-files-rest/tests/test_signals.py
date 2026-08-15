# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test file signals."""

from io import BytesIO

from flask import url_for
from .testutils import login_user

from invenio_files_rest.signals import file_deleted, file_uploaded


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_signals.py::test_signals -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_signals(app, client, headers, bucket_with_record, permissions, user_activity_log_partition_table, mocker):
    """Test file_uploaded and file_deleted signals."""

    mocker.patch("sqlalchemy.orm.scoping.scoped_session.remove")
    login_user(client, permissions["bucket"])
    key = "myfile.txt"
    data = b"content of my file"
    object_url = url_for("invenio_files_rest.object_api", bucket_id=bucket_with_record.id, key=key)

    calls = []

    def upload_listener(sender, obj=None):
        calls.append("file-uploaded")

    def delete_listener(sender, obj=None):
        calls.append("file-deleted")

    file_uploaded.connect(upload_listener, weak=False)
    file_deleted.connect(delete_listener, weak=False)
    try:
        client.put(
            object_url,
            input_stream=BytesIO(data),
            headers={"Content-Type": "application/octet-stream"},
        )
        client.delete(object_url)
        assert calls == ["file-uploaded", "file-deleted"]
    finally:
        file_uploaded.disconnect(upload_listener)
        file_deleted.disconnect(delete_listener)
