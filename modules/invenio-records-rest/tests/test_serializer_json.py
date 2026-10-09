# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_json.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tm

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

import json
from types import SimpleNamespace

import mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.schemas.fields import \
    PersistentIdentifier as PIDField
from invenio_records_rest.serializers.json import JSONSerializer


def test_serialize(app, db):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='2'),
        Record({'mytitle': 'test'})
    ))
    assert data['title'] == 'test'
    assert data['id'] == '2'


def test_serialize2(app, db, item_type):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')
        metadata = fields.Raw()

    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='3'),
        Record(
        {
            'item_type_id': "15",
            'mytitle': 'test',
            "_deposit": {
                "owners": [1],
                "owners_ext": {
                    "username": "test username",
                    "displayname": "test displayname",
                    "email": "test@test.com"
                }
            },
            "publish_date": "2021-08-06",
            "publish_status": "0"
        })
    ))
    assert data == {
        "id": "3",
        "metadata": {
            'item_type_id': "15",
            "_deposit": {
                "owners": [1]
            },
            'mytitle': 'test',
            "publish_date": "2021-08-06",
            "publish_status": "0"
        },
        "title": "test"
    }


def test_serialize_search(app, db):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': dict(mytitle='test1', pid='1'), '_id': 'a',
                     '_version': 1},
                    {'_source': dict(mytitle='test2', pid='2'), '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    ))

    assert data['aggregations'] == {}
    assert 'links' in data
    assert data['hits'] == dict(
        hits=[
            dict(title='test1', id='1'),
            dict(title='test2', id='2'),
        ],
        total=2,
    )


def test_serialize_search2(app, db, item_type, request_context):
    """Test JSON serialize."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')
        metadata = fields.Raw()

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {
                        '_source': {
                            '_item_metadata': {
                                "_deposit": {
                                    "owners": [1],
                                    "owners_ext": {
                                        "username": "test username",
                                        "displayname": "test displayname",
                                        "email": "test@test.com"
                                    }
                                },
                                "publish_date": "2021-08-06",
                                "item_type_id": "15"
                            },
                            'feedback_mail_list': [
                                'test@test.com'
                            ],
                            'pid': "1"
                        },
                        '_id': 'a',
                        '_version': 1
                    },
                ],
                total=2,
            ),
            aggregations={},
        )
    ))

    assert data['aggregations'] == {}
    assert 'links' in data
    assert data['hits'] == {
        'hits': [
            {
                'id': '1',
                'metadata': {
                    '_item_metadata': {
                        "_deposit": {
                            'owners': [1]
                        },
                        'publish_date': '2021-08-06',
                        "item_type_id": "15"
                    },
                    'feedback_mail_list': [], 'pid': '1'
                }
            }
        ],
        'total': 2
    }


def test_serialize_pretty(app, db):
    """Test pretty JSON."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.title')

    pid = PersistentIdentifier(pid_type='recid', pid_value='2'),
    rec = Record({'title': 'test'})

    with app.test_request_context():
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{"title":"test"}'

    with app.test_request_context('/?prettyprint=1'):
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{\n  "title": "test"\n}'


def _make_item_metadata():
    """Return the ``_item_metadata`` used by the search serializer tests."""
    return {
        "_deposit": {
            "owners": [1],
            "owners_ext": {
                "username": "test username",
                "displayname": "test displayname",
                "email": "test@test.com"
            }
        },
        "publish_date": "2021-08-06",
        "item_type_id": "15"
    }


# serialize が weko_shared_role_ids のみを除外する
def test_serialize_exclude_shared_role_ids(app, db, item_type):
    """Test that weko_shared_role_ids is removed from a single record response."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')
        metadata = fields.Raw()

    # 1. weko_shared_ids と weko_shared_role_ids を持つレコード
    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='4'),
        Record({
            'item_type_id': "15",
            'mytitle': 'test',
            'weko_shared_ids': [3],
            'weko_shared_role_ids': ["12"],
            "publish_date": "2021-08-06",
            "publish_status": "0"
        })
    ))
    assert 'weko_shared_role_ids' not in data['metadata']
    assert data['metadata']['weko_shared_ids'] == [3]
    assert data['metadata']['mytitle'] == 'test'

    # 2. weko_shared_role_ids を持たないレコード（例外にならず出力は改修前と同じ）
    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='5'),
        Record({
            'item_type_id': "15",
            'mytitle': 'test',
            'weko_shared_ids': [3],
            "publish_date": "2021-08-06",
            "publish_status": "0"
        })
    ))
    assert data == {
        "id": "5",
        "metadata": {
            'item_type_id': "15",
            'mytitle': 'test',
            'weko_shared_ids': [3],
            "publish_date": "2021-08-06",
            "publish_status": "0"
        },
        "title": "test"
    }


# serialize_search が各ヒットの weko_shared_role_ids のみを除外する
def test_serialize_search_exclude_shared_role_ids(app, db, item_type, request_context):
    """Test that weko_shared_role_ids is removed from every search hit."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')
        metadata = fields.Raw()

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {
                        '_source': {
                            '_item_metadata': _make_item_metadata(),
                            'feedback_mail_list': ['test@test.com'],
                            'weko_shared_ids': [3],
                            'weko_shared_role_ids': ["12"],
                            'pid': "1"
                        },
                        '_id': 'a',
                        '_version': 1
                    },
                    {
                        '_source': {
                            '_item_metadata': _make_item_metadata(),
                            'feedback_mail_list': ['test@test.com'],
                            'weko_shared_ids': [3],
                            'pid': "2"
                        },
                        '_id': 'b',
                        '_version': 1
                    },
                ],
                total=2,
            ),
            aggregations={},
        )
    ))

    hits = data['hits']['hits']
    assert len(hits) == 2
    for hit in hits:
        source = hit['metadata']
        assert 'weko_shared_role_ids' not in source
        assert source['weko_shared_ids'] == [3]
        # 既存の feedback_mail_list の処理は改修前と同じ
        assert source['feedback_mail_list'] == []


