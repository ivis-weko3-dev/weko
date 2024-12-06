# -*- coding: utf-8 -*-
#
#
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::xxxx -vv --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp


import pytest
import unittest
from invenio_pidstore.errors import PIDDoesNotExistError
import json
import os
from flask import session, url_for,current_app

from weko_records.api import ItemTypes
from weko_search_ui.utils import (
    check_permission,
    get_content_workflow,
    getEncode,
    validation_file_open_date,
    check_import_items,
    unpackage_import_file,
    handle_check_exist_record,
    handle_check_date,
    handle_check_doi,
    get_list_key_of_iso_date,
    handle_validate_item_import,
    get_item_type,handle_fill_system_item,
    get_system_data_uri,
    represents_int,
    validation_date_property,
    DefaultOrderedDict,
    defaultify,
    handle_get_all_sub_id_and_name
)
from invenio_i18n.ext import InvenioI18N, current_i18n
# from invenio_i18n.babel import set_locale
from flask import _request_ctx_stack
from weko_search_ui.config import (
    WEKO_REPO_USER,
    WEKO_SYS_USER,
    WEKO_IMPORT_SYSTEM_ITEMS,
    VERSION_TYPE_URI,
    ACCESS_RIGHT_TYPE_URI,
    RESOURCE_TYPE_URI
)

from unittest.mock import patch, Mock, MagicMock
from weko_search_ui import WekoSearchUI
# from flask_babelex import Babel
import copy

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

@pytest.fixture()
def test_records():
    results = []
    #
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord00.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord01.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord02.json"),
            "output": "",
        }
    )
    # 存在しない日付が設定されている
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "noExistentDate00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    # 日付がYYYY-MM-DD でない
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat01.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat02.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )

    return results

@pytest.fixture()
def test_list_records():
    tmp = []
    results = []
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records00.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records00_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records01.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records01_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records02.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records02_result.json"
            ),
        }
    )

    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records03.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records03_result.json"
            ),
        }
    )

    for t in tmp:
        with open(t.get("input"), encoding="utf-8") as f:
            input_data = json.load(f)
        with open(t.get("output"), encoding="utf-8") as f:
            output_data = json.load(f)
        results.append({"input": input_data, "output": output_data})
    return results

@pytest.fixture()
def test_importdata():
    files = [os.path.join(FIXTURE_DIR,'import00.zip')
    ]
    return files

@pytest.fixture()
def mocker_itemtype():
    item_type = MagicMock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15

    patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type)



#def get_tree_items(index_tree_id):
#def delete_records(index_tree_id, ignore_items):
#def get_journal_info(index_id=0):
#def get_feedback_mail_list():

# def check_permission():
def test_check_permission():
    user = MagicMock()
    user.roles = []
    with patch('flask_login.utils._get_user',return_value=user):
        assert check_permission() == False

    user.roles = [WEKO_SYS_USER]
    with patch('flask_login.utils._get_user',return_value=user):
        assert check_permission() == True

    user.roles = [WEKO_REPO_USER]
    with patch('flask_login.utils._get_user',return_value=user):
        assert check_permission() == True

    user.roles = ["ROLE"]
    with patch('flask_login.utils._get_user',return_value=user):
        assert check_permission() == False

    user.roles = ["ROLE",WEKO_SYS_USER]
    with patch('flask_login.utils._get_user',return_value=user):
        assert check_permission() == True

# def get_content_workflow(item):
def test_get_content_workflow():
    item = MagicMock()

    item.flowname = 'flowname'
    item.id = 'id'
    item.flow_id='flow_id'
    item.flow_define.flow_name='flow_name'
    item.itemtype.item_type_name.name='item_type_name'

    result = dict()
    result["flows_name"] = item.flows_name
    result["id"] = item.id
    result["itemtype_id"] = item.itemtype_id
    result["flow_id"] = item.flow_id
    result["flow_name"] = item.flow_define.flow_name
    result["item_type_name"] = item.itemtype.item_type_name.name

    assert get_content_workflow(item) == result

# def set_nested_item(data_dict, map_list, val):
# def convert_nested_item_to_list(data_dict, map_list):
# def define_default_dict():
# def defaultify(d: dict) -> dict:
# def handle_generate_key_path(key) -> list:
# def parse_to_json_form(data: list, item_path_not_existed=[], include_empty=False):

#def check_import_items(file, is_change_identifier: bool, is_gakuninrdm=False):
# def test_check_import_items(app,test_importdata,mocker):
#     app.config['WEKO_SEARCH_UI_IMPORT_TMP_PREFIX'] = 'importtest'
#     filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
#     with open(filepath,encoding="utf-8") as f:
#         item_map = json.load(f)

#     mocker.patch("weko_records.serializers.utils.get_mapping",return_value=item_map)
#     with app.test_request_context():
#         with set_locale('en'):
#             for file in test_importdata:
#                 assert check_import_items(file,False,False)==''

# def unpackage_import_file(data_path: str, csv_file_name: str, force_new=False):

