# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Facets tests."""
import pytest
from unittest.mock import patch
from flask import Flask, g
from flask_principal import Identity
from invenio_rest.errors import RESTValidationError
from invenio_search.engine import dsl
from werkzeug.datastructures import MultiDict
from weko_admin.models import AdminSettings,FacetSearchSetting
from invenio_records_rest.facets import (
    _aggregations,
    _create_filter_dsl,
    _post_filter,
    _query_filter,
    default_facets_factory,
    range_filter,
    terms_filter,
)


def test_terms_filter():
    """Test terms filter."""
    f = terms_filter("test")
    assert f(["a", "b"]).to_dict() == dict(terms={"test": ["a", "b"]})


def test_range_filter():
    """Test range filter."""
    f = range_filter("test", start_date_math="startmath", end_date_math="endmath")
    assert f(["1821--1940"]) == dsl.query.Range(
        test={
            "gte": "1821||startmath",
            "lte": "1940||endmath",
        }
    )
    assert f([">1821--"]) == dsl.query.Range(test={"gt": "1821||startmath"})
    assert f(["1821--<1940"]) == dsl.query.Range(
        test={"gte": "1821||startmath", "lt": "1940||endmath"}
    )

    assert pytest.raises(RESTValidationError, f, ["2016"])
    assert pytest.raises(RESTValidationError, f, ["--"])


def test_create_filter_dsl():
    """Test request value extraction."""
    app = Flask("testapp")
    kwargs = MultiDict([("a", "1")])
    defs = dict(
        type=terms_filter("type.type"),
        subtype=terms_filter("type.subtype"),
    )

    with app.test_request_context("?type=a&type=b&subtype=c&type=zażółcić"):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert len(filters) == 2
        assert args == MultiDict(
            [
                ("a", "1"),
                ("type", "a"),
                ("type", "b"),
                ("subtype", "c"),
                ("type", "zażółcić"),
            ]
        )

    kwargs = MultiDict([("a", "1")])
    with app.test_request_context("?atype=a&atype=b"):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert not filters
        assert args == kwargs


def test_post_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter("type"),
        subtype=terms_filter("subtype"),
    )

    with app.test_request_context("?type=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, args = _post_filter(search, urlargs, defs)
        assert "post_filter" in search.to_dict()
        assert search.to_dict()["post_filter"] == dict(terms=dict(type=["test"]))
        assert args["type"] == "test"

    with app.test_request_context("?anotertype=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, args = _post_filter(search, urlargs, defs)
        assert "post_filter" not in search.to_dict()


def test_query_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter("type"),
        subtype=terms_filter("subtype"),
    )

    with app.test_request_context("?type=test"):
        search = dsl.Search().query(dsl.Q("multi_match", query="value"))
        body = search.to_dict()
        search, args = _query_filter(search, urlargs, defs)
        assert "post_filter" not in search.to_dict()
        assert search.to_dict()["query"]["bool"]["must"][0] == body["query"]
        assert search.to_dict()["query"]["bool"]["filter"] == [
            dict(terms=dict(type=["test"]))
        ]
        assert args["type"] == "test"

    with app.test_request_context("?anotertype=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        body = search.to_dict()
        query, args = _query_filter(search, urlargs, defs)
        assert query.to_dict() == body


def test_aggregations(app):
    """Test aggregations."""
    with app.test_request_context(""):
        search = dsl.Search().query(dsl.Q(query="value"))
        defs = dict(
            type=dict(
                terms=dict(field="upload_type"),
            ),
            subtype=dict(
                terms=dict(field="subtype"),
            ),
        )
        assert _aggregations(search, defs).to_dict()["aggs"] == defs


def test_default_facets_factory(app, db, search_user, redis_connect):
    """Test aggregations."""
    test_redis_key = "test_facet_search_query_has_permission"
    redis_connect.delete(test_redis_key)
    defs = dict(
        aggs=dict(
            type=dict(
                filter=dict(
                    bool=dict(
                        must=[dict(term=dict(publish_status="0"))]
                    )
                ),
                aggs=dict(
                    type=dict(
                        terms=dict(
                            field="upload_type",size=1000
                        )
                    )
                )
            ),
            subtype=dict(
                filter=dict(bool=dict(must=[dict(term=dict(publish_status="0"))])),
                aggs=dict(subtype=dict(terms=dict(field="subtype",size=1000)))
            ),
        ),
        post_filters=dict(
            bool=dict(
                must=[dict(terms=dict(upload_type=["a"])),dict(terms=dict(subtype=["b"]))]
            )
        ),
    )
    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()
    app.config['SEARCH_UI_SEARCH_INDEX'] = 'testidx'
    app.config["RECORDS_REST_FACETS"]["testidx"] = defs
    from unittest.mock import patch
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context("?type=a&subtype=b"):
                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, "testidx")
                assert search.to_dict()["aggs"] == defs["aggs"]
                assert "post_filter" in search.to_dict()
                assert search.to_dict()['post_filter'] == defs['post_filters']
                #assert search.to_dict()["query"]["bool"]["filter"][0]["terms"]["subtype"]

                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, "anotheridx")
                assert "aggs" not in search.to_dict()
                assert "post_filter" not in search.to_dict()
                assert "bool" not in search.to_dict()["query"]
    redis_connect.delete(test_redis_key)


