# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Views module tests."""

from flask import render_template_string

from invenio_previewer.views import preview, dbsession_clean
from unittest.mock import patch, MagicMock


# .tox/c1/bin/pytest --cov=invenio_previewer tests/test_views.py::test_view_macro_file_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-previewer/.tox/c1/tmp
def test_view_macro_file_list(testapp):
    """Test file list macro."""
    with testapp.test_request_context():
        files = [
            {
                "key": "test1.txt",
                "size": 10,
                "date": "2016-07-12",
            },
            {
                "key": "test2.txt",
                "size": 12000000,
                "date": "2016-07-12",
            },
        ]

        pid = {"pid_value": 1}

        result = render_template_string(
            """
            {%- from "invenio_previewer/macros.html" import file_list %}
            {{ file_list(files, pid) }}
            """,
            files=files,
            pid=pid,
        )

        assert 'href="/record/1/files/test1.txt?download=1"' in result
        assert 'href="/record/1/files/test2.txt?download=1"' in result
        if testapp.config["APP_THEME"] == ["bootstrap3"]:
            assert '<td class="nowrap">10 Bytes</td>' in result
            assert '<td class="nowrap">12.0 MB</td>' in result
        else:
            assert "<td>10 Bytes</td>" in result
            assert "<td>12.0 MB</td>" in result



def test_previewable_test(testapp):
    """Test template test."""
    file = {"type": "md"}
    template = (
        "{% if file.type is previewable %}Previewable"
        "{% else %}Not previewable{% endif %}"
    )
    assert render_template_string(template, file=file) == "Previewable"

    file["type"] = "no"
    assert render_template_string(template, file=file) == "Not previewable"

    file["type"] = "pdf"
    assert render_template_string(template, file=file) == "Previewable"

    file["type"] = ""
    assert render_template_string(template, file=file) == "Not previewable"

# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=invenio_previewer tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-previewer/.tox/c1/tmp
def test_dbsession_clean(app, db):
    exception = "ValueError"
    dbsession_clean(exception=exception)

    exception = None
    dbsession_clean(exception=exception)