def test_unpackage_import_file(app,mocker_itemtype):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
    with open(filepath,encoding="utf-8") as f:
        item_map = json.load(f)
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_type_mapping.json")
    with open(filepath,encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    with patch("weko_records.serializers.utils.get_mapping",return_value=item_map):
        with patch("weko_records.api.Mapping.get_record",return_value=item_type_mapping):

            filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file/result.json")
            with open(filepath,encoding="utf-8") as f:
                result = json.load(f)

            filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file/result_force_new.json")
            with open(filepath,encoding="utf-8") as f:
                result_force_new = json.load(f)

            path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file")
            with app.test_request_context():
                # with set_locale('en'):
                ctx = _request_ctx_stack.top
                if ctx is not None and hasattr(ctx, 'babel_locale'):
                    with setattr(ctx, 'babel_locale', 'en'):
                        assert unpackage_import_file(path,'items.csv','csv',False)==result
                        assert unpackage_import_file(path,'items.csv','csv',True)==result_force_new


# def getEncode(filepath):
def test_getEncode():
    csv_files = [
        {"file":"eucjp_lf_items.csv","enc":"euc-jp"},
        {"file":"iso2022jp_lf_items.csv","enc":"iso-2022-jp"},
        {"file":"sjis_lf_items.csv","enc":"shift_jis"},
        {"file":"utf8_cr_items.csv","enc":"utf-8"},
        {"file":"utf8_crlf_items.csv","enc":"utf-8"},
        {"file":"utf8_lf_items.csv","enc":"utf-8"},
        {"file":"utf8bom_lf_items.csv","enc":"utf-8"},
        {"file":"utf16be_bom_lf_items.csv","enc":"utf-16be"},
        {"file":"utf16le_bom_lf_items.csv","enc":"utf-16le"},
        # {"file":"utf32be_bom_lf_items.csv","enc":"utf-32"},
        # {"file":"utf32le_bom_lf_items.csv","enc":"utf-32"},
         {"file":"big5.txt","enc":""},

    ]

    for f in csv_files:
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv",f['file'])
        print(filepath)
        assert getEncode(filepath) == f['enc']


# def handle_convert_validate_msg_to_jp(message: str):
# def handle_validate_item_import(list_record, schema) -> list:

def test_handle_validate_item_import(app,mocker_itemtype):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv","data.json")
    with open(filepath,encoding="utf-8") as f:
        data = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        ctx = _request_ctx_stack.top
        if ctx is not None and hasattr(ctx, 'babel_locale'):
            with setattr(ctx, 'babel_locale', 'en'):
                assert handle_validate_item_import(list_record, data.get("item_type_schema", {}))==result

# def represents_int(s):

def test_represents_int():
    assert represents_int("a") == False
    assert represents_int("30") == True
    assert represents_int("31.1") == False


# def get_item_type(item_type_id=0) -> dict:
def test_get_item_type(mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_get_item_type_result.json"
    )
    with open(filepath, encoding="utf-8") as f:
        except_result = json.load(f)
        check_item_type1 = MagicMock()
        check_item_type1.schema = {'type': 'object', '$schema': 'http://json-schema.org/draft-04/schema#', 'required': ['pubdate', 'item_1617186331708', 'item_1617258105262'], 'properties': {'pubdate': {'type': 'string', 'title': 'PubDate', 'format': 'datetime'}, 'system_file': {'type': 'object', 'title': 'File Information', 'format': 'object', 'properties': {'subitem_systemfile_size': {'type': 'string', 'title': 'SYSTEMFILE Size', 'format': 'text'}, 'subitem_systemfile_version': {'type': 'string', 'title': 'SYSTEMFILE Version', 'format': 'text'}, 'subitem_systemfile_datetime': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_systemfile_datetime_date': {'type': 'string', 'title': 'SYSTEMFILE DateTime Date', 'format': 'datetime'}, 'subitem_systemfile_datetime_type': {'enum': ['Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid'], 'type': 'string', 'title': 'SYSTEMFILE DateTime Type', 'format': 'select'}}}, 'title': 'SYSTEMFILE DateTime', 'format': 'array'}, 'subitem_systemfile_filename': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_systemfile_filename_uri': {'type': 'string', 'title': 'SYSTEMFILE Filename URI', 'format': 'text'}, 'subitem_systemfile_filename_type': {'enum': ['Abstract', 'Fulltext', 'Summary', 'Thumbnail', 'Other'], 'type': 'string', 'title': 'SYSTEMFILE Filename Type', 'format': 'select'}, 'subitem_systemfile_filename_label': {'type': 'string', 'title': 'SYSTEMFILE Filename Label', 'format': 'text'}}}, 'title': 'SYSTEMFILE Filename', 'format': 'array'}, 'subitem_systemfile_mimetype': {'type': 'string', 'title': 'SYSTEMFILE MimeType', 'format': 'text'}}, 'system_prop': True}, 'item_1617186331708': {'type': 'array', 'items': {'type': 'object', 'required': ['subitem_1551255647225', 'subitem_1551255648112'], 'properties': {'subitem_1551255647225': {'type': 'string', 'title': 'Title', 'format': 'text', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'title_i18n_temp': {'en': 'Title', 'ja': 'タイトル'}}, 'subitem_1551255648112': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Title', 'maxItems': 9999, 'minItems': 1}, 'item_1617186385884': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1551255720400': {'type': 'string', 'title': 'Alternative Title', 'format': 'text', 'title_i18n': {'en': 'Alternative Title', 'ja': 'その他のタイトル'}, 'title_i18n_temp': {'en': 'Alternative Title', 'ja': 'その他のタイトル'}}, 'subitem_1551255721061': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Alternative Title', 'maxItems': 9999, 'minItems': 1}, 'item_1617186419668': {'type': 'array', 'items': {'type': 'object', 'properties': {'iscreator': {'type': 'string', 'title': 'iscreator', 'format': 'text', 'uniqueKey': 'item_1617186419668_iscreator', 'title_i18n': {'en': '', 'ja': ''}}, 'givenNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'givenName': {'type': 'string', 'title': '名', 'format': 'text', 'title_i18n': {'en': 'Given Name', 'ja': '名'}, 'title_i18n_temp': {'en': 'Given Name', 'ja': '名'}}, 'givenNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '作成者名', 'format': 'array'}, 'familyNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'familyName': {'type': 'string', 'title': '姓', 'format': 'text', 'title_i18n': {'en': 'Family Name', 'ja': '姓'}, 'title_i18n_temp': {'en': 'Family Name', 'ja': '姓'}}, 'familyNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '作成者姓', 'format': 'array'}, 'creatorMails': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'creatorMail': {'type': 'string', 'title': 'メールアドレス', 'format': 'text', 'title_i18n': {'en': 'Email Address', 'ja': 'メールアドレス'}, 'title_i18n_temp': {'en': 'Email Address', 'ja': 'メールアドレス'}}}}, 'title': '作成者メールアドレス', 'format': 'array'}, 'creatorNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'creatorName': {'type': 'string', 'title': '姓名', 'format': 'text', 'title_i18n': {'en': 'Name', 'ja': '姓名'}, 'title_i18n_temp': {'en': 'Name', 'ja': '姓名'}}, 'creatorNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '作成者姓名', 'format': 'array'}, 'nameIdentifiers': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'nameIdentifier': {'type': 'string', 'title': '作成者識別子', 'format': 'text', 'title_i18n': {'en': 'Creator Identifier', 'ja': '作成者識別子'}, 'title_i18n_temp': {'en': 'Creator Identifier', 'ja': '作成者識別子'}}, 'nameIdentifierURI': {'type': 'string', 'title': '作成者識別子URI', 'format': 'text', 'title_i18n': {'en': 'Creator Identifier URI', 'ja': '作成者識別子URI'}, 'title_i18n_temp': {'en': 'Creator Identifier URI', 'ja': '作成者識別子URI'}}, 'nameIdentifierScheme': {'type': ['null', 'string'], 'title': '作成者識別子Scheme', 'format': 'select', 'currentEnum': []}}}, 'title': '作成者識別子', 'format': 'array'}, 'creatorAffiliations': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'affiliationNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'affiliationName': {'type': 'string', 'title': '所属機関名', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name', 'ja': '所属機関名'}, 'title_i18n_temp': {'en': 'Affiliation Name', 'ja': '所属機関名'}}, 'affiliationNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '所属機関名', 'format': 'array'}, 'affiliationNameIdentifiers': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'affiliationNameIdentifier': {'type': 'string', 'title': '所属機関識別子', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name Identifier', 'ja': '所属機関識別子'}, 'title_i18n_temp': {'en': 'Affiliation Name Identifier', 'ja': '所属機関識別子'}}, 'affiliationNameIdentifierURI': {'type': 'string', 'title': '所属機関識別子URI', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name Identifier URI', 'ja': '所属機関識別子URI'}, 'title_i18n_temp': {'en': 'Affiliation Name Identifier URI', 'ja': '所属機関識別子URI'}}, 'affiliationNameIdentifierScheme': {'enum': [None, 'kakenhi', 'ISNI', 'Ringgold', 'GRID'], 'type': ['null', 'string'], 'title': '所属機関識別子スキーマ', 'format': 'select', 'currentEnum': ['kakenhi', 'ISNI', 'Ringgold', 'GRID']}}}, 'title': '所属機関識別子', 'format': 'array'}}}, 'title': '作成者所属', 'format': 'array'}, 'creatorAlternatives': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'creatorAlternative': {'type': 'string', 'title': '別名', 'format': 'text', 'title_i18n': {'en': 'Alternative Name', 'ja': '別名'}, 'title_i18n_temp': {'en': 'Alternative Name', 'ja': '別名'}}, 'creatorAlternativeLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '作成者別名', 'format': 'array'}}}, 'title': 'Creator', 'maxItems': 9999, 'minItems': 1}, 'item_1617186476635': {'type': 'object', 'title': 'Access Rights', 'properties': {'subitem_1522299639480': {'enum': [None, 'embargoed access', 'metadata only access', 'open access', 'restricted access'], 'type': ['null', 'string'], 'title': 'アクセス権', 'format': 'select', 'currentEnum': ['embargoed access', 'metadata only access', 'open access', 'restricted access']}, 'subitem_1600958577026': {'type': 'string', 'title': 'アクセス権URI', 'format': 'text', 'title_i18n': {'en': 'Access Rights URI', 'ja': 'アクセス権URI'}, 'title_i18n_temp': {'en': 'Access Rights URI', 'ja': 'アクセス権URI'}}}}, 'item_1617186499011': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522650717957': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522650727486': {'type': 'string', 'title': '権利情報Resource', 'format': 'text', 'title_i18n': {'en': 'Rights Information Resource', 'ja': '権利情報Resource'}, 'title_i18n_temp': {'en': 'Rights Information Resource', 'ja': '権利情報Resource'}}, 'subitem_1522651041219': {'type': 'string', 'title': '権利情報', 'format': 'text', 'title_i18n': {'en': 'Rights Information', 'ja': '権利情報'}, 'title_i18n_temp': {'en': 'Rights Information', 'ja': '権利情報'}}}}, 'title': 'Rights', 'maxItems': 9999, 'minItems': 1}, 'item_1617186609386': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522299896455': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522300014469': {'enum': [None, 'BSH', 'DDC', 'LCC', 'LCSH', 'MeSH', 'NDC', 'NDLC', 'NDLSH', 'SciVal', 'UDC', 'Other'], 'type': ['null', 'string'], 'title': '主題Scheme', 'format': 'select', 'currentEnum': ['BSH', 'DDC', 'LCC', 'LCSH', 'MeSH', 'NDC', 'NDLC', 'NDLSH', 'SciVal', 'UDC', 'Other']}, 'subitem_1522300048512': {'type': 'string', 'title': '主題URI', 'format': 'text', 'title_i18n': {'en': 'Subject URI', 'ja': '主題URI'}, 'title_i18n_temp': {'en': 'Subject URI', 'ja': '主題URI'}}, 'subitem_1523261968819': {'type': 'string', 'title': '主題', 'format': 'text', 'title_i18n': {'en': 'Subject', 'ja': '主題'}, 'title_i18n_temp': {'en': 'Subject', 'ja': '主題'}}}}, 'title': 'Subject', 'maxItems': 9999, 'minItems': 1}, 'item_1617186626617': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_description': {'type': 'string', 'title': '内容記述', 'format': 'textarea', 'title_i18n': {'en': 'Description', 'ja': '内容記述'}, 'title_i18n_temp': {'en': 'Description', 'ja': '内容記述'}}, 'subitem_description_type': {'enum': [None, 'Abstract', 'Methods', 'TableOfContents', 'TechnicalInfo', 'Other'], 'type': ['null', 'string'], 'title': '内容記述タイプ', 'format': 'select', 'currentEnum': ['Abstract', 'Methods', 'TableOfContents', 'TechnicalInfo', 'Other']}, 'subitem_description_language': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Description', 'maxItems': 9999, 'minItems': 1}, 'item_1617186643794': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522300295150': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522300316516': {'type': 'string', 'title': '出版者', 'format': 'text', 'title_i18n': {'en': 'Publisher', 'ja': '出版者'}, 'title_i18n_temp': {'en': 'Publisher', 'ja': '出版者'}}}}, 'title': 'Publisher', 'maxItems': 9999, 'minItems': 1}, 'item_1617186660861': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522300695726': {'enum': [None, 'Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid'], 'type': ['null', 'string'], 'title': '日付タイプ', 'format': 'select', 'currentEnum': ['Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid']}, 'subitem_1522300722591': {'type': 'string', 'title': '日付', 'format': 'datetime', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'title_i18n_temp': {'en': 'Date', 'ja': '日付'}}}}, 'title': 'Date', 'maxItems': 9999, 'minItems': 1}, 'item_1617186702042': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1551255818386': {'enum': [None, 'jpn', 'eng', 'fra', 'ita', 'spa', 'zho', 'rus', 'lat', 'msa', 'epo', 'ara', 'ell', 'kor'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['jpn', 'eng', 'fra', 'ita', 'spa', 'zho', 'rus', 'lat', 'msa', 'epo', 'ara', 'ell', 'kor']}}}, 'title': 'Language', 'maxItems': 9999, 'minItems': 1}, 'item_1617186783814': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_identifier_uri': {'type': 'string', 'title': '識別子', 'format': 'text', 'title_i18n': {'en': 'Identifier', 'ja': '識別子'}, 'title_i18n_temp': {'en': 'Identifier', 'ja': '識別子'}}, 'subitem_identifier_type': {'enum': [None, 'DOI', 'HDL', 'URI'], 'type': ['null', 'string'], 'title': '識別子タイプ', 'format': 'select', 'currentEnum': ['DOI', 'HDL', 'URI']}}}, 'title': 'Identifier', 'maxItems': 9999, 'minItems': 1}, 'item_1617186819068': {'type': 'object', 'title': 'Identifier Registration', 'properties': {'subitem_identifier_reg_text': {'type': 'string', 'title': 'ID登録', 'format': 'text', 'title_i18n': {'en': 'Identifier Registration', 'ja': 'ID登録'}, 'title_i18n_temp': {'en': 'Identifier Registration', 'ja': 'ID登録'}}, 'subitem_identifier_reg_type': {'enum': [None, 'JaLC', 'Crossref', 'DataCite', 'PMID'], 'type': ['null', 'string'], 'title': 'ID登録タイプ', 'format': 'select', 'currentEnum': ['JaLC', 'Crossref', 'DataCite', 'PMID']}}}, 'item_1617186859717': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522658018441': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522658031721': {'type': 'string', 'title': '時間的範囲', 'format': 'text', 'title_i18n': {'en': 'Temporal', 'ja': '時間的範囲'}, 'title_i18n_temp': {'en': 'Temporal', 'ja': '時間的範囲'}}}}, 'title': 'Temporal', 'maxItems': 9999, 'minItems': 1}, 'item_1617186882738': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_geolocation_box': {'type': 'object', 'title': '位置情報（空間）', 'format': 'object', 'properties': {'subitem_east_longitude': {'type': 'string', 'title': '東部経度', 'format': 'text', 'title_i18n': {'en': 'East Bound Longitude', 'ja': '東部経度'}, 'title_i18n_temp': {'en': 'East Bound Longitude', 'ja': '東部経度'}}, 'subitem_north_latitude': {'type': 'string', 'title': '北部緯度', 'format': 'text', 'title_i18n': {'en': 'North Bound Latitude', 'ja': '北部緯度'}, 'title_i18n_temp': {'en': 'North Bound Latitude', 'ja': '北部緯度'}}, 'subitem_south_latitude': {'type': 'string', 'title': '南部緯度', 'format': 'text', 'title_i18n': {'en': 'South Bound Latitude', 'ja': '南部緯度'}, 'title_i18n_temp': {'en': 'South Bound Latitude', 'ja': '南部緯度'}}, 'subitem_west_longitude': {'type': 'string', 'title': '西部経度', 'format': 'text', 'title_i18n': {'en': 'West Bound Longitude', 'ja': '西部経度'}, 'title_i18n_temp': {'en': 'West Bound Longitude', 'ja': '西部経度'}}}}, 'subitem_geolocation_place': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_geolocation_place_text': {'type': 'string', 'title': '位置情報（自由記述）', 'format': 'text', 'title_i18n': {'en': 'Geo Location Place', 'ja': '位置情報（自由記述）'}, 'title_i18n_temp': {'en': 'Geo Location Place', 'ja': '位置情報（自由記述）'}}}}, 'title': '位置情報（自由記述）', 'format': 'array'}, 'subitem_geolocation_point': {'type': 'object', 'title': '位置情報（点）', 'format': 'object', 'properties': {'subitem_point_latitude': {'type': 'string', 'title': '緯度', 'format': 'text', 'title_i18n': {'en': 'Point Latitude', 'ja': '緯度'}, 'title_i18n_temp': {'en': 'Point Latitude', 'ja': '緯度'}}, 'subitem_point_longitude': {'type': 'string', 'title': '経度', 'format': 'text', 'title_i18n': {'en': 'Point Longitude', 'ja': '経度'}, 'title_i18n_temp': {'en': 'Point Longitude', 'ja': '経度'}}}}}}, 'title': 'Geo Location', 'maxItems': 9999, 'minItems': 1}, 'item_1617186901218': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522399143519': {'type': 'object', 'title': '助成機関識別子', 'format': 'object', 'properties': {'subitem_1522399281603': {'enum': [None, 'Crossref Funder', 'GRID', 'ISNI', 'Other', 'kakenhi'], 'type': ['null', 'string'], 'title': '助成機関識別子タイプ', 'format': 'select', 'currentEnum': ['Crossref Funder', 'GRID', 'ISNI', 'Other', 'kakenhi']}, 'subitem_1522399333375': {'type': 'string', 'title': '助成機関識別子', 'format': 'text', 'title_i18n': {'en': 'Funder Identifier', 'ja': '助成機関識別子'}, 'title_i18n_temp': {'en': 'Funder Identifier', 'ja': '助成機関識別子'}}}}, 'subitem_1522399412622': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1522399416691': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522737543681': {'type': 'string', 'title': '助成機関名', 'format': 'text', 'title_i18n': {'en': 'Funder Name', 'ja': '助成機関名'}, 'title_i18n_temp': {'en': 'Funder Name', 'ja': '助成機関名'}}}}, 'title': '助成機関名', 'format': 'array'}, 'subitem_1522399571623': {'type': 'object', 'title': '研究課題番号', 'format': 'object', 'properties': {'subitem_1522399585738': {'type': 'string', 'title': '研究課題URI', 'format': 'text', 'title_i18n': {'en': 'Award URI', 'ja': '研究課題URI'}, 'title_i18n_temp': {'en': 'Award URI', 'ja': '研究課題URI'}}, 'subitem_1522399628911': {'type': 'string', 'title': '研究課題番号', 'format': 'text', 'title_i18n': {'en': 'Award Number', 'ja': '研究課題番号'}, 'title_i18n_temp': {'en': 'Award Number', 'ja': '研究課題番号'}}}}, 'subitem_1522399651758': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1522721910626': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522721929892': {'type': 'string', 'title': '研究課題名', 'format': 'text', 'title_i18n': {'en': 'Award Title', 'ja': '研究課題名'}, 'title_i18n_temp': {'en': 'Award Title', 'ja': '研究課題名'}}}}, 'title': '研究課題名', 'format': 'array'}}}, 'title': 'Funding Reference', 'maxItems': 9999, 'minItems': 1}, 'item_1617186920753': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522646500366': {'enum': [None, 'PISSN', 'EISSN', 'ISSN', 'NCID'], 'type': ['null', 'string'], 'title': '収録物識別子タイプ', 'format': 'select', 'currentEnum': ['PISSN', 'EISSN', 'ISSN', 'NCID']}, 'subitem_1522646572813': {'type': 'string', 'title': '収録物識別子', 'format': 'text', 'title_i18n': {'en': 'Source Identifier', 'ja': '収録物識別子'}, 'title_i18n_temp': {'en': 'Source Identifier', 'ja': '収録物識別子'}}}}, 'title': 'Source Identifier', 'maxItems': 9999, 'minItems': 1}, 'item_1617186941041': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522650068558': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1522650091861': {'type': 'string', 'title': '収録物名', 'format': 'text', 'title_i18n': {'en': 'Source Title', 'ja': '収録物名'}, 'title_i18n_temp': {'en': 'Source Title', 'ja': '収録物名'}}}}, 'title': 'Source Title', 'maxItems': 9999, 'minItems': 1}, 'item_1617186959569': {'type': 'object', 'title': 'Volume Number', 'properties': {'subitem_1551256328147': {'type': 'string', 'title': 'Volume Number', 'format': 'text', 'title_i18n': {'en': 'Volume Number', 'ja': '巻'}, 'title_i18n_temp': {'en': 'Volume Number', 'ja': '巻'}}}}, 'item_1617186981471': {'type': 'object', 'title': 'Issue Number', 'properties': {'subitem_1551256294723': {'type': 'string', 'title': 'Issue Number', 'format': 'text', 'title_i18n': {'en': 'Issue Number', 'ja': '号'}, 'title_i18n_temp': {'en': 'Issue Number', 'ja': '号'}}}}, 'item_1617186994930': {'type': 'object', 'title': 'Number of Pages', 'properties': {'subitem_1551256248092': {'type': 'string', 'title': 'Number of Pages', 'format': 'text', 'title_i18n': {'en': 'Number of Pages', 'ja': 'ページ数'}, 'title_i18n_temp': {'en': 'Number of Pages', 'ja': 'ページ数'}}}}, 'item_1617187024783': {'type': 'object', 'title': 'Page Start', 'properties': {'subitem_1551256198917': {'type': 'string', 'title': 'Page Start', 'format': 'text', 'title_i18n': {'en': 'Page Start', 'ja': '開始ページ'}, 'title_i18n_temp': {'en': 'Page Start', 'ja': '開始ページ'}}}}, 'item_1617187045071': {'type': 'object', 'title': 'Page End', 'properties': {'subitem_1551256185532': {'type': 'string', 'title': 'Page End', 'format': 'text', 'title_i18n': {'en': 'Page End', 'ja': '終了ページ'}, 'title_i18n_temp': {'en': 'Page End', 'ja': '終了ページ'}}}}, 'item_1617187056579': {'type': 'object', 'title': 'Bibliographic Information', 'properties': {'bibliographicPageEnd': {'type': 'string', 'title': '終了ページ', 'format': 'text', 'title_i18n': {'en': 'Page End', 'ja': '終了ページ'}, 'title_i18n_temp': {'en': 'Page End', 'ja': '終了ページ'}}, 'bibliographic_titles': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'bibliographic_title': {'type': 'string', 'title': 'タイトル', 'format': 'text', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'title_i18n_temp': {'en': 'Title', 'ja': 'タイトル'}}, 'bibliographic_titleLang': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '雑誌名', 'format': 'array'}, 'bibliographicPageStart': {'type': 'string', 'title': '開始ページ', 'format': 'text', 'title_i18n': {'en': 'Page Start', 'ja': '開始ページ'}, 'title_i18n_temp': {'en': 'Page Start', 'ja': '開始ページ'}}, 'bibliographicIssueDates': {'type': 'object', 'title': '発行日', 'format': 'object', 'properties': {'bibliographicIssueDate': {'type': 'string', 'title': '日付', 'format': 'datetime', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'title_i18n_temp': {'en': 'Date', 'ja': '日付'}}, 'bibliographicIssueDateType': {'enum': [None, 'Issued'], 'type': ['null', 'string'], 'title': '日付タイプ', 'format': 'select', 'currentEnum': ['Issued']}}}, 'bibliographicIssueNumber': {'type': 'string', 'title': '号', 'format': 'text', 'title_i18n': {'en': 'Issue Number', 'ja': '号'}, 'title_i18n_temp': {'en': 'Issue Number', 'ja': '号'}}, 'bibliographicVolumeNumber': {'type': 'string', 'title': '巻', 'format': 'text', 'title_i18n': {'en': 'Volume Number', 'ja': '巻'}, 'title_i18n_temp': {'en': 'Volume Number', 'ja': '巻'}}, 'bibliographicNumberOfPages': {'type': 'string', 'title': 'ページ数', 'format': 'text', 'title_i18n': {'en': 'Number of Page', 'ja': 'ページ数'}, 'title_i18n_temp': {'en': 'Number of Page', 'ja': 'ページ数'}}}}, 'item_1617187087799': {'type': 'object', 'title': 'Dissertation Number', 'properties': {'subitem_1551256171004': {'type': 'string', 'title': 'Dissertation Number', 'format': 'text', 'title_i18n': {'en': 'Dissertation Number', 'ja': '学位授与番号'}, 'title_i18n_temp': {'en': 'Dissertation Number', 'ja': '学位授与番号'}}}}, 'item_1617187112279': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1551256126428': {'type': 'string', 'title': 'Degree Name', 'format': 'text', 'title_i18n': {'en': 'Degree Name', 'ja': '学位名'}, 'title_i18n_temp': {'en': 'Degree Name', 'ja': '学位名'}}, 'subitem_1551256129013': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Degree Name', 'maxItems': 9999, 'minItems': 1}, 'item_1617187136212': {'type': 'object', 'title': 'Date Granted', 'properties': {'subitem_1551256096004': {'type': 'string', 'title': 'Date Granted', 'format': 'datetime', 'title_i18n': {'en': 'Date Granted', 'ja': '学位授与年月日'}, 'title_i18n_temp': {'en': 'Date Granted', 'ja': '学位授与年月日'}}}}, 'item_1617187187528': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1599711633003': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1599711636923': {'type': 'string', 'title': 'Conference Name', 'format': 'text', 'title_i18n': {'en': 'Conference Name', 'ja': '会議名'}, 'title_i18n_temp': {'en': 'Conference Name', 'ja': '会議名'}}, 'subitem_1599711645590': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Conference Name', 'format': 'array'}, 'subitem_1599711655652': {'type': 'string', 'title': 'Conference Sequence', 'format': 'text', 'title_i18n': {'en': 'Conference Sequence', 'ja': '回次'}, 'title_i18n_temp': {'en': 'Conference Sequence', 'ja': '回次'}}, 'subitem_1599711660052': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1599711680082': {'type': 'string', 'title': 'Conference Sponsor', 'format': 'text', 'title_i18n': {'en': 'Conference Sponsor', 'ja': '主催機関'}, 'title_i18n_temp': {'en': 'Conference Sponsor', 'ja': '主催機関'}}, 'subitem_1599711686511': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Conference Sponsor', 'format': 'array'}, 'subitem_1599711699392': {'type': 'object', 'title': 'Conference Date', 'format': 'object', 'properties': {'subitem_1599711704251': {'type': 'string', 'title': 'Conference Date', 'format': 'text', 'title_i18n': {'en': 'Conference Date', 'ja': '開催期間'}, 'title_i18n_temp': {'en': 'Conference Date', 'ja': '開催期間'}}, 'subitem_1599711712451': {'type': 'string', 'title': 'Start Day', 'format': 'text', 'title_i18n': {'en': 'Start Day', 'ja': '開始日'}, 'title_i18n_temp': {'en': 'Start Day', 'ja': '開始日'}}, 'subitem_1599711727603': {'type': 'string', 'title': 'Start Month', 'format': 'text', 'title_i18n': {'en': 'Start Month', 'ja': '開始月'}, 'title_i18n_temp': {'en': 'Start Month', 'ja': '開始月'}}, 'subitem_1599711731891': {'type': 'string', 'title': 'Start Year', 'format': 'text', 'title_i18n': {'en': 'Start Year', 'ja': '開始年'}, 'title_i18n_temp': {'en': 'Start Year', 'ja': '開始年'}}, 'subitem_1599711735410': {'type': 'string', 'title': 'End Day', 'format': 'text', 'title_i18n': {'en': 'End Day', 'ja': '終了日'}, 'title_i18n_temp': {'en': 'End Day', 'ja': '終了日'}}, 'subitem_1599711739022': {'type': 'string', 'title': 'End Month', 'format': 'text', 'title_i18n': {'en': 'End Month', 'ja': '終了月'}, 'title_i18n_temp': {'en': 'End Month', 'ja': '終了月'}}, 'subitem_1599711743722': {'type': 'string', 'title': 'End Year', 'format': 'text', 'title_i18n': {'en': 'End Year', 'ja': '終了年'}, 'title_i18n_temp': {'en': 'End Year', 'ja': '終了年'}}, 'subitem_1599711745532': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'subitem_1599711758470': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1599711769260': {'type': 'string', 'title': 'Conference Venue', 'format': 'text', 'title_i18n': {'en': 'Conference Venue', 'ja': '開催会場'}, 'title_i18n_temp': {'en': 'Conference Venue', 'ja': '開催会場'}}, 'subitem_1599711775943': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Conference Venue', 'format': 'array'}, 'subitem_1599711788485': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1599711798761': {'type': 'string', 'title': 'Conference Place', 'format': 'text', 'title_i18n': {'en': 'Conference Place', 'ja': '開催地'}, 'title_i18n_temp': {'en': 'Conference Place', 'ja': '開催地'}}, 'subitem_1599711803382': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Conference Place', 'format': 'array'}, 'subitem_1599711813532': {'enum': [None, 'JPN', 'ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ARE', 'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BES', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH', 'BLM', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN', 'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CUW', 'CXR', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN', 'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'KAZ', 'KEN', 'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAC', 'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD', 'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR', 'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK', 'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI', 'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU', 'RUS', 'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB', 'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'SSD', 'STP', 'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SXM', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA', 'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV', 'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT', 'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM', 'ZAF', 'ZMB', 'ZWE'], 'type': ['null', 'string'], 'title': 'Conference Country', 'format': 'select', 'currentEnum': ['JPN', 'ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ARE', 'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BES', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH', 'BLM', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN', 'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CUW', 'CXR', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN', 'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'KAZ', 'KEN', 'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAC', 'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD', 'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR', 'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK', 'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI', 'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU', 'RUS', 'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB', 'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'SSD', 'STP', 'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SXM', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA', 'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV', 'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT', 'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM', 'ZAF', 'ZMB', 'ZWE']}}}, 'title': 'Conference', 'maxItems': 9999, 'minItems': 1}, 'item_1617258105262': {'type': 'object', 'title': 'Resource Type', 'required': ['resourceuri', 'resourcetype'], 'properties': {'resourceuri': {'type': 'string', 'title': '資源タイプ識別子', 'format': 'text', 'title_i18n': {'en': 'Resource Type Identifier', 'ja': '資源タイプ識別子'}, 'title_i18n_temp': {'en': 'Resource Type Identifier', 'ja': '資源タイプ識別子'}}, 'resourcetype': {'enum': [None, 'conference paper', 'data paper', 'departmental bulletin paper', 'editorial', 'journal article', 'newspaper', 'periodical', 'review article', 'software paper', 'article', 'book', 'book part', 'cartographic material', 'map', 'conference object', 'conference proceedings', 'conference poster', 'dataset', 'interview', 'image', 'still image', 'moving image', 'video', 'lecture', 'patent', 'internal report', 'report', 'research report', 'technical report', 'policy report', 'report part', 'working paper', 'data management plan', 'sound', 'thesis', 'bachelor thesis', 'master thesis', 'doctoral thesis', 'interactive resource', 'learning object', 'manuscript', 'musical notation', 'research proposal', 'software', 'technical documentation', 'workflow', 'other'], 'type': ['null', 'string'], 'title': '資源タイプ', 'format': 'select', 'currentEnum': ['conference paper', 'data paper', 'departmental bulletin paper', 'editorial', 'journal article', 'newspaper', 'periodical', 'review article', 'software paper', 'article', 'book', 'book part', 'cartographic material', 'map', 'conference object', 'conference proceedings', 'conference poster', 'dataset', 'interview', 'image', 'still image', 'moving image', 'video', 'lecture', 'patent', 'internal report', 'report', 'research report', 'technical report', 'policy report', 'report part', 'working paper', 'data management plan', 'sound', 'thesis', 'bachelor thesis', 'master thesis', 'doctoral thesis', 'interactive resource', 'learning object', 'manuscript', 'musical notation', 'research proposal', 'software', 'technical documentation', 'workflow', 'other']}}}, 'item_1617265215918': {'type': 'object', 'title': 'Version Type', 'properties': {'subitem_1522305645492': {'enum': [None, 'AO', 'SMUR', 'AM', 'P', 'VoR', 'CVoR', 'EVoR', 'NA'], 'type': ['null', 'string'], 'title': '出版タイプ', 'format': 'select', 'currentEnum': ['AO', 'SMUR', 'AM', 'P', 'VoR', 'CVoR', 'EVoR', 'NA']}, 'subitem_1600292170262': {'type': 'string', 'title': '出版タイプResource', 'format': 'text', 'title_i18n': {'en': 'Version Type Resource', 'ja': '出版タイプResource'}, 'title_i18n_temp': {'en': 'Version Type Resource', 'ja': '出版タイプResource'}}}}, 'item_1617349709064': {'type': 'array', 'items': {'type': 'object', 'properties': {'givenNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'givenName': {'type': 'string', 'title': '名', 'format': 'text', 'title_i18n': {'en': 'Given Name', 'ja': '名'}, 'title_i18n_temp': {'en': 'Given Name', 'ja': '名'}}, 'givenNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '寄与者名', 'format': 'array'}, 'familyNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'familyName': {'type': 'string', 'title': '姓', 'format': 'text', 'title_i18n': {'en': 'Family Name', 'ja': '姓'}, 'title_i18n_temp': {'en': 'Family Name', 'ja': '姓'}}, 'familyNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '寄与者姓', 'format': 'array'}, 'contributorType': {'enum': [None, 'ContactPerson', 'DataCollector', 'DataCurator', 'DataManager', 'Distributor', 'Editor', 'HostingInstitution', 'Producer', 'ProjectLeader', 'ProjectManager', 'ProjectMember', 'RelatedPerson', 'Researcher', 'ResearchGroup', 'Sponsor', 'Supervisor', 'WorkPackageLeader', 'Other'], 'type': ['null', 'string'], 'title': '寄与者タイプ', 'format': 'select', 'currentEnum': ['ContactPerson', 'DataCollector', 'DataCurator', 'DataManager', 'Distributor', 'Editor', 'HostingInstitution', 'Producer', 'ProjectLeader', 'ProjectManager', 'ProjectMember', 'RelatedPerson', 'Researcher', 'ResearchGroup', 'Sponsor', 'Supervisor', 'WorkPackageLeader', 'Other']}, 'nameIdentifiers': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'nameIdentifier': {'type': 'string', 'title': '寄与者識別子', 'format': 'text', 'title_i18n': {'en': 'Contributor Identifier', 'ja': '寄与者識別子'}, 'title_i18n_temp': {'en': 'Contributor Identifier', 'ja': '寄与者識別子'}}, 'nameIdentifierURI': {'type': 'string', 'title': '寄与者識別子URI', 'format': 'text', 'title_i18n': {'en': 'Contributor Identifier URI', 'ja': '寄与者識別子URI'}, 'title_i18n_temp': {'en': 'Contributor Identifier URI', 'ja': '寄与者識別子URI'}}, 'nameIdentifierScheme': {'type': ['null', 'string'], 'title': '寄与者識別子Scheme', 'format': 'select', 'currentEnum': []}}}, 'title': '寄与者識別子', 'format': 'array'}, 'contributorMails': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'contributorMail': {'type': 'string', 'title': 'メールアドレス', 'format': 'text', 'title_i18n': {'en': 'Email Address', 'ja': 'メールアドレス'}, 'title_i18n_temp': {'en': 'Email Address', 'ja': 'メールアドレス'}}}}, 'title': '寄与者メールアドレス', 'format': 'array'}, 'contributorNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'lang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'contributorName': {'type': 'string', 'title': '姓名', 'format': 'text', 'title_i18n': {'en': 'Name', 'ja': '姓名'}, 'title_i18n_temp': {'en': 'Name', 'ja': '姓名'}}}}, 'title': '寄与者姓名', 'format': 'array'}, 'contributorAffiliations': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'contributorAffiliationNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'contributorAffiliationName': {'type': 'string', 'title': '所属機関名', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name', 'ja': '所属機関名'}, 'title_i18n_temp': {'en': 'Affiliation Name', 'ja': '所属機関名'}}, 'contributorAffiliationNameLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '所属機関識別子', 'format': 'array'}, 'contributorAffiliationNameIdentifiers': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'contributorAffiliationURI': {'type': 'string', 'title': '所属機関識別子URI', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name Identifier URI', 'ja': '所属機関識別子URI'}, 'title_i18n_temp': {'en': 'Affiliation Name Identifier URI', 'ja': '所属機関識別子URI'}}, 'contributorAffiliationScheme': {'enum': [None, 'kakenhi', 'ISNI', 'Ringgold', 'GRID'], 'type': ['null', 'string'], 'title': '所属機関識別子スキーマ', 'format': 'select', 'currentEnum': ['kakenhi', 'ISNI', 'Ringgold', 'GRID']}, 'contributorAffiliationNameIdentifier': {'type': 'string', 'title': '所属機関識別子', 'format': 'text', 'title_i18n': {'en': 'Affiliation Name Identifier', 'ja': '所属機関識別子'}, 'title_i18n_temp': {'en': 'Affiliation Name Identifier', 'ja': '所属機関識別子'}}}}, 'title': '所属機関識別子', 'format': 'array'}}}, 'title': '寄与者所属', 'format': 'array'}, 'contributorAlternatives': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'contributorAlternative': {'type': 'string', 'title': '別名', 'format': 'text', 'title_i18n': {'en': 'Alternative Name', 'ja': '別名'}, 'title_i18n_temp': {'en': 'Alternative Name', 'ja': '別名'}}, 'contributorAlternativeLang': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '寄与者別名', 'format': 'array'}}}, 'title': 'Contributor', 'maxItems': 9999, 'minItems': 1}, 'item_1617349808926': {'type': 'object', 'title': 'Version', 'properties': {'subitem_1523263171732': {'type': 'string', 'title': 'バージョン情報', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}}}}, 'item_1617351524846': {'type': 'object', 'title': 'APC', 'properties': {'subitem_1523260933860': {'enum': [None, 'Paid', 'Fully waived', 'Not required', 'Partially waived', 'Not charged', 'Unknown'], 'type': ['null', 'string'], 'title': 'APC', 'format': 'select', 'currentEnum': ['Paid', 'Fully waived', 'Not required', 'Partially waived', 'Not charged', 'Unknown']}}}, 'item_1617353299429': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1522306207484': {'enum': [None, 'isVersionOf', 'hasVersion', 'isPartOf', 'hasPart', 'isReferencedBy', 'references', 'isFormatOf', 'hasFormat', 'isReplacedBy', 'replaces', 'isRequiredBy', 'requires', 'isSupplementTo', 'isSupplementedBy', 'isIdenticalTo', 'isDerivedFrom', 'isSourceOf'], 'type': ['null', 'string'], 'title': '関連タイプ', 'format': 'select', 'currentEnum': ['isVersionOf', 'hasVersion', 'isPartOf', 'hasPart', 'isReferencedBy', 'references', 'isFormatOf', 'hasFormat', 'isReplacedBy', 'replaces', 'isRequiredBy', 'requires', 'isSupplementTo', 'isSupplementedBy', 'isIdenticalTo', 'isDerivedFrom', 'isSourceOf']}, 'subitem_1522306287251': {'type': 'object', 'title': '関連識別子', 'format': 'object', 'properties': {'subitem_1522306382014': {'enum': [None, 'ARK', 'arXiv', 'DOI', 'HDL', 'ICHUSHI', 'ISBN', 'J-GLOBAL', 'Local', 'PISSN', 'EISSN', 'ISSN（非推奨）', 'NAID', 'NCID', 'PMID', 'PURL', 'SCOPUS', 'URI', 'WOS'], 'type': ['null', 'string'], 'title': '識別子タイプ', 'format': 'select', 'currentEnum': ['ARK', 'arXiv', 'DOI', 'HDL', 'ICHUSHI', 'ISBN', 'J-GLOBAL', 'Local', 'PISSN', 'EISSN', 'ISSN（非推奨）', 'NAID', 'NCID', 'PMID', 'PURL', 'SCOPUS', 'URI', 'WOS']}, 'subitem_1522306436033': {'type': 'string', 'title': '関連識別子', 'format': 'text', 'title_i18n': {'en': 'Relation Identifier', 'ja': '関連識別子'}, 'title_i18n_temp': {'en': 'Relation Identifier', 'ja': '関連識別子'}}}}, 'subitem_1523320863692': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1523320867455': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1523320909613': {'type': 'string', 'title': '関連名称', 'format': 'text', 'title_i18n': {'en': 'Related Title', 'ja': '関連名称'}, 'title_i18n_temp': {'en': 'Related Title', 'ja': '関連名称'}}}}, 'title': '関連名称', 'format': 'array'}}}, 'title': 'Relation', 'maxItems': 9999, 'minItems': 1}, 'item_1617605131499': {'type': 'array', 'items': {'type': 'object', 'properties': {'url': {'type': 'object', 'title': '本文URL', 'format': 'object', 'properties': {'url': {'type': 'string', 'title': '本文URL', 'format': 'text', 'title_i18n': {'en': 'Text URL', 'ja': '本文URL'}, 'title_i18n_temp': {'en': 'Text URL', 'ja': '本文URL'}}, 'label': {'type': 'string', 'title': 'ラベル', 'format': 'text', 'title_i18n': {'en': 'Label', 'ja': 'ラベル'}, 'title_i18n_temp': {'en': 'Label', 'ja': 'ラベル'}}, 'objectType': {'enum': [None, 'abstract', 'summary', 'fulltext', 'thumbnail', 'other'], 'type': ['null', 'string'], 'title': 'オブジェクトタイプ', 'format': 'select', 'currentEnum': ['abstract', 'summary', 'fulltext', 'thumbnail', 'other']}}}, 'date': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'dateType': {'type': ['null', 'string'], 'title': '日付タイプ', 'format': 'select', 'currentEnum': []}, 'dateValue': {'type': 'string', 'title': '日付', 'format': 'datetime', 'title_i18n': {'en': '', 'ja': ''}}}}, 'title': 'オープンアクセスの日付', 'format': 'array'}, 'format': {'type': 'string', 'title': 'フォーマット', 'format': 'text', 'title_i18n': {'en': 'Format', 'ja': 'フォーマット'}, 'title_i18n_temp': {'en': 'Format', 'ja': 'フォーマット'}}, 'groups': {'type': ['null', 'string'], 'title': 'グループ', 'format': 'select', 'currentEnum': []}, 'version': {'type': 'string', 'title': 'バージョン情報', 'format': 'text', 'title_i18n': {'en': 'Version Information', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version Information', 'ja': 'バージョン情報'}}, 'fileDate': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'fileDateType': {'enum': [None, 'Accepted', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid'], 'type': ['null', 'string'], 'title': '日付タイプ', 'format': 'select', 'currentEnum': ['Accepted', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid']}, 'fileDateValue': {'type': 'string', 'title': '日付', 'format': 'datetime', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'title_i18n_temp': {'en': 'Date', 'ja': '日付'}}}}, 'title': '日付', 'format': 'array'}, 'filename': {'type': ['null', 'string'], 'title': '表示名', 'format': 'text', 'title_i18n': {'en': 'FileName', 'ja': '表示名'}, 'title_i18n_temp': {'en': 'FileName', 'ja': '表示名'}}, 'filesize': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'value': {'type': 'string', 'title': 'サイズ', 'format': 'text', 'title_i18n': {'en': 'Size', 'ja': 'サイズ'}, 'title_i18n_temp': {'en': 'Size', 'ja': 'サイズ'}}}}, 'title': 'サイズ', 'format': 'array'}, 'accessrole': {'enum': ['open_access', 'open_date', 'open_login', 'open_no'], 'type': ['null', 'string'], 'title': 'アクセス', 'format': 'radios'}, 'displaytype': {'enum': [None, 'detail', 'simple', 'preview'], 'type': ['null', 'string'], 'title': '表示形式', 'format': 'select', 'currentEnum': ['detail', 'simple', 'preview']}, 'licensefree': {'type': 'string', 'title': '自由ライセンス', 'format': 'textarea', 'title_i18n': {'en': '自由ライセンス', 'ja': '自由ライセンス'}}, 'licensetype': {'type': ['null', 'string'], 'title': 'ライセンス', 'format': 'select', 'currentEnum': []}}}, 'title': 'File', 'maxItems': 9999, 'minItems': 1}, 'item_1617610673286': {'type': 'array', 'items': {'type': 'object', 'properties': {'nameIdentifiers': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'nameIdentifier': {'type': 'string', 'title': '権利者識別子', 'format': 'text', 'title_i18n': {'en': 'Right Holder Identifier', 'ja': '権利者識別子'}, 'title_i18n_temp': {'en': 'Right Holder Identifier', 'ja': '権利者識別子'}}, 'nameIdentifierURI': {'type': 'string', 'title': '権利者識別子URI', 'format': 'text', 'title_i18n': {'en': 'Right Holder Identifier URI', 'ja': '権利者識別子URI'}, 'title_i18n_temp': {'en': 'Right Holder Identifier URI', 'ja': '権利者識別子URI'}}, 'nameIdentifierScheme': {'type': ['null', 'string'], 'title': '権利者識別子Scheme', 'format': 'select', 'currentEnum': []}}}, 'title': '権利者識別子', 'format': 'array'}, 'rightHolderNames': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'rightHolderName': {'type': 'string', 'title': '権利者名', 'format': 'text', 'title_i18n': {'en': 'Right Holder Name', 'ja': '権利者名'}, 'title_i18n_temp': {'en': 'Right Holder Name', 'ja': '権利者名'}}, 'rightHolderLanguage': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': '言語', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': '権利者名', 'format': 'array'}}}, 'title': 'Rights Holder', 'maxItems': 9999, 'minItems': 1}, 'item_1617620223087': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1565671149650': {'enum': [None, 'ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'ja-Kana', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}, 'subitem_1565671169640': {'type': 'string', 'title': 'Banner Headline', 'format': 'text', 'title_i18n': {'en': 'Banner Headline', 'ja': '大見出し'}, 'title_i18n_temp': {'en': 'Banner Headline', 'ja': '大見出し'}}, 'subitem_1565671178623': {'type': 'string', 'title': 'Subheading', 'format': 'text', 'title_i18n': {'en': 'Subheading', 'ja': '小見出し'}, 'title_i18n_temp': {'en': 'Subheading', 'ja': '小見出し'}}}}, 'title': 'Heading', 'maxItems': 9999, 'minItems': 1}, 'item_1617944105607': {'type': 'array', 'items': {'type': 'object', 'properties': {'subitem_1551256015892': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256027296': {'type': 'string', 'title': 'Degree Grantor Name Identifier', 'format': 'text', 'title_i18n': {'en': 'Degree Grantor Name Identifier', 'ja': '学位授与機関識別子'}, 'title_i18n_temp': {'en': 'Degree Grantor Name Identifier', 'ja': '学位授与機関識別子'}}, 'subitem_1551256029891': {'enum': [None, 'kakenhi'], 'type': ['null', 'string'], 'title': 'Degree Grantor Name Identifier Scheme', 'format': 'select', 'currentEnum': ['kakenhi']}}}, 'title': 'Degree Grantor Name Identifier', 'format': 'array'}, 'subitem_1551256037922': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256042287': {'type': 'string', 'title': 'Degree Grantor Name', 'format': 'text', 'title_i18n': {'en': 'Degree Grantor Name', 'ja': '学位授与機関名'}, 'title_i18n_temp': {'en': 'Degree Grantor Name', 'ja': '学位授与機関名'}}, 'subitem_1551256047619': {'enum': [None, 'ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']}}}, 'title': 'Degree Grantor Name', 'format': 'array'}}}, 'title': 'Degree Grantor', 'maxItems': 9999, 'minItems': 1}, 'system_identifier_doi': {'type': 'object', 'title': 'Persistent Identifier(DOI)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}, 'system_identifier_hdl': {'type': 'object', 'title': 'Persistent Identifier(HDL)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}, 'system_identifier_uri': {'type': 'object', 'title': 'Persistent Identifier(URI)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}}, 'description': ''}
        check_item_type1.item_type_name.name = "デフォルトアイテムタイプ（フル）"
        check_item_type1.item_type_name.item_type.id = 15

        with patch("weko_records.api.ItemTypes.get_by_id", return_value=check_item_type1):
            result = get_item_type(15)
            assert result['is_lastest']== False
            assert result['name']==except_result['name']
            assert result['item_type_id']==except_result['item_type_id']
            assert result['schema']==except_result['schema']
            assert result is not None

            assert get_item_type(0) == {}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_exist_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_exist_record(app):
    case =  unittest.TestCase()
    # case 1 import new items
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 2 import items with id
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record1.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result1.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        ctx = _request_ctx_stack.top
        if ctx is not None and hasattr(ctx, 'babel_locale'):
            with setattr(ctx, 'babel_locale', 'en'):
                case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 3 import items with id and uri
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record2.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result2.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        ctx = _request_ctx_stack.top
        if ctx is not None and hasattr(ctx, 'babel_locale'):
            with setattr(ctx, 'babel_locale', 'en'):
                with patch("weko_deposit.api.WekoRecord.get_record_by_pid") as m:
                    m.return_value.pid.is_deleted.return_value = False
                    m.return_value.get.side_effect = [1,2,3,4,5,6,7,8,9,10]
                    case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 4 import new items with doi_ra
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record3.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record3_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        ctx = _request_ctx_stack.top
        if ctx is not None and hasattr(ctx, 'babel_locale'):
            with setattr(ctx, 'babel_locale', 'en'):
                case.assertCountEqual(handle_check_exist_record(list_record),result)

    # with open(filepath,encoding="utf-8", mode='wt') as f:
    #      json.dump(result,f,ensure_ascii=False)
    # for item in list_record:
    #     item['uri'] = "http://localhost/records/"+str(item['id'])
    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record2.json")
    # with open(filepath,encoding="utf-8", mode='wt') as f:
    #     json.dump(list_record,f,ensure_ascii=False)
    # i = 1
    # for record in list_record:
    #     record['id'] = i
    #     i=i+1

    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record1.json")
    # with open(filepath,encoding="utf-8", mode='wt') as f:
    #       json.dump(list_record,f,ensure_ascii=False)


    # with open(filepath,encoding="utf-8", mode='wt') as f:
    #      result = handle_check_exist_record(list_record)
    #      json.dump(result,f,ensure_ascii=False)


