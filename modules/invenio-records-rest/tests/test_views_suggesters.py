# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Basic tests."""

import json
from unittest.mock import ANY, call

import pytest
from flask import url_for
from invenio_search.engine import dsl


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                suggesters=dict(
                    text=dict(completion=dict(field="suggest_title")),
                    text_byyear=dict(
                        completion=dict(field="suggest_byyear", context="year")
                    ),
                    text_filtered_source=dict(
                        _source=["control_number"],
                        completion=dict(field="suggest_title"),
                    ),
                )
            )
        )
    ],
    indirect=["app"],
)
def test_valid_suggest(
    app, db, search, item_type, indexed_records, mock_search_execute, mocker
):
    """Test VALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        suggest_mocker = mocker.spy(dsl.Search, "suggest")
        source_mocker = mocker.spy(dsl.Search, "source")
        # Valid simple completion suggester
        mocker.patch.object(
            dsl.Search,
            "execute",
            return_value=mock_search_execute(
                {
                    "suggest": {
                        "text": "test_value",
                        "text_filtered_source": {"_source": "1"},
                        "suggest_title": "test_title",
                        "text_byyear": "test_byyear",
                        "year": 1990,
                    }
                }
            ),
        )
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"), query_string={"text": "Back"}
        )
        assert res.status_code == 200
        suggest_mocker.assert_has_calls(
            [call(ANY, "text", "Back", completion=dict(field="suggest_title"))]
        )
        data = json.loads(res.get_data(as_text=True))
        assert data == {"text": "test_value"}

        # Valid simple completion suggester with source filtering for ES5
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"),
            query_string={"text_filtered_source": "Back"},
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data == {"text_filtered_source": {"_source": "1"}}
        source_mocker.assert_called_once_with(ANY, ["control_number"])
        suggest_mocker.assert_has_calls(
            [
                call(
                    ANY,
                    "text_filtered_source",
                    "Back",
                    completion={"field": "suggest_title"},
                )
            ]
        )

        # Valid simple completion suggester with size
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"),
            query_string={"text": "Back", "size": 1},
        )
        data = json.loads(res.get_data(as_text=True))
        assert data == {"text": "test_value"}

        suggest_mocker.assert_has_calls(
            [
                call(
                    ANY,
                    "text",
                    "Back",
                    completion={"field": "suggest_title", "size": 1},
                )
            ]
        )

        # Valid context suggester
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"),
            query_string={"text_byyear": "Back", "year": "2015"},
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data == {"text_byyear": "test_byyear"}

        suggest_mocker.assert_has_calls(
            [
                call(
                    ANY,
                    "text_byyear",
                    "Back",
                    completion={"field": "suggest_byyear", "context": {"year": "2015"}},
                )
            ]
        )

        # Missing context for context suggester
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"),
            query_string={"text_byyear": "Back"},
        )
        assert res.status_code == 400

        # Missing missing and invalid suggester
        res = client.get(
            url_for("invenio_records_rest.recid_suggest"),
            query_string={"invalid": "Back"},
        )
        assert res.status_code == 400
