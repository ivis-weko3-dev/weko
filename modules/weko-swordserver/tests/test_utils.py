# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
import os
from io import BytesIO
import shutil
import tempfile
import zipfile
import time
from hashlib import sha256,sha512
from zipfile import ZipFile, BadZipFile
from weko_swordserver.api import SwordClient, SwordItemTypeMapping
from unittest.mock import MagicMock, patch
from weko_swordserver.utils import (
    check_import_file_format,
    # get_record_by_client_id,
    # process_json,
    unpack_zip,
    is_valid_file_hash,
    update_item_ids
)
from .helpers import json_data
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.models import SwordClientModel, SwordItemTypeMappingModel
from weko_search_ui.mapper import JsonLdMapper

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_import_file_format(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_import_file_format -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_import_file_format(app):
    # No 1
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SWORDBagIt') == 'JSON'


    # No 2
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/invalid.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SWORDBagIt')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "SWORDBagIt requires metadate/sword.json."

    # No 3
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('ro-crate-metadata.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'JSON'

    # No 4
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('invalid.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'OTHERS'

    # No 5
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    packaging = 'InvalidPackaging'
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, packaging)
    assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
    assert e.value.message == f"Not accept packaging format: {packaging}"


# def unpack_zip(file):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_unpack_zip -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_unpack_zip(app,mocker):
    # No 1
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('test.txt', 'This is a test file.')
        zip_file.writestr('test1.txt', 'This is a test1 file.')
    file_content.seek(0)

    data_path, file_list = unpack_zip(file_content)

    assert os.path.exists(data_path)
    assert 'test.txt' in file_list
    assert 'test1.txt' in file_list
    assert os.path.isfile(os.path.join(data_path, 'test.txt'))
    assert os.path.isfile(os.path.join(data_path, 'test1.txt'))

    # Clean up
    if os.path.exists(data_path):
        shutil.rmtree(data_path)

    # No 2  NG
    file_content = BytesIO(b"This is not a zip file")
    with pytest.raises(Exception) as e:
        data_path, file_list = unpack_zip(file_content)
    assert e.type == BadZipFile
    assert str(e.value) == "File is not a zip file"

    # Clean up
    if os.path.exists(data_path):
        shutil.rmtree(data_path)

    # No 19
    time.sleep(1)
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('dir\\test.txt', 'This is a test file.')
    file_content.seek(0)
    original_os_sep = os.sep
    os.sep = "\\"
    data_path, file_list = unpack_zip(file_content)

    assert os.path.exists(data_path)
    assert 'dir/test.txt' in file_list
    assert os.path.isfile(os.path.join(data_path, 'dir/test.txt'))
    os.sep = original_os_sep

    if os.path.exists(data_path):
        shutil.rmtree(data_path)

    # Exception
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('test.txt', 'This is a test file.')
    file_content.seek(0)
    zip_ref = ZipFile(file_content)
    infolist = zip_ref.infolist()
    infolist[0].orig_filename = "invalid\x80.txt"
    with patch("zipfile.ZipFile.infolist", return_value=infolist):
        with pytest.raises(UnicodeEncodeError):
            unpack_zip(file_content)

# def is_valid_file_hash(expected_hash, file):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_is_valid_file_hash -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_is_valid_file_hash():
    # No 1
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content)
    assert result is True

    # No 2
    file_content.seek(0)
    invalid_hash = sha256(b'Invalid content').hexdigest()
    result = is_valid_file_hash(invalid_hash ,file_content)
    assert result is False

    # No 3:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha512(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False

    # No 4:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content')
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False

# def update_item_ids(list_record, new_id):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_update_item_ids -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_update_item_ids(app, mocker):
    """
    update_item_ids 関数の動作をテストする。
    すべての条件分岐やエッジケースをカバーする。
    """
    # テストケース 1: list_record がリストでない場合
    with pytest.raises(ValueError, match="list_record must be a list."):
        update_item_ids(None, "new_id")

    # テストケース 2: list_record が空のリストの場合
    assert update_item_ids([], "new_id") == []

    # テストケース 3: list_record に dict 以外の要素が含まれている場合
    list_record_3 = [1, 2, 3]
    assert update_item_ids(list_record_3, "new_id") == list_record_3

    # テストケース 4: list_record の要素に metadata がない場合
    list_record_4 = [{"key": "value"}]
    assert update_item_ids(list_record_4, "new_id") == list_record_4

    # テストケース 5: metadata に id がない場合
    list_record_5 = [{"metadata": {}}]
    assert update_item_ids(list_record_5, "new_id") == list_record_5

    # テストケース 6: metadata に link_data がない場合
    list_record_6 = [{"metadata": {"id": "123"}}]
    assert update_item_ids(list_record_6, "new_id") == list_record_6

    # テストケース 7: link_data がリストでない場合
    list_record_7 = [{"metadata": {"id": "123", "link_data": "not_a_list"}}]
    assert update_item_ids(list_record_7, "new_id") == list_record_7

    # テストケース 8: link_data の要素が dict でない場合
    list_record_8 = [{"metadata": {"id": "123", "link_data": [1, 2, 3]}}]
    assert update_item_ids(list_record_8, "new_id") == list_record_8

    # テストケース 9: link_data の要素に item_id と sele_id がない場合
    list_record_9 = [{"metadata": {"id": "123", "link_data": [{"key": "value"}]}}]
    assert update_item_ids(list_record_9, "new_id") == list_record_9

    # テストケース 10: link_data の要素に item_id があるが、sele_id が "isSupplementedBy" でない場合
    mock_metadata = MagicMock()
    mock_metadata.id = "123"
    mock_metadata.link_data = [{"item_id": "456", "sele_id": "isSupplementTo"}]
    # JsonLdMapper()._InformedMetadata() をモック化
    with patch.object(JsonLdMapper, '_InformedMetadata', return_value=mock_metadata):
        # テストデータ
        list_record = [{"metadata": mock_metadata}]
        new_id = "new_id"

        # テスト対象関数を呼び出し
        result = update_item_ids(list_record, new_id)

        # 結果を検証
        assert result[0]["metadata"].link_data[0]["item_id"] == "456"
        assert mock_metadata.id == "123"
        assert mock_metadata.link_data == [{"item_id": "456", "sele_id": "isSupplementTo"}]

    # テストケース 11: link_data の要素に item_id があり、sele_id が "isSupplementedBy" の場合
    # モックを作成
    mock_metadata = MagicMock()
    mock_metadata.id = "123"
    mock_metadata.link_data = [{"item_id": "123", "sele_id": "isSupplementedBy"}]

    # JsonLdMapper()._InformedMetadata() をモック化
    with patch.object(JsonLdMapper, '_InformedMetadata', return_value=mock_metadata):
        # テストデータ
        list_record = [{"metadata": mock_metadata}]
        new_id = "new_id"

        # テスト対象関数を呼び出し
        result = update_item_ids(list_record, new_id)

        # 結果を検証
        assert result[0]["metadata"].link_data[0]["item_id"] == new_id
        assert mock_metadata.id == "123"
        assert mock_metadata.link_data == [{"item_id": "new_id", "sele_id": "isSupplementedBy"}]

    # テストケース 12: 複数の ITEM が含まれる場合
    # モックを作成
    mock_metadata = MagicMock()
    mock_metadata.id = "123"
    mock_metadata.link_data = [{"item_id": "123", "sele_id": "isSupplementTo"}]

    mock_metadata1 = MagicMock()
    mock_metadata1.id = "789"
    mock_metadata1.link_data = [{"item_id": "789", "sele_id": "isSupplementedBy"}]

    # JsonLdMapper()._InformedMetadata() をモック化
    with patch.object(JsonLdMapper, '_InformedMetadata', return_value=mock_metadata):
        # テストデータ
        list_record = [{"metadata": mock_metadata}, {"metadata": mock_metadata1}]
        new_id = "new_id"

        # テスト対象関数を呼び出し
        result = update_item_ids(list_record, new_id)
        # for item in result:
        #     print(getattr(item.get('metadata'), 'link_data', []))


        # 結果を検証
        assert result[0]["metadata"].link_data[0]["item_id"] == "123"

        assert result[1]["metadata"].link_data[0]["item_id"] == new_id

# def get_record_by_client_id(client_id):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_get_record_by_client_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
# def test_get_record_by_client_id(app,mocker):
#     # No 1
#     client_id = "valid_client_id"
#     expected_client = SwordClientModel(client_id="client_id", mapping_id="mapping_id")
#     expected_mapping = SwordItemTypeMappingModel(id="mapping_id")

#     with patch.object(SwordClient, 'get_client_by_id', return_value=expected_client):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=expected_mapping):
#             client, mapping = get_record_by_client_id(client_id)
#             assert client == expected_client
#             assert mapping == expected_mapping

#     # No 2
#     invalid_client_id = "invalid_client_id"

#     with patch.object(SwordClient, 'get_client_by_id', return_value=None):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=expected_mapping):
#             client, mapping = get_record_by_client_id(invalid_client_id)
#             assert client == None
#             assert mapping == expected_mapping

#     # No 3
#     valid_client_id = "valid_client_id"
#     expected_client = SwordClientModel(client_id="client_id", mapping_id="invalid_mapping_id")
#     with patch.object(SwordClient, 'get_client_by_id', return_value=expected_client):
#         with patch.object(SwordItemTypeMapping, 'get_mapping_by_id', return_value=None):
#             client, mapping = get_record_by_client_id(valid_client_id)
#             assert client == expected_client
#             assert mapping == None

# def process_json(json_ld):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_process_json -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
# def test_process_json(app):
#     # No 1: Valid JSON-LD
#     json_ld = json_data("data/item_type/ro-crate-metadata_2.json")
#     expected_json = json_data("data/item_type/processed_json_2.json")
#     result = process_json(json_ld)
#     assert result == expected_json

#     # No 2: Invalid JSON-LD format @id is missing
#     invalid_json_ld = {"@graph": [{"@type": "Dataset"}, {"@id": "#summary"}]}
#     with pytest.raises(WekoSwordserverException) as e:
#         process_json(invalid_json_ld)
#     assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
#     assert e.value.message == "Invalid json-ld format."

#     # No 3: Invalid JSON-LD format "@graph" not in json
#     invalid_json_ld = {"@graph1": [{"@id": "invalid"}]}
#     with pytest.raises(WekoSwordserverException) as e:
#         process_json(invalid_json_ld)
#     assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
#     assert e.value.message == "Invalid json-ld format."
