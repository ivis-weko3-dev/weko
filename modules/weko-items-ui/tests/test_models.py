import io
import uuid
from datetime import datetime
from unittest import mock  # python3
#from unittest.mock import MagicMock

import mock  # python2, after pip install mock
import pytest
from flask import Flask, json, jsonify, session, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_login import current_user
from flask_security import login_user
from flask_security.utils import login_user
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from mock import patch

from weko_items_ui.models import CRISLinkageResult, LinkageItems
from weko_deposit.pidstore import weko_deposit_minter
from weko_records.models import ItemMetadata

record_uuid = uuid.uuid4()
record_uuid_2 = uuid.uuid4()
record_uuid_3 = uuid.uuid4()
record_uuid_4 = uuid.uuid4()
record_uuid_5 = uuid.uuid4()
data = {"recid":1}
data_2 = {"recid":2}
data_4 = {"recid":4}

cris_linkage_result = CRISLinkageResult(
    recid = 1,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid,
    succeed = False,
    failed_log = "failed_log"
)

cris_linkage_result_2 = CRISLinkageResult(
    recid = 2,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid_2,
    succeed = False,
    failed_log = "failed_log"
)

cris_linkage_result_4 = CRISLinkageResult(
    recid = 4,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid_4,
    succeed = False,
    failed_log = "failed_log"
)

item_metadata = ItemMetadata(
    id = record_uuid,
    item_type_id = 1,
    json = {}
)

item_metadata_2 = ItemMetadata(
    id = record_uuid_2,
    item_type_id = 1,
    json = {}
)

item_metadata_3 = ItemMetadata(
    id = record_uuid_3,
    item_type_id = 1,
    json = {}
)

item_metadata_4 = ItemMetadata(
    id = record_uuid_4,
    item_type_id = 1,
    json = {}
)

item_metadata_5 = ItemMetadata(
    id = record_uuid_5,
    item_type_id = 1,
    json = {}
)

#class CRISLinkageResult(db.Model, Timestamp):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