# def make_csv_by_line(lines):
# def make_stats_csv(raw_stats, list_name):
# def create_deposit(item_id):
# def clean_thumbnail_file(deposit, root_path, thumbnail_path):
# def up_load_file(record, root_path, deposit, allow_upload_file_content, old_files):
# def get_file_name(file_path):
# def register_item_metadata(item, root_path, is_gakuninrdm=False):
# def update_publish_status(item_id, status):
# def handle_workflow(item: dict):
# def create_work_flow(item_type_id):
# def create_flow_define():
# def import_items_to_system(item: dict, request_info=None, is_gakuninrdm=False):
# def handle_item_title(list_record):
# def handle_check_and_prepare_publish_status(list_record):
# def handle_check_and_prepare_index_tree(list_record):
# def handle_check_and_prepare_feedback_mail(list_record):
# def handle_set_change_identifier_flag(list_record, is_change_identifier):
# def handle_check_cnri(list_record):
# def handle_check_doi_indexes(list_record):
# def handle_check_doi_ra(list_record):

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_utils.py::test_handle_check_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_handle_check_doi(app):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record)==None

    # case new items with doi_ra
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_doi.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record)==None

# def register_item_handle(item):
# def prepare_doi_setting():
# def get_doi_prefix(doi_ra):
# def get_doi_link(doi_ra, data):
# def prepare_doi_link(item_id):
# def register_item_doi(item):
# def register_item_update_publish_status(item, status):
# def handle_doi_required_check(record):