def test_selecting_one_specified_facet(app, db, search_user, redis_connect):
    test_redis_key = "test_facet_search_query_has_permission"

    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()

    expected_agg = {"filtered": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"type": {"terms": {"field": "upload_type", "size": 1000}}}}}
    index = "{}-weko".format("test")
    app.config['SEARCH_UI_SEARCH_INDEX'] = index
    app.config['RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE'] = True
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context("?type=a&subtype=b&facets=type"):
                g.identity = Identity('test_user')
                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, index)
                assert search.to_dict().get("aggs").get('type').get('aggs') == expected_agg


def test_selecting_specified_facet(app, db, aggs_and_facet):
    test_redis_key = "test_facet_search_query_has_permission"
    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()

    expected_agg = {"filtered": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"type": {"terms": {"field": "upload_type", "size": 1000}}}}}
    index = "{}-weko".format("test")
    app.config['SEARCH_UI_SEARCH_INDEX'] = index
    app.config['RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE'] = True
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context("?type=a&subtype=b&facets=type,subtype"):
                g.identity = Identity('test_user')
                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, index)
                assert search.to_dict().get("aggs").get('type').get('aggs') == expected_agg


def test_turn_off_facets(app, db, aggs_and_facet):
    test_redis_key = "test_facet_search_query_has_permission"
    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()

    index = "{}-weko".format("test")
    app.config['SEARCH_UI_SEARCH_INDEX'] = index
    app.config['RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE'] = True
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context("?type=a&subtype=b&facets=null"):
                g.identity = Identity('test_user')
                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, "test_facet_names")
                assert search.to_dict().get("aggs") is None


def test_selecting_all_facets_by_default(app, db, aggs_and_facet):
    test_redis_key = "test_facet_search_query_has_permission"
    type_setting = FacetSearchSetting(
        name_en="type",
        name_jp="type",
        mapping="upload_type",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    subtype_setting = FacetSearchSetting(
        name_en="subtype",
        name_jp="subtype",
        mapping="subtype",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=2,
        is_open=True
    )
    db.session.add(type_setting)
    db.session.add(subtype_setting)
    db.session.commit()

    index = "{}-weko".format("test")
    app.config['SEARCH_UI_SEARCH_INDEX'] = index
    app.config['RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE'] = True
    with patch("weko_search_ui.permissions.search_permission.can",return_value=True):
        with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
            with app.test_request_context("?type=a&subtype=b"):
                g.identity = Identity('test_user')
                search = dsl.Search().query(dsl.Q(query="value"))
                search, urlkwargs = default_facets_factory(search, "test_facet_names")
                assert search.to_dict().get("aggs") is None
