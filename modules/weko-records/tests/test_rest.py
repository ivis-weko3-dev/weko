from invenio_oauth2server.models import Token
from mock import patch
from flask import Blueprint
from pytest import fail
import pytest

from sqlalchemy.exc import SQLAlchemyError
from weko_records.rest import (
    create_error_handlers,
    create_blueprint,
)

# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_create_error_handlers -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records/.tox/c1/tmp
# def create_error_handlers(blueprint):
def test_create_error_handlers(app):
    blueprint = Blueprint(
        'weko_records_rest',
        __name__,
        url_prefix='',
    )
    assert create_error_handlers(blueprint) == None

# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records/.tox/c1/tmp
# def create_blueprint(endpoints):
def test_create_blueprint(app):
    endpoints = {
        'oa_status_callback': {
            'route': '/<string:version>/oa_status/callback',
            'default_media_type': 'application/json',
        },
        'dummy_endpoint': {
            'route': '/dummy',
            'default_media_type': 'application/json',
        }
    }
    assert create_blueprint(endpoints) != None

# OaStatusCallback
# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_OaStatusCallback_post_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
@pytest.mark.parametrize('version, use_token, json, status', [
    ("v1",False,{
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    },401),
    ("v0",True,{
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    },400),
    ("v1",True,{},400),
    ("v1",True,{"articles":[{"wos_record_status": "aaa"}]},200),
    ("v1",True,{
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    },200),
    ("v1",True,{
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            },
            {
                "id": 2,
                "wos_record_status": "bbb",
            }
        ]
    },200)
])
def test_OaStatusCallback_post_v1(app, tokens, users, version, use_token, json, status):
    """Test OaStatusCallback.post_v1 method."""

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_REST_ENDPOINTS']))

    if use_token:
        token = tokens[0]["token"].access_token
        headers = {
            "Authorization":"Bearer {}".format(token),
        }
    else:
        headers = {"Authorization": "Bearer xxxxxxxxx"}

    with app.test_client() as client:

        # TestCase: invalid token
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = headers,
                json = json,
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == status


def test_OaStatusCallback_post_v1_SQLAlchemyError(app, tokens, users):
    """Test OaStatusCallback.post_v1 method."""

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_REST_ENDPOINTS']))
    version="v1"
    correct_request_body={
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    }
    token = tokens[0]["token"].access_token
    headers = {
            "Authorization":"Bearer {}".format(token),
        }

    with app.test_client() as client:
         # TestCase: SQLAlchemyError
        with patch('weko_records.rest.OaStatus.get_oa_status', side_effect=SQLAlchemyError):
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code == 500

def test_OaStatusCallback_post_v1_Exception(app, tokens, users):
    """Test OaStatusCallback.post_v1 method."""

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_REST_ENDPOINTS']))
    version="v1"
    correct_request_body={
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    }
    token = tokens[0]["token"].access_token
    headers = {
        "Authorization":"Bearer {}".format(token),
    }

    with app.test_client() as client:
        with patch('weko_records.rest.OaStatus.get_oa_status', side_effect=Exception):
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code == 500

def test_OaStatusCallback_post_v1_Exception2(app, tokens, users):
    """Test OaStatusCallback.post_v1 method."""

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_REST_ENDPOINTS']))
    version="v1"
    correct_request_body={
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    }
    token = tokens[0]["token"].access_token
    headers = {
        "Authorization":"Bearer {}".format(token),
    }

    with app.test_client() as client:
        with patch('weko_records.rest.db.session.commit',side_effect=Exception("Test exception")):
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code != 200
