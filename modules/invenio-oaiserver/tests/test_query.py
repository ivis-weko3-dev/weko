import pytest
from mock import patch
import uuid
from flask import current_app
from datetime import datetime
from opensearch_dsl import query as dsl_query

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_search import current_search_client
# from invenio_search.engine import dsl
from weko_index_tree.models import Index
from invenio_oaiserver.query import query_string_parser
from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.query import (
    query_string_parser,
    get_records
)
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

#def query_string_parser(search_pattern):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_query_string_parser -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_query_string_parser(es_app):
    # current_oaiserver not have query_parse, config is str
    result = query_string_parser("test_path")
    assert type(result) == dsl_query.QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string": {"query": "test_path", "fields": ["title_statement"]}}

    # current_oaiserver not have query_parse, config is not str
    current_app.config.update(OAISERVER_QUERY_PARSER=dsl_query.Q)
    delattr(current_oaiserver, "query_parser")
    result = query_string_parser("test_path")
    assert type(result) == dsl_query.QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string": {"query": "test_path", "fields": ["title_statement"]}}

    # current_oaiserver have query_parse
    result = query_string_parser("test_path")
    assert type(result) == dsl_query.QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string": {"query": "test_path", "fields": ["title_statement"]}}

#class OAIServerSearch(RecordsSearch):

#def get_records(**kwargs):

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_get_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_records(es_app, db, mock_execute):
    indexes = list()
    for i in range(10):
        indexes.append(
            Index(
                parent=0,
                position=i,
                index_name_english="test_index{}".format(i),
                index_link_name_english="test_index_link{}".format(i),
                harvest_public_state=True,
                public_state=True,
                public_date=datetime(2100, 1, 1),
                browsing_role="3,-99"
            )
        )
    rec_uuid1 = uuid.uuid4()
    identifier1 = PersistentIdentifier.create('doi', "https://doi.org/00001", object_type='rec', object_uuid=rec_uuid1, status=PIDStatus.REGISTERED)

    rec_data1 = {"title": ["test_item1"], "path": [1], "_oai": {"id": "oai:test:00001", "sets": []}, "relation_version_is_last": "true", "control_number": "1"}
    rec1 = RecordMetadata(id=rec_uuid1, json=rec_data1)
    rec_uuid2 = uuid.uuid4()
    rec_data2 = {"title": ["test_item2"], "path": [1000], "_oai": {"id": "oai:test:00002", "sets": ["12345"]}, "relation_version_is_last": "true", "control_number": "2"}
    identifier2 = PersistentIdentifier.create('doi', "https://doi.org/00002", object_type='rec', object_uuid=rec_uuid2, status=PIDStatus.REGISTERED)
    rec2 = RecordMetadata(id=rec_uuid2, json=rec_data2)
    db.session.add_all(indexes)
    db.session.add(rec1)
    db.session.add(rec2)

    db.session.commit()

    es_info = dict(id=str(rec_uuid1),
                   index=current_app.config['INDEXER_DEFAULT_INDEX'])
    body = dict(version=1,
                version_type="external_gte",
                body=rec_data1)
    current_search_client.index(**{**es_info, **body})
    es_info = dict(id=str(rec_uuid2),
                   index=current_app.config['INDEXER_DEFAULT_INDEX'])
    body = dict(version=1,
                version_type='external_gte',
                body=rec_data2)
    current_search_client.index(**{**es_info, **body})

    # not scroll_id, ":" not in set
    data = {
        "set": "12345"
    }
    result = get_records(**data)
    assert result

    # not scroll_id, ":" in set
    data = {
        "set": "12345:6789"
    }
    result = get_records(**data)
    assert result

    # not scroll_id, "set" not in data, exist "from_", "until" in data
    data = {
        "from_": "2022-01-01",
        "until": "2023-01-01"
    }
    result = get_records(**data)
    assert result

    # in scroll_id
    data = {
        "resumptionToken": {"page": 1, "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAVfgWYmVhQ3BkbEdSSm0wS3pTaEdQeHQ1QQ=="}
    }
    dummy_data = {
        "hits": {
            "total": 1,
            "hits": [
                {
                    "_id": str(rec_uuid1),
                    "_source": rec_data1
                }
            ]
        }
    }
    with patch("invenio_oaiserver.query.current_search_client.scroll", return_value=dummy_data):
        result = get_records(**data)
        assert result