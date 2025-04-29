# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Index prefixing tests."""

import json
from unittest.mock import patch

from invenio_records_rest.errors import PIDResolveRESTError

from .conftest import IndexFlusher
from helpers import assert_hits_len, get_json, record_url
from invenio_search import current_search, current_search_client


def test_index_creation(app):
    """Sanity check for index creation."""
    suffix = current_search.current_suffix
    es_aliases = current_search_client.indices.get_alias()
    # Keys are the indices
    assert set(es_aliases.keys()) is not None

    aliases = set()
    for index_info in es_aliases.values():
        aliases |= set(index_info.get("aliases", {}).keys())
    assert aliases == {
        'tenant1-weko',
        'tenant1-stats-index',
        'tenant1-events-stats-record-view',
        'tenant1-authors-author-v1.0.0',
        'tenant1-events-stats-celery-task',
        'tenant1-events-stats-item-create',
        '.kibana',
        'tenant1-stats-record-view',
        'tenant1-events-stats-file-preview',
        'tenant1-stats-top-view',
        'tenant1-events-stats-index',
        'tenant1-events-stats-search',
        'tenant1-stats-search',
        'tenant1-stats-celery-task',
        'tenant1-events-stats-top-view',
        'tenant1-stats-file-download',
        'tenant1-stats-file-preview',
        'tenant1-events-stats-file-download',
        'tenant1-authors',
        'tenant1-weko-item-v1.0.0',
        'tenant1-stats-item-create'
    }


@patch("invenio_records_rest.views.db.session.remove")
def test_api_views(mock_remove, app, db, test_data, search_url, search_class, search_index, item_type, mock_itemtypes):
    """Test REST API views behavior."""
    # suffix = current_search.current_suffix

    with app.test_client() as client:
        HEADERS = [
            ("Accept", "application/json"),
            ("Content-Type", "application/json"),
        ]

        # Create record
        res = client.post(search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        recid = get_json(res)["id"]
        assert res.status_code == 201

        # Flush and check indices
        IndexFlusher(search_class).flush_and_wait()
        es_client = search_index
        index_name = "test-weko"

        result = es_client.search(index=index_name)
        assert len(result["hits"]["hits"]) == 1
        record_doc = result["hits"]["hits"][0]
        assert record_doc["_index"] == "test-weko-item-v1.0.0"

        # Fetch the record
        assert client.get(record_url(recid)).status_code == 200
        # Record shows up in search
        res = client.get(search_url)
        assert_hits_len(res, 1)

        # Delete the record
        res = client.delete(record_url(recid))
        assert res.status_code == 204
        IndexFlusher(search_class).flush_and_wait()
        result = es_client.search(index=index_name)
        # result = current_search.search(index="test-invenio-records-rest")
        assert len(result["hits"]["hits"]) == 0

        # Deleted record should return 410
        with patch("invenio_records_rest.views.RecordResource.get", side_effect=PIDResolveRESTError):
            res = client.get(record_url(recid))
            res.status_code == 410
        # Record doesn't show up in search
        res = client.get(search_url)
        assert_hits_len(res, 0)
