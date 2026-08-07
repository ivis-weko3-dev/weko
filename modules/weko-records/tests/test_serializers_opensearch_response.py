import pytest
from tests.helpers import json_data
from unittest.mock import patch

from invenio_records_rest.schemas.json import RecordSchemaJSONV1
from invenio_pidstore.models import PersistentIdentifier
from weko_records.serializers.opensearchresponse import (
    oepnsearch_responsify,
    add_link_header,
    custom_output_open_search
)
from weko_records.serializers.opensearchserializer import OpenSearchSerializer

# def oepnsearch_responsify(serializer):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_opensearch_response.py::test_oepnsearch_responsify -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[("data/record_hit/record_hit1.json")]
@pytest.mark.parametrize("hit", params)
def test_oepnsearch_responsify(app, db, hit):
    def fetcher(obj_uuid, data):
        assert obj_uuid=="1"
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    _search_result = {'hits': {'total': {'value':1}, 'hits': [json_data(hit)]}}
    opensearch_v1 = OpenSearchSerializer(RecordSchemaJSONV1)
    opensearch = oepnsearch_responsify(opensearch_v1)
    with app.test_request_context():
        with patch("weko_records_ui.utils.hide_by_email",return_value = {'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-10-26'}, 'path': [1], 'control_number': '1', 'item_type_id': '1', 'item_test1_1': {'attribute_name': 'Test Item1-1', 'attribute_value_mlt': [{'test_item_lang1': 'en', 'test_value1': 'this is test item1-1'}]}, 'item_test1_2': {'attribute_name': 'Test Item1-2', 'attribute_value_mlt': [{'test_item_lang1': 'en'}]}, 'item_test1_3': {'attribute_name': 'Test Item1-3', 'attribute_value_mlt': [{'test_value1': 'this is test item1-3'}]}, 'item_test1_4': {'attrinute_name': 'Test Item1-4', 'attribute_value_mlt': [{'test_value1': ''}]}, 'item_test1_5': {'attribute_name': 'Test Item1-5', 'attribute_value_mlt': [{'test_item_lang1': 'en', 'test_value1': ''}]}, 'item_test2_title': {'attribute_name': 'Title', 'attribute_value_mlt': [{'test_title': 'this is test item title', 'test_title_lang': 'en'}]}, 'item_test3_file': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'label': 'open and exist label'}, 'accessrole': 'open_restricted', 'format': 'application/pdf'}, {'url': {'test': 'open and not exist label'}, 'accessrole': 'open_restricted', 'format': 'application/pdf'}, {'url': {'url': 'https://localhostnot label, but version_id'}, 'version_id': '1.0', 'filename': 'test.txt', 'format': 'application/pdf'}, {'url': {'label': 'not file url'}, 'version_id': '1.0', 'filename': 'test_not_extension', 'format': 'application/pdf'}, {'url': {'test': 'not open and not label'}, 'format': 'application/pdf'}]}, 'item_resource_type': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'test type', 'resourceuri': 'http://nii.co.jp/resource_type/01'}]}, 'item_description': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description_value': 'test description', 'subitem_description_lang': 'en'}]}, 'item_date': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_date_value': '2021-10-26', 'subitem_date_type': 'Available'}, {'subitem_date_value': '2021-10-26', 'subitem_date_type': 'Issued'}]}, 'item_publisher': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_publisher': 'takeshi', 'subitem_publisherLang': 'en'}]}, 'item_source_ids': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_source_id': '123', 'subitem_source_id_type': 'ISSN'}]}, 'item_version': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_version': '1.0.0'}]}, 'item_test4_thumbnail': {'attribute_name': 'thumbnail', 'attribute_type': 'thumbnail', 'attribute_value_mlt': [{'subitem_thumbnail': []}]}, 'item_test4_2_thumbnail': {'attribute_name': 'thumbnail2', 'attribute_type': 'thumbnail', 'attribute_value_mlt': [{'subitem_thumbnail': [{'thumbnail_label': 'サムネイルラベル'}]}]}, 'item_test5_creator': {'attribute_name': 'creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorNames': [{'creatorName': 'takeshi', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': None, 'familyNameLang': 'en'}, {'familyName': 'takesi family'}], 'givenNames': [{'givenName': 'takesi given', 'givenNameLang': 'en'}], 'nameIdentifierURI': [{'nameIdentifierURI': ''}]}]}, 'item_test6_bibliographic': {'attribute_value_mlt': [{'bibliographic_titles': [{'bibliographic_titleLang': 'en', 'bibliographic_title': 'this is test bibliographic title'}], 'bibliographic_volume': '10', 'bibliographic_issue': '7', 'bibliographic_pageStart': '1', 'bibliographic_pageEnd': '11'}]}, 'item_test8_not_mlt': {'attribute_type': 'test'}, 'item_test9': {'attribute_value_mlt': {'item_test9_dict': {'item_test9_dict_value': 'value9_dict'}, 'item_test9_list': [['item_test9_list_value']]}}, 'item_test11': {'attribute_value_mlt': 'str_attribute_value_mlt'}, 'item_test12.indot_item': {'attribute_value_mlt': {'value': 'value'}}}),\
             patch("weko_deposit.api.WekoRecord.get_record_by_pid",return_value={}):
             result = opensearch(fetcher, _search_result)
             assert result.status_code==200

# def add_link_header(response, links):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_opensearch_response.py::test_add_link_header -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_add_link_header(app, db):
    _response = app.response_class()
    _links = {'key1': 'value1', 'key2': 'value2'}

    add_link_header(_response, _links)
    assert _response.headers[1]==('Link', '<value1>; rel="key1", <value2>; rel="key2"')

# def custom_output_open_search(record_lst: list):
