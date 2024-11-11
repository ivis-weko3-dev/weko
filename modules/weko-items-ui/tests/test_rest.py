# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""
import os
from weko_admin.models import RankingSettings
from unittest.mock import patch, MagicMock
import pytest

from flask import json
from sqlalchemy.exc import SQLAlchemyError
from invenio_search.engine import search
from werkzeug.exceptions import InternalServerError

ranking_type = [
    'new_items',
    'most_reviewed_items',
    'most_downloaded_items',
    'most_searched_keywords',
    'created_most_items_user'
]

opensearch_username = os.getenv('OPENSEARCH_USERNAME', 'admin')
opensearch_password = os.getenv('OPENSEARCH_PASSWORD', 'admin')

# OpenSearchクライアントの設定
client = search.client.OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=(opensearch_username, opensearch_password),  # 認証情報を追加
    use_ssl=True,
    verify_certs=False,  # テストのためにSSL検証を無効にする
    ssl_show_warn=False
)

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoRanking -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize('ranking_type', ranking_type)
def test_WekoRanking(app, client, db, db_ranking, ranking_type):
    """Test Ranking."""
    app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS'] = {
        'is_show': True,
        'new_item_period': 14,
        'statistical_period': 365,
        'display_rank': 10,
        'rankings': {'new_items': True, 'most_reviewed_items': True, 'most_downloaded_items': True, 'most_searched_keywords': True, 'created_most_items_user': True}
    }
    ranking_result = {
        ranking_type: []
    }
    with patch('weko_items_ui.rest.get_ranking', return_value=ranking_result):
        res = client.get(f'/v1/ranking/{ranking_type}')
        assert res.status_code == 200
        data = json.loads(res.get_data())
        assert data['ranking_type'] == ranking_type


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoRanking_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_WekoRanking_error(app, client, db, db_ranking):
    """Test Ranking."""
    url = '/v1/ranking/most_reviewed_items'
    app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS'] = {
        'is_show': True,
        'new_item_period': 14,
        'statistical_period': 365,
        'display_rank': 10,
        'rankings': {'new_items': True, 'most_reviewed_items': True, 'most_downloaded_items': False, 'most_searched_keywords': False, 'created_most_items_user': False}
    }

    ranking_result = {
        'new_items': []
    }
    with patch('weko_items_ui.rest.get_ranking', return_value=ranking_result):
        res = client.get(url)
        headers = {}
        headers['If-None-Match'] = res.headers['Etag']
        res = client.get(url, headers=headers)
        assert res.status_code == 304

        res = client.get('/v0/ranking/most_reviewed_items')
        assert res.status_code == 400

        res = client.get('/v1/ranking/most_reviewed_items?display_rank=typeerror')
        assert res.status_code == 400

        res = client.get('/v1/ranking/no_ranking')
        assert res.status_code == 404

        with patch('weko_admin.models.RankingSettings.get', MagicMock(side_effect=SQLAlchemyError("SQLAlchemy connection failed"))):
            res = client.get(url)
            assert res.status_code == 500
            # assert b"SQLAlchemy connection failed" in res.get_data()

        with patch('weko_admin.models.RankingSettings.get', MagicMock(side_effect=search.OpenSearchException())):
            res = client.get(url)
            assert res.status_code == 500

        res = client.get('/v1/ranking/most_downloaded_items')
        assert res.status_code == 403


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoFileRanking -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_WekoFileRanking(app, client, records, db_itemtype):
    """Test File Ranking."""
    ranking_result = {
        'new_items': []
    }
    with patch('weko_items_ui.utils.get_file_download_data', return_value=ranking_result):
        # 1 GET request
        url = '/v1/ranking/11/files'
        res = client.get(url + "?date=2024-01&display_number=10")
        assert res.status_code == 200

    ranking_result = {'new_items':[{'item01':"01"}]}
    with patch('weko_items_ui.utils.get_file_download_data', return_value=ranking_result):
        # 2 Set pretty true
        url = '/v1/ranking/11/files' + '?pretty=true'
        res = client.get(url)
        assert res.status_code == 200
        assert res.get_data(True) == '{\n    "new_items": [\n        {\n            "item01": "01"\n        }\n    ]\n}'

    with patch('weko_items_ui.utils.get_file_download_data', return_value=ranking_result) as test_mock:
        # 3 Contain thumbnail
        url = '/v1/ranking/17/files'
        res = client.get(url)
        assert res.status_code == 200
        assert test_mock.call_args[0][2] == ["helloworld.pdf"]


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoFileRanking_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_WekoFileRanking_error(app, client, records, db_itemtype):
    """Test File Ranking."""
    ranking_result = {
        'new_items': []
    }
    
    # 基本URLを定義
    url = '/v1/ranking/11/files'
    
    # アクセス権限を制御するパッチを適用
    with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=True)), \
         patch('weko_records_ui.permissions.page_permission_factory', MagicMock(return_value=True)):
        
        # 4: Access denied
        with patch('weko_records_ui.permissions.check_publish_status', MagicMock(return_value=False)):
            res = client.get(url)
            assert res.status_code == 403
        
        # 4: Access denied
        with patch('weko_records_ui.permissions.page_permission_factory', MagicMock(return_value=False)):
            res = client.get(url)
            assert res.status_code == 403
        
        # 5: File not exist
        with patch('weko_items_ui.utils.get_file_download_data', return_value=ranking_result):
            url_non_existent_file = '/v1/ranking/16/files'
            res = client.get(url_non_existent_file)
            assert res.status_code == 404

            # 6: Invalid record
            url_invalid_record = '/v1/ranking/100/files'
            res = client.get(url_invalid_record)
            assert res.status_code == 404

            # 7: Invalid version
            url_invalid_version = '/v0/ranking/11/files'
            res = client.get(url_invalid_version)
            assert res.status_code == 400

            # 8: Invalid date
            res = client.get(url + "?date=a")
            assert res.status_code == 400

            # 9: Invalid display_number
            res = client.get(url + "?display_number=a")
            assert res.status_code == 400

            # 10: display_number > 2147483647
            res = client.get(url + "?display_number=2147483648")
            assert res.status_code == 400

            # 11: Check Etag
            res = client.get(url)
            etag = res.headers['Etag']
            headers = {'If-None-Match': etag}
            res = client.get(url, headers=headers)
            assert res.status_code == 304

            # 12: Handle OpenSearchException
            with patch('weko_admin.models.RankingSettings.get', MagicMock(side_effect=search.OpenSearchException)):
                try:
                    res = client.get(url)
                except InternalServerError as e:
                    assert "OpenSearchException" in str(e)
                    assert res.status_code == 500