# 非公開メタデータ判定用 item_roles に weko_shared_role_ids が加わる
def test_serialize_search_item_roles(app, db, item_type, request_context):
    """Test that item_roles passed to hide_meta_data_for_role has weko_shared_role_ids."""
    app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS'] = ['creatorMails', 'contributorMails', 'mails']
    app.config['WEKO_ITEMS_UI_PROXY_POSTING'] = True

    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')
        metadata = fields.Raw()

    def fetcher(obj_uuid, data):
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    # U_O: 登録者 / U_P1: 代理投稿者(個人) / U_G: 代理投稿グループ R_A 所属 / U_N: いずれでもない
    # ※ is_item_editable_by は対象ユーザーを DB から引き直すため、実ユーザー・実ロールを作成する
    ds = app.extensions["invenio-accounts"].datastore
    role_a = ds.create_role(name='jc_idp_example_org_gr_Alpha')
    users = {}
    for name in ('U_O', 'U_P1', 'U_G', 'U_N'):
        users[name] = ds.create_user(
            email='{}@test.org'.format(name.lower()), password='123456',
            active=True)
    ds.add_role_to_user(users['U_G'], role_a)
    ds.commit()
    rid_a = str(role_a.id)
    uid_o = users['U_O'].id
    uid_p1 = users['U_P1'].id

    def make_result():
        return dict(
            hits=dict(
                hits=[
                    {   # S1
                        '_source': {
                            '_item_metadata': _make_item_metadata(),
                            'weko_creator_id': str(uid_o),
                            'weko_shared_ids': [uid_p1],
                            'weko_shared_role_ids': [rid_a],
                            'pid': "1"
                        },
                        '_id': 'a', '_version': 1
                    },
                    {   # S2: weko_shared_ids / weko_shared_role_ids を持たない
                        '_source': {
                            '_item_metadata': _make_item_metadata(),
                            'weko_creator_id': str(uid_o),
                            'pid': "2"
                        },
                        '_id': 'b', '_version': 1
                    },
                ],
                total=2,
            ),
            aggregations={},
        )

    import weko_items_ui.utils as items_utils
    real_hide = items_utils.hide_meta_data_for_role

    expected_hidden = {'U_O': False, 'U_P1': False, 'U_G': False, 'U_N': True}
    for name, user in users.items():
        calls = []

        def spy(record):
            result = real_hide(record)
            calls.append((dict(record), result))
            return result

        with mock.patch('weko_items_ui.utils.current_user', user), \
                mock.patch('weko_items_ui.utils.hide_meta_data_for_role',
                           side_effect=spy):
            data = json.loads(JSONSerializer(TestSchema).serialize_search(
                fetcher, make_result()))

        # 2. hide_meta_data_for_role に渡された item_roles（S1・S2）
        assert len(calls) == 2
        assert calls[0][0] == {
            'weko_creator_id': str(uid_o),
            'weko_shared_ids': [uid_p1],
            'weko_shared_role_ids': [rid_a],
        }
        assert calls[1][0] == {
            'weko_creator_id': str(uid_o),
            'weko_shared_ids': [],
            'weko_shared_role_ids': [],
        }

        # 1. S1 の判定結果。グループのメンバーにも個人の代理投稿者と同様に
        #    非公開メタデータが返る（隠されない）。U_N は隠される
        assert calls[0][1] is expected_hidden[name], name

        # 3. 除外は判定の後。応答に weko_shared_role_ids は含まれず
        #    weko_shared_ids は残る
        s1_meta = data['hits']['hits'][0]['metadata']
        assert 'weko_shared_role_ids' not in s1_meta
        assert s1_meta['weko_shared_ids'] == [uid_p1]