# def handle_check_date(list_record):
def test_handle_check_date(app, test_list_records, mocker_itemtype, db):
    for t in test_list_records:
        input_data = t.get("input")
        output_data = t.get("output")
        with app.app_context():
            ret = handle_check_date(input_data)
            assert ret == output_data

# def get_data_in_deep_dict(search_key, _dict={}):
# def validation_file_open_date(record):
def test_validation_file_open_date(app, test_records):
    for t in test_records:
        filepath = t.get("input")
        result = t.get("output")
        with open(filepath, encoding="utf-8") as f:
            ret = json.load(f)
        with app.app_context():
            assert validation_file_open_date(ret) == result


# def validation_date_property(date_str):

def test_validation_date_property():
    # with pytest.raises(Exception):
    assert validation_date_property("2022")==True
    assert validation_date_property("2022-03")==True
    assert validation_date_property("2022-1")==False
    assert validation_date_property("2022-1-1")==False
    assert validation_date_property("2022-2-31")==False
    assert validation_date_property("2022-12-01")==True
    assert validation_date_property("2022-02-31")==False
    assert validation_date_property("2022-12-0110")==False
    assert validation_date_property("hogehoge")==False

# def get_list_key_of_iso_date(schemaform):
def test_get_list_key_of_iso_date():
    form = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type", "form00.json"
    )
    result = [
        "item_1617186660861.subitem_1522300722591",
        "item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
        "item_1617187136212.subitem_1551256096004",
        "item_1617605131499.fileDate.fileDateValue",
    ]
    with open(form, encoding="utf-8") as f:
        df = json.load(f)
    assert get_list_key_of_iso_date(df) == result


