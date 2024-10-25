import os
import json
import copy
import pytest
import unittest
import datetime
from invenio_search import current_search
from unittest.mock import patch, MagicMock, Mock
from flask import current_app, make_response, request
from flask_login import current_user
from flask_babel import Babel

from invenio_resourcesyncserver.query import (
    get_items_by_index_tree,
    get_item_changes_by_index,
    item_path_search_factory,
    item_changes_search_factory
)


# def get_items_by_index_tree(index_tree_id):
def test_get_items_by_index_tree(i18n_app, indices):
    index_tree_id = 33

    assert get_items_by_index_tree(index_tree_id) == []


# def get_item_changes_by_index(index_tree_id, date_from, date_until):
def test_get_item_changes_by_index(i18n_app, indices, es):
    index_tree_id = 'test_index_tree_id'
    date_from = '2023-01-01'
    date_until = '2023-12-31'

    mock_records_search = MagicMock()
    mock_records_search.with_preference_param.return_value = mock_records_search
    mock_records_search.params.return_value = mock_records_search
    mock_records_search._index = ['']

    with patch('invenio_resourcesyncserver.query.current_app.config', {'SEARCH_UI_SEARCH_INDEX': 'test-weko'}):
        # Mock item_changes_search_factory
        mock_search_instance = MagicMock()
        mock_search_instance.execute.return_value.to_dict.return_value = {
            'hits': {'hits': [{'id': 'test_id'}]}
        }
        with patch('invenio_resourcesyncserver.query.RecordsSearch', return_value=mock_records_search):
            with patch('invenio_resourcesyncserver.query.item_changes_search_factory', return_value=mock_search_instance):
                result = get_item_changes_by_index(index_tree_id, date_from, date_until)

                assert result == [{'id': 'test_id'}]
                mock_records_search.with_preference_param.assert_called_once()
                mock_records_search.params.assert_called_once_with(version=False)
                assert mock_records_search._index[0] == 'test-weko'
                mock_search_instance.execute.assert_called_once()


# def item_path_search_factory(search, index_id="0"):
def test_item_path_search_factory(i18n_app, indices):
    search = MagicMock()
    data_1 = MagicMock()

    assert item_path_search_factory(search, index_id=33)

    with patch("weko_index_tree.api.Indexes.get_list_path_publish", return_value="test"):
        with patch("weko_index_tree.api.Indexes.get_child_list", return_value=[MagicMock()]):
            assert item_path_search_factory(data_1, index_id="Root Index")

    assert item_path_search_factory(data_1, index_id=33)


# def item_changes_search_factory(search, index_id=0, date_from="now/d", date_until="now/d"):
def test_item_changes_search_factory(i18n_app, indices):
    search = MagicMock()

    assert item_changes_search_factory(search, index_id=33)

    with patch("weko_index_tree.api.Indexes.get_list_path_publish", return_value="test"):
        with patch("weko_index_tree.api.Indexes.get_child_list", return_value=[MagicMock()]):
            assert item_changes_search_factory(search, index_id="Root Index")
