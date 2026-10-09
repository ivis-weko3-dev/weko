# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator test cases."""

import os
import pytest

from flask import Flask
from invenio_cache import InvenioCache, current_cache
from invenio_db import db as db_

from invenio_oaiserver import current_oaiserver, InvenioOAIServer
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.query import OAINoRecordsMatchError, get_records
from invenio_oaiserver.receivers import after_update_oai_set
from invenio_oaiserver.percolator import (
    _create_percolator_mapping,
    _new_percolator,
    _delete_percolator,
    create_percolate_query,
    percolate_query,
    find_sets_for_record
)
from invenio_search import current_search

from .helpers import create_record, run_after_insert_oai_set

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

@pytest.fixture()
def test0(search_app, db, without_oaiset_signals, schema):
    record = create_record(
        search_app,
        {"title": ["Test0"], "title_statement": {"title": "Test0"},
         "$schema": schema},
    )
    current_search.flush_and_refresh("weko-item-v1.0.0")
    return record


def create_oaiset(name, title_pattern):
    oaiset = OAISet(
        spec=name,
        # the percolator mapping only knows the `title` field
        search_pattern=f"title:{title_pattern}",
        system_created=False,
    )
    db_.session.add(oaiset)
    db_.session.commit()
    run_after_insert_oai_set()
    current_search.flush_and_refresh("weko-item-v1.0.0-percolators")

    return oaiset


def test_set_with_no_records(db, without_oaiset_signals, schema, search_app):
    _ = create_oaiset("test", "Test0")
    # the record index has to exist for the query to be executed
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")


def test_empty_set(without_oaiset_signals, test0):
    _ = create_oaiset("test", "Test1")
    with pytest.raises(OAINoRecordsMatchError):
        get_records(set="test")


def test_set_with_records(app, without_oaiset_signals, test0, schema):
    # create extra record
    record = create_record(
        app,
        {"title": ["Test1"], "title_statement": {"title": "Test1"},
         "$schema": schema},
    )
    current_search.flush_and_refresh("weko-item-v1.0.0")

    # create and query set
    _ = create_oaiset("test", "Test0")
    assert find_sets_for_record(test0) == ["test"]
    assert find_sets_for_record(record) == []


def test_search_pattern_change(without_oaiset_signals, test0):
    """Test search pattern change."""
    # create set
    oaiset = create_oaiset("test", "Test0")
    # check record is in set
    assert find_sets_for_record(test0) == ["test"]

    # change search pattern
    oaiset.search_pattern = "title:Test1"
    db_.session.merge(oaiset)
    db_.session.commit()
    after_update_oai_set(None, None, oaiset)
    current_search.flush_and_refresh("weko-item-v1.0.0-percolators")
    # check record is not in set
    assert find_sets_for_record(test0) == []

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_create_percolator_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_create_percolator_mapping(app,mocker):
    search_ext = mocker.MagicMock()
    search_ext.client.indices.exists.return_value = False
    app.extensions["invenio-search"] = search_ext

    index = "test-weko-item-v1.0.0"
    mapping_path = os.path.join(
        os.path.dirname(__file__), "data", "os-v2", "records",
        "record-v1.0.0.json"
    )
    _create_percolator_mapping(index, mapping_path)
    create_kwargs = search_ext.client.indices.create.call_args.kwargs
    assert create_kwargs["index"].endswith("-percolators")
    properties = create_kwargs["body"]["mappings"]["properties"]
    assert properties["query"] == {"type": "percolator"}

    search_ext.client.indices.exists.return_value = True
    _create_percolator_mapping(index, mapping_path)
    assert search_ext.client.indices.create.call_count == 1

def test_create_percolate_query():
    query = create_percolate_query(documents=[{"title_statement": {"title": "t"}}])
    must = query["query"]["bool"]["must"]
    assert must[0]["percolate"]["field"] == "query"
    assert must[0]["percolate"]["documents"] == [{"title_statement": {"title": "t"}}]

    query = create_percolate_query(
        documents=[{"a": 1}], percolator_ids=["oaiset-1", "oaiset-2"])
    must = query["query"]["bool"]["must"]
    assert must[0]["percolate"]["field"] == "query"
    assert must[1] == {"ids": {"values": ["oaiset-1", "oaiset-2"]}}

    query = create_percolate_query(
        document_search_ids=["id1"], document_search_indices=["idx1"])
    must = query["query"]["bool"]["must"]
    assert must[0]["percolate"]["id"] == "id1"
    assert must[0]["percolate"]["index"] == "idx1"
    assert must[0]["percolate"]["name"] == "idx1:id1"

    with pytest.raises(Exception):
        create_percolate_query()

    with pytest.raises(Exception):
        create_percolate_query(
            document_search_ids=["id1"], document_search_indices=[])

def test_percolate_query(mocker):
    documents = [{"title_statement": {"title": "t"}}]
    scan = mocker.patch(
        "invenio_oaiserver.percolator.search.helpers.scan",
        return_value=iter([{"_id": "oaiset-1"}]))

    result = list(percolate_query("idx-percolators", documents=documents))

    assert result == [{"_id": "oaiset-1"}]
    kwargs = scan.call_args.kwargs
    assert kwargs["index"] == "idx-percolators"
    must = kwargs["query"]["query"]["bool"]["must"]
    assert must[0]["percolate"]["documents"] == documents


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_new_percolator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_new_percolator(search_app,db,without_oaiset_signals,mocker):
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern="test_pettern",
        system_created=False)

    db.session.add(oai)
    db.session.commit()
    _new_percolator(None,None)
    _new_percolator(spec=oai.spec,search_pattern=oai.search_pattern)

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_percolator.py::test_delete_percolator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_delete_percolator(search_app,mocker):

    # spec is None
    _delete_percolator(None,None)

    _delete_percolator("test","test")


def test_sets_cache(instance_path):
    app = Flask("test_app",instance_path=instance_path)
    app.config.update(
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        OAISERVER_CACHE_KEY="DynamicOAISets::",
        OAISERVER_REGISTER_RECORD_SIGNALS=False,
        OAISERVER_REGISTER_SET_SIGNALS=False,
        )
    InvenioCache(app)
    with app.app_context():
        current_cache.delete("DynamicOAISets::")
        InvenioOAIServer(app,cache=current_cache)

        assert current_oaiserver.sets is None

        current_oaiserver.sets = ["test"]
        assert current_oaiserver.sets == ["test"]

        current_cache.delete("DynamicOAISets::")
        assert current_oaiserver.sets is None


def test_find_sets_for_record(app,mocker):
    mocker.patch("invenio_oaiserver.percolator._create_percolator_mapping")
    mocker.patch(
        "invenio_oaiserver.percolator._build_percolator_index_name",
        return_value="test-weko-item-v1.0.0-percolators")
    indexer = mocker.patch("invenio_oaiserver.percolator.RecordIndexer")
    indexer.return_value._record_to_index.return_value = "test-weko-item-v1.0.0"
    mocker.patch(
        "invenio_oaiserver.percolator.percolate_query",
        return_value=[
            {"_id": "oaiset-test",
             "fields": {"_percolator_document_slot": [0]}},
            {"_id": "notoaiset-test",
             "fields": {"_percolator_document_slot": [0]}},
        ])

    record = {"_oai": {"sets": []}}
    assert find_sets_for_record(record) == ["test"]

    mocker.patch(
        "invenio_oaiserver.percolator.percolate_query", return_value=[])