# def get_current_language():
# def get_change_identifier_mode_content():
# def get_root_item_option(item_id, item, sub_form={"title_i18n": {}}):
# def get_sub_item_option(key, schemaform):
# def check_sub_item_is_system(key, schemaform):
# def get_lifetime():
# def get_system_data_uri(key_type, key):

def test_get_system_data_uri():
    data = [{"resource_type":RESOURCE_TYPE_URI}, {"version_type": VERSION_TYPE_URI}, {"access_right":ACCESS_RIGHT_TYPE_URI}]
    for t in data:
        for key_type in t.keys():
            val = t.get(key_type)
            for key in val.keys():
                url = val.get(key)
                assert get_system_data_uri(key_type,key)==url

# def handle_fill_system_item(list_record):

def test_handle_fill_system_item(app,test_list_records):

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
    with open(filepath,encoding="utf-8") as f:
        item_map = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_type_mapping.json")
    with open(filepath,encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    with patch("weko_records.serializers.utils.get_mapping",return_value=item_map):
        with patch("weko_records.api.Mapping.get_record",return_value=item_type_mapping):

            filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records/list_records_fill_system.json")
            with open(filepath,encoding="utf-8") as f:
                list_record = json.load(f)

            items = []
            items_result = []

            for a in VERSION_TYPE_URI:
                item = copy.deepcopy(list_record[0])
                item['metadata']['item_1617265215918']['subitem_1522305645492']=a
                item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI[a]
                item['metadata']['item_1617186476635']['subitem_1522299639480']="open access"
                item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI["open access"]
                item['metadata']['item_1617258105262']['resourcetype']="conference paper"
                item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI["conference paper"]
                items_result.append(item)
                item2 = copy.deepcopy(item)
                item2['metadata']['item_1617265215918']['subitem_1522305645492']=a
                item2['metadata']['item_1617265215918']['subitem_1600292170262']=""
                items.append(item2)

            for a in ACCESS_RIGHT_TYPE_URI:
                item = copy.deepcopy(list_record[0])
                item['metadata']['item_1617265215918']['subitem_1522305645492']="VoR"
                item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI["VoR"]
                item['metadata']['item_1617186476635']['subitem_1522299639480']=a
                item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI[a]
                item['metadata']['item_1617258105262']['resourcetype']="conference paper"
                item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI["conference paper"]
                items_result.append(item)
                item2 = copy.deepcopy(item)
                item2['metadata']['item_1617186476635']['subitem_1522299639480']=a
                item2['metadata']['item_1617186476635']['subitem_1600958577026']=""
                items.append(item2)

            for a in RESOURCE_TYPE_URI:
                item = copy.deepcopy(list_record[0])
                item['metadata']['item_1617265215918']['subitem_1522305645492']="VoR"
                item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI["VoR"]
                item['metadata']['item_1617186476635']['subitem_1522299639480']="open access"
                item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI["open access"]
                item['metadata']['item_1617258105262']['resourcetype']= a
                item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI[a]
                items_result.append(item)
                item2 = copy.deepcopy(item)
                item2['metadata']['item_1617258105262']['resourcetype']=a
                item2['metadata']['item_1617258105262']['resourceuri']=""
                items.append(item2)

            # with open("items.json","w") as f:
            #     json.dump(items,f)

            # with open("items_result.json","w") as f:
            #     json.dump(items_result,f)


            # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items.json")
            # with open(filepath,encoding="utf-8") as f:
            #     items = json.load(f)

            # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items_result.json")
            # with open(filepath,encoding="utf-8") as f:
            #     items_result = json.load(f)

            with app.test_request_context():
                ctx = _request_ctx_stack.top
                if ctx is not None and hasattr(ctx, 'babel_locale'):
                    with setattr(ctx, 'babel_locale', 'en'):
                        handle_fill_system_item(items)
                        assert len(items)==len(items_result)
                        assert items==items_result




# def get_thumbnail_key(item_type_id=0):
# def handle_check_thumbnail_file_type(thumbnail_paths):
# def handle_check_metadata_not_existed(str_keys, item_type_id=0):


@pytest.mark.parametrize(
    "items,root_id,root_name,form,ids,names",[
        pytest.param({'interim': {'type': 'string'}},'.metadata.item_1657196790737[0]','text[0]',[{'key': 'item_1657196790737[].interim', 'type': 'text', 'notitle': True}],['.metadata.item_1657196790737[0].interim'],['text[0].None']),
        pytest.param({'interim': {'enum': [None, 'op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'list', 'title_i18n': {'en': '', 'ja': ''}}},
        '.metadata.item_1657204077414[0]',
        'list[0]',[{'key': 'item_1657204077414[].interim', 'type': 'select', 'title': 'list', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
        ,['.metadata.item_1657204026946.interim[0]'],['check.check[0]']),
        pytest.param({'interim': {'enum': [None, 'op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'list', 'format': 'select'}},
'.metadata.item_1657204070640','list',[{'key': 'item_1657204070640.interim', 'type': 'select', 'title': 'list', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204036771[0].interim[0]'],['checjk[0].checjk[0]']),
pytest.param({'interim': {'type': 'array', 'items': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': 'string'}, 'title': 'check', 'format': 'checkboxes', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204026946','check',[{'key': 'item_1657204026946.interim', 'type': 'template', 'title': 'check', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}, 'templateUrl': '/static/templates/weko_deposit/checkboxes.html'}]
,['.metadata.item_1657204043063.interim'],['rad.rad']),
pytest.param({'interim': {'type': 'array', 'items': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': 'string'}, 'title': 'checjk', 'format': 'checkboxes', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204036771[0]','check[0]',[{'key': 'item_1657204036771[].interim', 'type': 'template', 'title': 'checjk', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}, 'templateUrl': '/static/templates/weko_deposit/checkboxes.html'}]
,['.metadata.item_1657204049138[0].interim'],['rd[0].rd']),
pytest.param({'interim': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'rad', 'format': 'radios'}},
'.metadata.item_1657204043063',
'rad',[{'key': 'item_1657204043063.interim', 'type': 'radios', 'title': 'rad', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204070640.interim'],['list.list']),
pytest.param({'interim': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'rd', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204049138[0]','rd[0]',[{'key': 'item_1657204049138[].interim', 'type': 'radios', 'title': 'rd', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204077414[0].interim'],['list[0].list']
)
]
)
def test_handle_get_all_sub_id_and_name(app,items,root_id,root_name,form,ids,names):
    with app.app_context():
        assert ids,names == handle_get_all_sub_id_and_name(items,root_id,root_name,form)

# def handle_get_all_id_in_item_type(item_type_id):
# def handle_check_consistence_with_mapping(mapping_ids, keys):
# def handle_check_duplication_item_id(ids: list):
# def export_all(root_url):
# def delete_exported(uri, cache_key):
# def cancel_export_all():
# def get_export_status():
# def handle_check_item_is_locked(item):
# def handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata):
# def check_index_access_permissions(func):
# def handle_check_file_metadata(list_record, data_path):
# def handle_check_file_path(
# def handle_check_file_content(record, data_path):
# def handle_check_thumbnail(record, data_path):
# def get_key_by_property(record, item_map, item_property):
# def get_data_by_property(item_metadata, item_map, mapping_key):
# def get_filenames_from_metadata(metadata):
# def handle_check_filename_consistence(file_paths, meta_filenames):

def test_DefaultOrderDict_deepcopy():
    import copy

    data={
        "key0":"value0",
        "key1":"value1",
        "key2":{
            "key2.0":"value2.0",
            "key2.1":"value2.1"
            }
        }
    dict1 = defaultify(data)
    dict2 = copy.deepcopy(dict1)

    for i, d in enumerate(dict2):
        if i in [0, 1] :
            assert d == "key" + str(i)
            assert dict2[d] == "value" + str(i)
        else:
            assert d == "key" + str(i)
            assert isinstance(dict2[d], DefaultOrderedDict)
            for s, dd in enumerate(dict2[d]):
                assert dd == "key{}.{}".format(i,s)
                assert dict2[d][dd] == "value{}.{}".format(i,s)