class TestCRISLinkageResult:

    # def get_last(self ,recid ,cris_institution):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_get_last -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_get_last(self, app, db):
        weko_deposit_minter(record_uuid, data, 1)
        db.session.add(item_metadata)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result)
        db.session.commit()

        result = CRISLinkageResult().get_last(recid=100, cris_institution="researchmap")
        assert result == None

    # def register_linkage_result(self ,recid ,cris_institution ,result ,item_uuid ,failed_log):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_register_linkage_result -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_register_linkage_result(self,app, db):
        weko_deposit_minter(record_uuid_2, data_2, 2)
        weko_deposit_minter(record_uuid_3, data, 100)
        db.session.add(item_metadata_2)
        db.session.add(item_metadata_3)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result_2)
        db.session.commit()

        result = CRISLinkageResult().register_linkage_result(recid=2, cris_institution="researchmap", result=True, item_uuid=record_uuid_2, failed_log="")
        assert result == True

        result = CRISLinkageResult().register_linkage_result(recid=100, cris_institution="researchmap", result=False, item_uuid=record_uuid_3, failed_log="")
        assert result == True


    # def set_running(self, item_uuid ,cris_institution):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_set_running -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_set_running(self,app,db):
        weko_deposit_minter(record_uuid_4, data_4, 4)
        weko_deposit_minter(record_uuid_5, data, 100)
        db.session.add(item_metadata_4)
        db.session.add(item_metadata_5)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result_4)
        db.session.commit()

        CRISLinkageResult().set_running(record_uuid_4, "researchmap")
        result = CRISLinkageResult().get_last(4, "researchmap")
        assert result.last_linked_item == record_uuid_4

        CRISLinkageResult().set_running(record_uuid_5, "researchmap")
        result = CRISLinkageResult().get_last(100, "researchmap")
        assert result.last_linked_item == record_uuid_5

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
class TestLinkageItems:
    
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems::test_get_by_item_id -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_get_by_item_id(self, app, db):
        # Create a LinkageItems instance and add it to the database
        linkage_item_1 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            status=LinkageItems.Status.REGISTERED
        )
        linkage_item_2 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_2",
            external_system=LinkageItems.ExternalSystem.RM,
            status=LinkageItems.Status.DELETED
        )
        linkage_item_3 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_3",
            external_system="other_system",
            status=LinkageItems.Status.REGISTERED
        )
        db.session.add(linkage_item_1)
        db.session.add(linkage_item_2)
        db.session.add(linkage_item_3)
        db.session.commit()

        result = LinkageItems.get_by_item_id(record_uuid, LinkageItems.ExternalSystem.RM, status=LinkageItems.Status.REGISTERED)
        assert result == [linkage_item_1]

        result = LinkageItems.get_by_item_id(record_uuid, LinkageItems.ExternalSystem.RM)
        assert result == [linkage_item_1, linkage_item_2]

    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems::test_get_by_external_item_id -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_get_by_external_item_id(self, app, db):
        # Create a LinkageItems instance and add it to the database
        linkage_item_1 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            status=LinkageItems.Status.REGISTERED
        )
        linkage_item_2 = LinkageItems(
            item_id=record_uuid_2,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            status=LinkageItems.Status.DELETED
        )
        linkage_item_3 = LinkageItems(
            item_id=record_uuid_3,
            external_item_id="external_id_2",
            external_system="other_system",
            status=LinkageItems.Status.REGISTERED
        )
        db.session.add(linkage_item_1)
        db.session.add(linkage_item_2)
        db.session.add(linkage_item_3)
        db.session.commit()

        result = LinkageItems.get_by_external_item_id("external_id_1", LinkageItems.ExternalSystem.RM, status=LinkageItems.Status.REGISTERED)
        assert result == [linkage_item_1]

        result = LinkageItems.get_by_external_item_id("external_id_1", LinkageItems.ExternalSystem.RM)
        assert len(result) == 2
        assert {linkage_item.item_id for linkage_item in result} == {record_uuid, record_uuid_2}

    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems::test_get_items_by_permalink_itemid -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_get_items_by_permalink_itemid(self, app, db):
        # Create a LinkageItems instance and add it to the database
        linkage_item_1 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            permalink="permalink_1",
            status=LinkageItems.Status.REGISTERED
        )
        linkage_item_2 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_2",
            external_system=LinkageItems.ExternalSystem.RM,
            permalink="permalink_2",
            status=LinkageItems.Status.DELETED
        )
        linkage_item_3 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_3",
            external_system="other_system",
            permalink="permalink_3",
            status=LinkageItems.Status.REGISTERED
        )
        linkage_item_4 = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_4",
            external_system=LinkageItems.ExternalSystem.RM,
            permalink="permalink_4",
            status=LinkageItems.Status.REGISTERED
        )
        db.session.add(linkage_item_1)
        db.session.add(linkage_item_2)
        db.session.add(linkage_item_3)
        db.session.add(linkage_item_4)
        db.session.commit()

        permalinks = ["permalink_1", "permalink_2", "permalink_3"]
        result = LinkageItems.get_items_by_permalink_itemid(record_uuid, permalinks, LinkageItems.ExternalSystem.RM)
        assert len(result) == 1
        assert result[0].permalink == "permalink_1"
        assert result[0].external_item_id == "external_id_1"

        result = LinkageItems.get_items_by_permalink_itemid(record_uuid, permalinks, LinkageItems.ExternalSystem.RM, status=LinkageItems.Status.DELETED)
        assert len(result) == 1
        assert result[0].permalink == "permalink_2"
        assert result[0].external_item_id == "external_id_2"

    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems::test_create -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_create(self, app, db):
        # Create a new linkage item
        new_linkage_item = LinkageItems.create(
            item_id=record_uuid,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            permalink="permalink_1",
            status=LinkageItems.Status.DELETED
        )

        # Verify that the linkage item was created and added to the database
        assert new_linkage_item.item_id == record_uuid
        assert new_linkage_item.external_item_id == "external_id_1"
        assert new_linkage_item.external_system == LinkageItems.ExternalSystem.RM
        assert new_linkage_item.permalink == "permalink_1"
        assert new_linkage_item.status == LinkageItems.Status.DELETED

        # Verify that the linkage item exists in the database
        result = LinkageItems.query.filter_by(item_id=record_uuid, external_item_id="external_id_1").first()
        assert result is not None

        # Create another linkage item without specifying permalink and status
        new_linkage_item_2 = LinkageItems.create(
            item_id=record_uuid,
            external_item_id="external_id_2",
            external_system=LinkageItems.ExternalSystem.RM
        )

        # Verify that the second linkage item was created with default values for permalink and status
        assert new_linkage_item_2.item_id == record_uuid
        assert new_linkage_item_2.external_item_id == "external_id_2"
        assert new_linkage_item_2.external_system == LinkageItems.ExternalSystem.RM
        assert new_linkage_item_2.permalink is None
        assert new_linkage_item_2.status == LinkageItems.Status.REGISTERED

        # Verify that the second linkage item exists in the database
        result_2 = LinkageItems.query.filter_by(item_id=record_uuid, external_item_id="external_id_2").first()
        assert result_2 is not None

    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestLinkageItems::test_update_status -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_update_status(self, app, db):
        # Create a LinkageItems instance and add it to the database
        linkage_item = LinkageItems(
            item_id=record_uuid,
            external_item_id="external_id_1",
            external_system=LinkageItems.ExternalSystem.RM,
            status=LinkageItems.Status.REGISTERED
        )
        db.session.add(linkage_item)
        db.session.commit()

        # Update the status of the linkage item
        linkage_item.update_status(LinkageItems.Status.DELETED)

        # Verify that the status was updated in the database
        result = LinkageItems.query.filter_by(item_id=record_uuid, external_item_id="external_id_1").first()
        assert result.status == LinkageItems.Status.DELETED