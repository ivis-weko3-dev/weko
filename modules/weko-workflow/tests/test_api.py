# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, MagicMock, call, patch
import unittest
from unittest.mock import MagicMock, patch
import pytest
import math
from flask import current_app, session
from flask_login.utils import login_user, logout_user

from marshmallow import ValidationError
from requests import HTTPError
from sqlalchemy import and_, or_, not_
from sqlalchemy.exc import SQLAlchemyError

from weko_notifications.notifications import Notification
from weko_records.api import ItemsMetadata
from weko_workflow.api import Flow, GetCommunity, WorkActivity, WorkFlow, UpdateItem
from weko_workflow.models import Activity, ActivityHistory, ActivityAction, FlowAction, FlowActionRole
from weko_schema_ui.models import PublishStatus

from invenio_accounts.testutils import login_user_via_session
from invenio_accounts.models import Role, User
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from weko_deposit.api import WekoIndexer
from weko_notifications.notifications import Notification
from weko_records.api import ItemsMetadata
from weko_records.models import RequestMailList as _RequestMailList
from weko_records.models import ItemApplication as _ItemApplication
from weko_records_ui.models import FileSecretDownload
from weko_schema_ui.models import PublishStatus


from weko_workflow.api import (
    Flow, GetCommunity, UpdateItem, WorkActivity, WorkFlow
)
from weko_workflow.models import Action as _Action
from weko_workflow.models import Activity as _Activity
from weko_workflow.models import ActivityAction
from weko_workflow.models import FlowAction as _FlowAction
from weko_workflow.models import FlowActionRole as _FlowActionRole
from weko_workflow.models import FlowDefine as _Flow
from weko_workflow.models import WorkFlow as _WorkFlow
from weko_workflow.models import Activity, ActivityHistory, ActivityAction, FlowAction, FlowActionRole
from weko_workflow.models import ActionStatusPolicy, Activity, ActivityAction, FlowActionRole, ActivityRequestMail, ActivityItemApplication
from .helpers_proxy import (
    UNSET, build_func_query, build_proxy_env, build_tab_query, compile_sql, create_group_roles,
    create_proxy_activity, create_role, create_role_with_id_prefix, disable_map,
    enable_map, list_activity_ids, rid, set_proxy_posting, set_raw_json,
    add_flow_action_role,
)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_create_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_create_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()

        flow = _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'create_flow_test_root'
        assert flow.repository_id == 'Root Index'

        flow = _flow.create_flow({'flow_name': 'create_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'create_flow_test_1'
        assert flow.repository_id == 'comm01'

        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.create_flow({'flow_name': '', 'repository_id': 'com1'})

        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.create_flow({'flow_name': 'test_flow'})

        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.create_flow({'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_upt_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_upt_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})

        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'Root Index'

        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'comm01'

        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': '', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': ''})

        flow1 = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'comm01'})
        db.session.add(flow)
        db.session.add(flow1)
        db.session.commit()
        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_get_flow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_get_flow_list(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'get_flow_list_test', 'repository_id': 'Root Index'})
        db.session.add(flow)
        db.session.commit()

        login_user(users[2]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow

        login_user(users[3]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 0

        flow_com = _flow.create_flow({'flow_name': 'flow_comm01', 'repository_id': 'comm01'})
        db.session.add(flow_com)
        db.session.commit()

        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow_com


class TestFlow:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_action(self,app, client, users, db, action_data):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test', 'repository_id': 'Root Index'})
            assert flow.flow_name == 'create_flow_test'

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                "action":"ADD"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            flow_id = flow.flow_id
            flow = _flow.get_flow_detail(flow_id)
            assert flow.flow_name == 'create_flow_test'

            res = _flow.del_flow(flow_id)
            assert res['code'] == 500

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_upt_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_item_registrant', [
        (-2, True, None, True, True),
        (-2, False, None, False, True),
        (2, True, 2, True, False),
        (2, False, 2, False, False),
    ])
    def test_upt_flow_action(self, app, client, users, db, action_data, user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_item_registrant):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test', 'repository_id': 'Root Index'})

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            actual =  db.session.query(FlowActionRole).get(3)
            if expected_action_user is None:
                assert actual.action_user is None
            else:
                assert actual.action_user == expected_action_user
            assert actual.specify_property is None
            assert actual.action_user_exclude == expected_action_user_exclude
            assert actual.action_item_registrant == expected_action_item_registrant
            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"parentkey.subitem_restricted_access_guarantor_mail_address",
                    "user_deny": True,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":db.session.query(FlowActionRole).get(2).flow_action_id,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"UPDATE"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":actual.flow_action_id,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"DEL"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)
            actual =  db.session.query(FlowActionRole).get(3)
            update_actual = db.session.query(FlowActionRole).get(5)
            assert actual == None
            assert update_actual.action_user_exclude == True
            assert update_actual.specify_property == "parentkey.subitem_restricted_access_guarantor_mail_address"



    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_upt_flow_action_for_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_request_mail', [
        (-3, True, None, True, True),
        (-3, False, None, False, True),
    ])
    def test_upt_flow_action_for_request_mail(self, app, client, users, db, action_data, user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_request_mail):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test', 'repository_id': 'Root Index'})

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"4",
                    "name":"Request Mail",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":4,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            actual =  db.session.query(FlowActionRole).get(4)
            if expected_action_user is None:
                assert actual.action_user is None
            else:
                assert actual.action_user == expected_action_user
            assert actual.specify_property is None
            assert actual.action_user_exclude == expected_action_user_exclude
            assert actual.action_request_mail == expected_action_request_mail

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_get_flow_action_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_flow_action_list(self, db,workflow):
        res = Flow().get_flow_action_list(workflow["flow"].id)
        assert len(res) == 7
        assert res[0].action_order == 1
        assert res[1].action_order == 2
        assert res[2].action_order == 3
        assert res[3].action_order == 4
        assert res[4].action_order == 5
        assert res[5].action_order == 6
        assert res[6].action_order == 7


class TestWorkActivity:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_filter_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_filter_by_date(self,app, db):
        query = db.session.query()
        activity = WorkActivity()
        assert activity.filter_by_date('2022-01-01', '2022-01-02', query)


    # wait タブは、shared_user_ids を持つアクティビティを1件も返せない。
    # query_activities_by_tab_is_wait の条件が
    #   not_(temp_data #>> "{'metainfo', 'shared_user_ids'}" contains ...)
    # を AND で使っているが、この JSON パスのリテラルは PostgreSQL の
    # text[] としては要素が 'metainfo' (引用符込み) になるため常に NULL を返す。
    # NULL を not_ しても NULL なので、その AND 枝は決して真にならず、
    # 残るのは shared_user_ids IS NULL の枝だけ。
    # 詳細は issues.md A-10。
    WAIT_TAB_XFAIL = pytest.mark.xfail(
        raises=AssertionError,
        reason="wait タブの JSON パスリテラルが不正で、shared_user_ids を"
               "持つアクティビティが決して返らない (issues.md A-10)",
    )

    conditions = [
        {
            'tab': ['todo'],
            'pagestodo': ['1'],
            'sizetodo': ['10']
        },
        pytest.param({
            'tab': ['wait'],
            'pageswait': ['1'],
            'sizewait': ['10']
        }, marks=WAIT_TAB_XFAIL),
        {
            'tab': ['all'],
            'pagesall': ['1'],
            'sizeall': ['10']
        },
        {
            'tab': ['todo']
        },
        pytest.param({
            'tab': ['wait']
        }, marks=WAIT_TAB_XFAIL),
        {
            'tab': ['all']
        }
    ]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('conditions', conditions)
    def test_get_activity_list(self, app, users, db_register_activity, conditions, client):
        # test preparation
        activity = WorkActivity()

        # contributor
        with app.test_request_context():
            login_user(users[0]['obj'])
            activities, max_page, size, page, name_param, count = \
                activity.get_activity_list(conditions, False)

            if conditions.get('tab')[0] == 'todo':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 1
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[0].activity_id
                assert activities[0].title == db_register_activity.get('activity')[0].title
            elif conditions.get('tab')[0] == 'wait':
                assert size == conditions.get('sizewait')[0] if conditions.get('sizewait') else '20'
                assert page == conditions.get('pageswait')[0] if conditions.get('pageswait') else '1'
                assert max_page == 1
                assert count == 1
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
                assert activities[0].title == db_register_activity.get('activity')[2].title
            elif conditions.get('tab')[0] == 'all':
                assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
                assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
                assert max_page == 1
                # contributor が login_user のアクティビティは
                # 'contributor-todo' と 'contributor-wait' の2件。
                # all タブはその両方を新しい順に返す。
                assert count == 2
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
                assert activities[0].title == db_register_activity.get('activity')[2].title
                assert activities[1].activity_id == db_register_activity.get('activity')[0].activity_id
                assert activities[1].title == db_register_activity.get('activity')[0].title
            else:
                assert False

        # sysadmin
        with app.test_request_context():
            login_user(users[2]['obj'])
            activities, max_page, size, page, name_param, count = \
                activity.get_activity_list(conditions, False)

            if conditions.get('tab')[0] == 'todo':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 3
                assert name_param == ''
                for i in range(0, 3):
                    assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
                for i in range(0, 3):
                    assert activities[i].title == db_register_activity.get('activity')[2-i].title
            elif conditions.get('tab')[0] == 'wait':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 1
                assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
                assert activities[0].title == db_register_activity.get('activity')[2].title
            elif conditions.get('tab')[0] == 'all':
                assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
                assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
                assert max_page == 1
                assert count == 3
                assert name_param == ''
                for i in range(0, 3):
                    assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
                for i in range(0, 3):
                    assert activities[i].title == db_register_activity.get('activity')[2-i].title
            else:
                assert False


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_all_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_all_activity_list(self,app, client, users, db_register_full_action):
        with app.test_request_context():
            login_user(users[2]["obj"])
            activity = WorkActivity()
            activities = activity.get_all_activity_list()
            assert len(activities) == 20


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_activity_index_search(self,app, db_register_full_action):
        activity = WorkActivity()
        with app.test_request_context():
            activity_detail, item, steps, action_id, cur_step, \
                temporary_comment, approval_record, step_item_login_url,\
                histories, res_check, pid, community_id, ctx = activity.get_activity_index_search("1")
            assert activity_detail.id == 1
            assert activity_detail.action_id == 1
            assert activity_detail.title == 'test'
            assert activity_detail.activity_id == '1'
            assert activity_detail.flow_id == 1
            assert activity_detail.workflow_id == 1
            assert activity_detail.action_order == 1


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_upt_activity_detail(self,app, db_register_full_action, db_records):
        activity = WorkActivity()
        db_activity = activity.upt_activity_detail(db_records[2][2].id)
        assert db_activity == None


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_corresponding_usage_activities(self,app, db_register_full_action):
        activity = WorkActivity()
        usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
        assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
        assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_check_community_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_community_permission(self,app,db_register_full_action):
        activity = WorkActivity()
        activities = db_register_full_action["activities"]
        not_itemid_act = activities[1]
        # not exist activity.item_id
        result = WorkActivity._check_community_permission(not_itemid_act, ["1"])

        assert result == True

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_query_check_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_query_check_path(self, db):
        index_list = ["1","2","3"]
        metadatas = [
            {"title":"not_exist_path"},
            {"title":"deny_path","path":["4","5","6"]},
            {"title":"allow_path","path":["3","4","5"]}]
        record_metadatas = []
        for metadata in metadatas:
            record_metadatas.append(
                RecordMetadata(json=metadata)
            )
        db.session.add_all(record_metadatas)
        db.session.commit()

        # Get metadata path that contain elements of index_list
        exist_query = WorkActivity._WorkActivity__query_check_path(index_list,is_within=True)
        result = db.session.query(RecordMetadata).filter(exist_query).all()
        assert len(result)==1
        assert result[0].json==metadatas[2]

        # Get metadata path that does not contain any index_list elements
        exist_query = WorkActivity._WorkActivity__query_check_path(index_list,is_within=False)
        result = db.session.query(RecordMetadata).filter(exist_query).all()
        assert len(result)==2
        assert result[0].json==metadatas[0]
        assert result[1].json==metadatas[1]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_community_user_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_community_user_ids(self, client, app, activity_acl_users):
        users = activity_acl_users["users"]
        # not login
        result = WorkActivity._WorkActivity__get_community_user_ids()
        assert result == []

        # no role
        with app.test_request_context():
            login_user(users[6])
            result = WorkActivity._WorkActivity__get_community_user_ids()
            assert result == []

        # no communities
        with app.test_request_context():
            login_user(users[4])
            result = WorkActivity._WorkActivity__get_community_user_ids()
            assert result == []

        # exist communities
        with app.test_request_context():
            login_user(users[3])
            result = WorkActivity._WorkActivity__get_community_user_ids()
            assert result == [3,4]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_list2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_activity_list2(self, app, client, activity_acl, activity_acl_users, db):
        # {user_id:{tab:[activity_id,...],...}}
        # all タブは wait タブのアクティビティも含む。期待値のほうが
        # wait の1件 (user 3 の 17、user 4 の 39) を落としていた。
        result = {
            1:{# sysadmin
                "todo":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 28, 27, 26, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 7, 6, 5, 2, 1],
                "wait":[],
                "all":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
            },
            3:{# test_role01_user
                "todo":[42, 38, 37, 34, 33, 32, 31, 27, 22, 21, 19, 18, 16, 14, 5],
                "wait":[17],
                "all":[42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 19, 18, 17, 16, 14, 5]
            },
            4:{# test_role01_comadmin
                "todo":[42, 41, 40, 38, 34, 32, 26, 23, 22, 18, 16, 14, 12, 11, 10, 7, 6, 5],
                "wait":[39],
                "all":[42, 41, 40, 39, 38, 34, 32, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
            },
            5:{# test_role02_user
                "todo":[40,35,19,15,10],
                "wait":[],
                "all":[40,35,19,15,10]
            },
        }

        size_list = [20, 50, 75]
        activity = WorkActivity()
        for user_id, tag_act in result.items():
            user = User.query.filter_by(id=user_id).one()
            with app.test_request_context():
                login_user(user)
                for tab, acts in tag_act.items():
                    for res_size in size_list:
                        num_page = math.ceil(len(acts)/res_size)
                        for res_page in range(num_page):
                            res_page = res_page + 1
                            conditions={"tab":[tab]}
                            if res_size != 20:
                                conditions["size{}".format(tab)]=[str(res_size)]
                            if res_page != 1:
                                conditions["pages{}".format(tab)]=[str(res_page)]
                            activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
                            assert [ac.id for ac in activities] == acts[res_size*(res_page-1):res_size*res_page]
                            assert max_page == num_page
                            assert size == str(res_size)
                            assert page == str(res_page)
                            assert count == len(acts)

                    num_page = math.ceil(len(acts)/20)
                    conditions = {"tab":[tab]}
                    # is_get_all = True
                    activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions,is_get_all=True)
                    assert [ac.id for ac in activities] == acts
                    assert max_page == num_page
                    assert size == '20'
                    assert page == '1'
                    assert count == len(acts)

                    # activitylog = True
                    activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions,activitylog=True)
                    assert [ac.id for ac in activities] == acts
                    assert max_page == math.ceil(len(acts)/100000)
                    assert size == 100000
                    assert page == 1
                    assert count == len(acts)

        # count = 0
        user = User.query.filter_by(id=7).one()
        with app.test_request_context():
            login_user(user)
            conditions={"tab":["todo"]}
            activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
            assert activities == []
            assert max_page == 0
            assert size == '20'
            assert page == '1'

        current_app.config['WEKO_ITEMS_UI_MULTIPLE_APPROVALS'] = False
        user = User.query.filter_by(id=7).one()
        with app.test_request_context():
            login_user(user)
            conditions={"tab":["todo"]}
            activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
            assert activities == []
            assert max_page == 0
            assert size == '20'
            assert page == '1'

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_usage_report_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_usage_report_activities(app, activity_usage_report):
        activity = WorkActivity()
        result = activity.get_usage_report_activities([])
        assert result == activity_usage_report

        result = activity.get_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report])
        assert result == activity_usage_report

        result = activity.get_usage_report_activities([], size=5, page=1)
        assert len(result) == 5
        assert result == activity_usage_report[:5]

        result = activity.get_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report], size=5, page=2)
        assert len(result) == 5
        assert result == activity_usage_report[5:10]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_count_all_usage_report_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_count_all_usage_report_activities(app, activity_usage_report):
        activity = WorkActivity()
        result = activity.count_all_usage_report_activities([])
        assert result == 10

        result = activity.count_all_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report[:5]])
        assert result == 5


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_count_waiting_approval_by_workflow_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_count_waiting_approval_by_workflow_id(app, db, db_register_full_action):
    activity = WorkActivity()
    assert activity.count_waiting_approval_by_workflow_id(1) == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_upt_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_upt_workflow(app, db, workflow, logging_client, users):
    with app.test_request_context():
        # System Administrator
        login_user(users[2]["obj"])
        w = workflow["workflow"]
        _workflow = WorkFlow()
        data = dict(flows_id=w.flows_id,
                    flows_name='test workflow01',
                    itemtype_id=1,
                    flow_id=1,
                    index_tree_id=None,
                    open_restricted=False,
                    location_id=None,
                    is_gakuninrdm=False,
                    repository_id='Root Index')

        res = _workflow.upt_workflow(data)
        for key in data:
            assert getattr(res, key) == data[key]

        # Repository Administrator
        login_user(users[1]["obj"])
        data = dict(flows_id=w.flows_id,
                    flows_name='test workflow01',
                    itemtype_id=1,
                    flow_id=1,
                    index_tree_id=None,
                    open_restricted=True,
                    location_id=None,
                    is_gakuninrdm=False,
                    repository_id='Root Index')
        res = _workflow.upt_workflow(data)
        data["open_restricted"] = False  # cannot update open_restricted
        for key in data:
            assert getattr(res, key) == data[key]

        res = _workflow.upt_workflow({'flows_id': uuid.uuid4()})
        assert res is None

        with pytest.raises(AssertionError):
            _workflow.upt_workflow(None)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_get_workflow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_get_workflow_list(app, db, workflow, users):
    w = workflow["workflow"]
    _workflow = WorkFlow()
    res = _workflow.get_workflow_list()
    assert len(res) == 1

    user = users[2]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1

    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 0

    w.repository_id = "comm01"
    db.session.commit()
    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_workflows_by_roles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_workflows_by_roles(app, mocker):
    role_1 = MagicMock(id=1, name='')
    role_2 = MagicMock(id=2, name='')
    role_3 = MagicMock(id=3, name='')

    mock_user = MagicMock()
    mock_user.roles = [role_1, role_2]
    mocker.patch("flask_login.utils._get_user", return_value=mock_user) # current_user_roles

    mock_query = mocker.patch("invenio_accounts.models.Role.query")
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = [role_1, role_3] # all roles

    mock_outerjoin = mock_query.outerjoin.return_value
    mock_filter1 = mock_outerjoin.filter.return_value
    mock_filter2 = mock_filter1.filter.return_value
    mock_filter2.all.return_value = [role_1] # list_hide

    wf = WorkFlow()
    wf1 = MagicMock(id=11, name='')

    # user_roles:[role_1] - list_hide:[role_1] = [] -> not show wf1
    workflows = wf.get_workflows_by_roles([wf1])
    assert workflows == []

    mock_filter2.all.return_value = [] # list_hide

    # user_roles:[role_1] - list_hide:[] = [role_1] -> show wf1
    workflows = wf.get_workflows_by_roles([wf1])
    assert workflows == [wf1]

    # argument is None
    workflows = wf.get_workflows_by_roles(None)
    assert workflows == []

    # user_roles is None
    mock_filter.all.return_value = None # role
    workflows = wf.get_workflows_by_roles([wf1])
    assert workflows == []


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_action(app, db):
    query = db.session.query(Activity)
    activity = WorkActivity()


    # case: empty action
    list_action = []
    assert activity._WorkActivity__filter_by_action(query, list_action) == query


    # case: single action, correct
    list_action = ['start']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([1])))

    list_action = ['end']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([2])))

    list_action = ['itemregistration']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([3])))

    list_action = ['approval']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([4])))

    list_action = ['itemlink']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([5])))

    list_action = ['oapolicyconfirmation']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([6])))

    list_action = ['identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([7])))


    # case: single action, incorrect
    list_action = ['invalid_action']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([])))


    # case: multiple actions, correct
    list_action = ['start', 'itemregistration', 'approval', 'identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([1, 3, 4, 7])))


    # case: multiple actions, incorrect
    list_action = ['invalid1', 'invalid2', 'invalid3']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([])))


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_index_search(app, db_register_full_action):
    activity = WorkActivity()
    with app.test_request_context():
        activity_detail, item, steps, action_id, cur_step, \
            temporary_comment, approval_record, step_item_login_url,\
            histories, res_check, pid, community_id, ctx = activity.get_activity_index_search('1')
        assert activity_detail.id == 1
        assert activity_detail.action_id == 1
        assert activity_detail.title == 'test'
        assert activity_detail.activity_id == '1'
        assert activity_detail.flow_id == 1
        assert activity_detail.workflow_id == 1
        assert activity_detail.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_upt_activity_detail(app, db_register_full_action,users, db_records):
    activity = WorkActivity()
    with app.test_request_context():
        login_user(users[0]["obj"])
        db_activity = activity.upt_activity_detail(db_records[2][2].id)
        assert db_activity.id == db_register_full_action.get('activities')[1].id
        assert db_activity.action_id == 2
        assert db_activity.title == 'test item1'
        assert db_activity.activity_id == '2'
        assert db_activity.flow_id == 1
        assert db_activity.workflow_id == 1
        assert db_activity.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_corresponding_usage_activities(app, db_register_full_action):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

from unittest.mock import call, patch, MagicMock

class MockRecord(dict):
    def commit(self):
        pass

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_publish -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_records_ui.models.FileSecretDownload')
@patch('weko_deposit.api.WekoIndexer')
@patch('weko_workflow.api.db.session.commit')
def test_publish(mock_db_commit, mock_WekoIndexer, mock_FileSecretDownload):
    def create_mock_record(publish_status, accessroles, filenames, recid='12345'):
        attribute_value_mlt = [{'accessrole': role, 'filename': filename} for role, filename in zip(accessroles, filenames)]
        record = MockRecord({
            'publish_status': publish_status,
            'recid': recid,
            'some_field': {
                'attribute_value_mlt': attribute_value_mlt
            }
        })
        record.commit = MagicMock()
        return record

    def assert_publish(record, status, reset_mock=True):
        update_item.publish(record, status)
        assert record['publish_status'] == status
        record.commit.assert_called_once()
        mock_db_commit.assert_called()
        mock_WekoIndexer.return_value.update_es_data.assert_called_with(record, update_revision=False, field='publish_status')
        if reset_mock:
            mock_FileSecretDownload.query.filter_by.return_value.all.reset_mock()

    # Mock record objects
    record1 = create_mock_record(None, [None], ['testfile.txt'])
    record2 = create_mock_record(PublishStatus.PRIVATE.value, ['open_date'], ['testfile.txt'])
    record3 = create_mock_record(PublishStatus.NEW.value, ['open_no'], ['testfile.txt'])
    record4 = create_mock_record(PublishStatus.DELETE.value, ['other_date'], ['testfile.txt'])
    record5 = create_mock_record(PublishStatus.PUBLIC.value, ['other_date'], ['testfile.txt'], None)
    record_multiple_files = create_mock_record(PublishStatus.PUBLIC.value, ['open_no', 'open_date', 'other_date'], ['testfile1.txt', 'testfile2.txt', 'testfile3.txt'])

    # Mock secret URLs
    mock_secret_url = MagicMock()
    mock_secret_url.delete_logically = MagicMock()
    mock_FileSecretDownload.query.filter_by.return_value.all.return_value = [mock_secret_url]

    # Create instance of UpdateItem
    update_item = UpdateItem()

    # record1のテスト
    assert_publish(record1, PublishStatus.PUBLIC.value)

    # record2のテスト
    assert_publish(record2, PublishStatus.PUBLIC.value)

    # record3のテスト
    assert_publish(record3, PublishStatus.PUBLIC.value)

    # record4のテスト
    assert_publish(record4, PublishStatus.PUBLIC.value, reset_mock=False)
    # record4のシークレットURL削除確認
    mock_FileSecretDownload.query.filter_by.assert_called_with(record_id='12345', is_deleted=False, file_name='testfile.txt')
    assert mock_secret_url.delete_logically.call_count == 1

    # モックの呼び出し履歴をリセット
    mock_FileSecretDownload.query.filter_by.reset_mock()
    mock_secret_url.delete_logically.reset_mock()

    # record5のテスト (recidがNoneの場合)
    assert_publish(record5, PublishStatus.PUBLIC.value, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_not_called()
    mock_secret_url.delete_logically.assert_not_called()

    # 複数のファイルが含まれている場合のテスト
    record_multiple_files = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'other_date'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_multiple_files, PublishStatus.PUBLIC.value, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    assert mock_secret_url.delete_logically.call_count == 2

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # 片方のファイルが更新され、片方が更新されない場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'open_no'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_partial_update, PublishStatus.PUBLIC.value, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    assert mock_secret_url.delete_logically.call_count == 1

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # どちらのファイルも論理削除が行われない場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['open_no', 'open_no'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_partial_update, PublishStatus.PUBLIC.value, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    mock_secret_url.delete_logically.assert_not_called()

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # 2つ以上のファイルすべてが更新され、論理削除が行われる場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'other_date','other_date'], ['testfile1.txt', 'testfile2.txt', 'testfile3.txt'])
    assert_publish(record_partial_update, PublishStatus.PUBLIC.value, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile3.txt')
    assert mock_secret_url.delete_logically.call_count == 3

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # attribute_value_mltが空のリストの場合のテスト
    record_empty_role = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': []
        }
    })
    update_item.publish(record_empty_role, PublishStatus.PUBLIC.value)
    mock_secret_url.delete_logically.assert_not_called()
    assert record_empty_role['publish_status'] == PublishStatus.PUBLIC.value

    # "accessrole"が欠落しているケースのテスト
    record_no_role = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': [{'filename': 'testfile.txt'}]
        }
    })
    update_item.publish(record_no_role, PublishStatus.PUBLIC.value)
    mock_secret_url.delete_logically.assert_not_called()
    assert record_no_role['publish_status'] == PublishStatus.PUBLIC.value

    # "attribute_value_mlt"が辞書ではない場合のテスト
    record_non_dict_attribute_value_mlt = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': ['not_dict']
        }
    })
    update_item.publish(record_non_dict_attribute_value_mlt, PublishStatus.PUBLIC.value)
    mock_secret_url.delete_logically.assert_not_called()
    assert record_non_dict_attribute_value_mlt['publish_status'] == PublishStatus.PUBLIC.value

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_init_activity(app, users, item_type, workflow):
    """
    Test init_activity

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    with app.test_request_context():
        login_user(users[2]["obj"])
        # send param
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}

        # 51992 case.01(init_activity)
        q = Activity.query.all()
        assert len(q) == 0
        q = ActivityHistory.query.all()
        assert len(q) == 0
        q = ActivityAction.query.all()
        assert len(q) == 0

        activity = WorkActivity()
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
        activity_detail = activity.init_activity(input)
        assert isinstance(activity_detail, Activity)
        q = Activity.query.all()
        assert len(q) == 1
        q = ActivityHistory.query.all()
        assert len(q) == 1
        q = ActivityAction.query.all()
        assert len(q) == 7


        with patch("weko_workflow.api.current_app") as mock_current_app:
            mock_current_app.config = {
                'WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE': True,
                'WEKO_ITEMS_UI_SHOW_TERM_AND_CONDITION': ['itemtype_with_terms'],
                'WEKO_WORKFLOW_MAX_ACTIVITY_ID': 1000000,
                'WEKO_WORKFLOW_ACTIVITY_ID_FORMAT': 'A-{}-{}'
            }

            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_confirm_term_of_use': False}
            # 51992 case.02(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == False

            # 51992 case.03(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms2'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == True

            # 51992 case.04(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == str(users[2]["obj"].id)

            # 51992 case.05(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_login_user': 1}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == 1

            # 51992 case.08(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'related_title': 'Test%20Title'}
            activity_detail = activity.init_activity(input)
            assert activity_detail.extra_info["related_title"] == 'Test Title'

            # 51992 case.09(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            with patch("weko_workflow.api.PersistentIdentifier.create", side_effect=Exception("Test Error")):
                with pytest.raises(Exception):
                    activity.init_activity(input)

            # 51992 case.10(init_activity)
            with patch("weko_workflow.api.db.session.add", side_effect=Exception("Test Error")):
                input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
                with pytest.raises(Exception):
                    activity.init_activity(input)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_single_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_single_flow_action(app, users, item_type, workflow_one, mocker):
    """
    Test init_activity when FlowAction return a data

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow_one (fixture): one FlowAction workflow
        mocker (fixture): mocker
    """
    workflow_id = workflow_one["workflow"].flows_id
    flow_id = int(workflow_one["flow"].id)
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_id}

    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.06(init_activity)
    with app.test_request_context():
        result = work_activity.init_activity(input)

        assert result.action_id == 0
        assert result.action_order == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_no_begin_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_no_begin_action(app, users, item_type, workflow, no_begin_action, mocker):
    """
    Test init_activity when workflow_action has not begin_action

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
        no_begin_action(fixture): update begin_action to other_action
        mocker (fixture): mocker
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}

    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.07(init_activity)
    with app.test_request_context():
        with pytest.raises(AttributeError):
            result = work_activity.init_activity(input)

            assert result.action_id == 0  # action_id should be the initial value

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_GetCommunity_get_community_by_root_node_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetCommunity_get_community_by_root_node_id(db):
    communities = GetCommunity.get_community_by_root_node_id(1738541618993)
    assert communities is not None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_deleted_workflow_list -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_deleted_workflow_list(app,db,workflow):
    res = WorkFlow().get_deleted_workflow_list()
    assert res[0].flows_name == "test workflow02"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_activity_request_mail_list_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_activity_request_mail_list_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _request_maillist1 = []
    _request_maillist2 = [{"email": "test@example.com", "author_id": ""}]
    activity.create_or_update_activity_request_mail("1", _request_maillist1, True)
    assert activity.get_activity_request_mail("1").request_maillist == []
    activity.create_or_update_activity_request_mail("1", _request_maillist2, True)
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2
    activity.create_or_update_activity_request_mail("1111111", _request_maillist1, "aaa")
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("case, param_method, notification_method, mail_method", [
    ("registered", "_get_params_for_registrant", "create_item_registered", "send_mail_item_registered"),
    ("request_approval", "_get_params_for_approver", "create_request_approval", "send_mail_request_approval"),
    ("approved", "_get_params_for_registrant", "create_item_approved", "send_mail_item_approved"),
    ("rejected", "_get_params_for_registrant", "create_item_rejected", "send_mail_item_rejected"),
    ("deleted", "_get_params_for_registrant", "create_item_deleted", "send_mail_item_deleted"),
    ("deletion_request", "_get_params_for_approver", "create_request_delete_approval", "send_mail_request_delete_approval"),
    ("deletion_approved", "_get_params_for_registrant", "create_item_delete_approved", "send_mail_item_delete_approved"),
    ("deletion_rejected", "_get_params_for_registrant", "create_item_delete_rejected", "send_mail_item_delete_rejected"),
])
def test_workactivity_notify_about_activity(app, db_register_full_action, mocker, case, param_method, notification_method, mail_method):
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1 = db_register_full_action["activities"][0]
    activity = WorkActivity()

    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    mock_mail = mocker.patch.object(activity, mail_method)

    activity.notify_about_activity(activity1.activity_id, case)

    expected_params = getattr(activity, param_method)
    expected_notification = getattr(Notification, notification_method)

    mock_notify.assert_called_once_with(activity1, case, expected_params, expected_notification)
    mock_mail.assert_called_once_with(activity1)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_early_return -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_early_return(app, db, db_register_full_action, mocker):
    activity = WorkActivity()

    # with WEKO_NOTIFICATIONS is False
    app.config["WEKO_NOTIFICATIONS"] = False
    activity1 = db_register_full_action["activities"][0]
    mock_get_activity_by_id = mocker.patch.object(activity, "get_activity_by_id")
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_get_activity_by_id.assert_not_called()

    # with restricted workflow
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1.workflow.open_restricted = True
    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    mock_mail = mocker.patch.object(activity, "send_mail_item_registered")
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_notify.assert_not_called()
    mock_mail.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_invalid_case -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_invalid_case(app, db, db_register_full_action, mocker):
    activity = WorkActivity()
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1 = db_register_full_action["activities"][0]
    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    assert activity.notify_about_activity(activity1.activity_id, 'invalid_case') == None
    mock_notify.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_get_params_for_registrant -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_get_params_for_registrant(app, users, db_register_full_action, db_records, db_user_profile):
    mock_activity = MagicMock(
        activity_login_user=users[0]["id"],
        activity_update_user=users[1]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
    )
    activity_obj = WorkActivity()
    set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)
    assert set_target_id == {users[0]["id"]}
    assert recid == db_records[2][0]
    assert actor_id == users[1]["id"]
    assert actor_name == None

    activity_obj = WorkActivity()

    # case: not shared_user_ids
    # activity_login_user == activity_update_user: directly registration
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=None,
            item_id=db_records[2][2].id,
        )

        set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)

        assert set_target_id == set()
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])

    # case: not shared_user_ids
    # activity_login_user != activity_update_user: item approvaled
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[2]["id"],
            shared_user_ids=None,
            item_id=db_records[2][2].id,
        )

        set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)

        assert set_target_id == {users[0]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[2]["id"]
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[2]["id"])

    # 以降は代理投稿者が複数指定された場合(複数化フラグ有効)
    app.config["WEKO_ITEMS_UI_PROXY_POSTING"] = True

    # case: shared_user_ids
    # activity_login_user == activity_update_user: directly registration
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=[{"user": users[1]["id"]}, {"user": users[3]["id"]}],
            item_id=db_records[2][2].id,
        )

        set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)

        assert set_target_id == {users[1]["id"], users[3]["id"]}
        assert recid == db_records[2][0]
        # actor は操作者のまま維持される(shared_user_ids[0] に上書きされない)
        assert actor_id == users[0]["id"]
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])

    # case: shared_user_ids
    # activity_login_user != activity_update_user: item approvaled
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[2]["id"],
            shared_user_ids=[{"user": users[1]["id"]}, {"user": users[3]["id"]}],
            item_id=db_records[2][2].id,
        )

        set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)

        assert set_target_id == {users[0]["id"], users[1]["id"], users[3]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[2]["id"]
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[2]["id"])


@pytest.fixture
def mock_create_item_registered(mocker):
    return mocker.patch.object(
        Notification, "create_item_registered",
        return_value=Notification()
    )


@pytest.fixture
def mock_send(mocker):
    return mocker.patch.object(Notification, "send")


@pytest.fixture
def mock_inbox_url(mocker):
    return mocker.patch(
        "weko_workflow.api.inbox_url",
        return_value="http://example.com/inbox"
    )


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("weko_workflow.api.current_app.logger")


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_success(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    expected_calls = [
        call(1, "123", 1, context_id=1, actor_name="actor_name", object_name="test"),
        call(2, "123", 1, context_id=1, actor_name="actor_name", object_name="test"),
    ]
    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    assert mock_create_item_registered.call_args_list == expected_calls
    assert mock_send.call_count == 2
    mock_logger.info.assert_called_once_with(
        "2 notification(s) sent for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_sql_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_sql_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    getter = MagicMock(side_effect=SQLAlchemyError)

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Failed to get notification parameters for activity: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_valid_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_valid_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_create_item_registered.side_effect = ValidationError("Invalid data")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )
    mock_logger.error.assert_called_once_with(
        "Failed to send notification for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_http_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_http_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_send.side_effect = HTTPError("HTTP error occurred")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Failed to send notification for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_exception(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_create_item_registered.side_effect = Exception("Unexpected error")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Unexpected error had occurred during sending notification for activity: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_invalid_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_invalid_activity(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = MagicMock()
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_create_item_registered.assert_not_called()
    mock_send.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_get_params_for_approver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_get_params_for_approver(app, users, db, db_register_full_action, mocker, db_records, db_user_profile):
    from invenio_communities.models import Community
    from weko_index_tree.models import Index

    index = Index(position=1, id=111)
    db.session.add(index)
    db.session.commit()
    comm = Community(id="test_com11", id_role=users[3]["id"],
                        id_user=users[3]["id"], title="test community",
                        description="this is test community",
                        root_node_id=index.id)
    db.session.add(comm)
    db.session.commit()
    flow_define = db_register_full_action["flow_define"]

    mock_activity1 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=users[1]["id"],
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id=None
    )
    mock_activity2 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id=None,
        action_order=3
    )
    mock_activity3 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id="test_com11"
    )
    activity = WorkActivity()
    flow_define = db_register_full_action["flow_define"]

    # case: not shared_user_ids, community_id is None
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=None,
            activity_community_id=None,
            item_id=db_records[2][2].id,
            flow_define=flow_define,
            action_order=3
        )

        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity)

        assert set_target_id == {users[1]["id"], users[6]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])

    # case: shared_user_ids is not None, community_id is None
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=[{"user": users[4]["id"]}, {"user": users[5]["id"]}],
            activity_community_id=None,
            item_id=db_records[2][2].id,
            flow_define=flow_define,
        )

        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity)

        assert set_target_id == {users[1]["id"], users[6]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]  # actor は代理投稿者の先頭ではなく操作者(activity_update_user)
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])

    flow_id = flow_define.flow_id
    flow_detail = Flow().get_flow_detail(flow_id)
    # case: shared_user_ids is not None, community_id is None,
    # and action_role is specified.
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile, \
            patch("weko_workflow.api.Flow.get_flow_detail") as mock_get_flow_detail:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_flow_detail = MagicMock(
            flow_actions=[_ for _ in flow_detail.flow_actions]
        )
        mock_flow_detail.flow_actions[3].action_role = MagicMock(action_role=6, action_user=None)
        mock_get_flow_detail.return_value = mock_flow_detail
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=[{"user": users[4]["id"]}, {"user": users[5]["id"]}],
            activity_community_id=None,
            item_id=db_records[2][2].id,
            flow_define=flow_define,
            action_order=3
        )

        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity)

        assert set_target_id == {users[1]["id"], users[6]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]  # actor は代理投稿者の先頭ではなく操作者(activity_update_user)
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])
        mock_get_flow_detail.assert_called_once_with(flow_id)

    # case: shared_user_ids is not None, community_id is None,
    # and action_role is specified, action_user_exclude is True.
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile, \
            patch("weko_workflow.api.Flow.get_flow_detail") as mock_get_flow_detail:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_flow_detail = MagicMock(
            flow_actions=[_ for _ in flow_detail.flow_actions]
        )
        mock_flow_detail.flow_actions[3].action_role = MagicMock(action_role=6, action_user=7, action_user_exclude=False)
        mock_get_flow_detail.return_value = mock_flow_detail
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=[{"user": users[4]["id"]}, {"user": users[5]["id"]}],
            activity_community_id=None,
            item_id=db_records[2][2].id,
            flow_define=flow_define,
            action_order=3
        )

        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity)

        assert set_target_id == {users[1]["id"], users[5]["id"], users[6]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]  # actor は代理投稿者の先頭ではなく操作者(activity_update_user)
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])
        mock_get_flow_detail.assert_called_once_with(flow_id)

    # case: community_id is specified.
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_get_user_profile, \
            patch("weko_workflow.api.Flow.get_flow_detail") as mock_get_flow_detail, \
            patch("weko_workflow.api.GetCommunity.get_community_by_id") as mock_get_community_by_id:
        mock_user_profile = MagicMock(username="test_username")
        mock_get_user_profile.return_value = mock_user_profile
        mock_get_community_by_id.return_value = MagicMock(id_role=4)
        mock_flow_detail = MagicMock(
            flow_actions=[_ for _ in flow_detail.flow_actions]
        )
        mock_flow_detail.flow_actions[3].action_role = MagicMock(action_role=6, action_user=7, action_user_exclude=False)
        mock_get_flow_detail.return_value = mock_flow_detail
        mock_activity = MagicMock(
            activity_login_user=users[0]["id"],
            activity_update_user=users[0]["id"],
            shared_user_ids=[{"user": users[4]["id"]}, {"user": users[5]["id"]}],
            activity_community_id="comm01",
            item_id=db_records[2][2].id,
            flow_define=flow_define,
            action_order=3,
        )

        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity)

        assert set_target_id == {users[1]["id"], users[3]["id"], users[5]["id"], users[6]["id"]}
        assert recid == db_records[2][0]
        assert actor_id == users[0]["id"]  # actor は代理投稿者の先頭ではなく操作者(activity_update_user)
        assert actor_name == mock_user_profile.username
        mock_get_user_profile.assert_called_once_with(users[0]["id"])
        mock_get_flow_detail.assert_called_once_with(flow_id)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_registered -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_registered(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_registered_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_registered(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_registered(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_approval(app, users, db, db_register_full_action, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_request_approval_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_approver',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_approved(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_approved_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_approved(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_rejected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_rejected(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_rejected(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_deleted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_deleted(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_deleted_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_deleted(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_deleted(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_delete_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_delete_approval(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_request_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_approver",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_delete_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_delete_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_delete_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_delete_approved(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_approved_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_approved(activity)
    assert res is None


def test_workactivity_send_mail_item_delete_rejected(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_delete_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_rejected(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_send_notification_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_notification_email(app, mocker):
    mock_activity = MagicMock(activity_id="123")
    mock_target = MagicMock(id=1, email="test@example.com", confirmed_at=True)
    mock_settings = {1: MagicMock(subscribe_email=True)}
    mock_profiles = {1: MagicMock(language="en")}
    mock_template = "email_template_{language}.tpl"
    mock_data_callback = MagicMock(return_value={"subject": "Test Subject", "body": "Test Body"})

    mock_load_template = mocker.patch("weko_workflow.utils.load_template", return_value="template_content")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", return_value={"subject": "Test Subject", "body": "Test Body"})
    mock_send_mail = mocker.patch("weko_workflow.utils.send_mail")

    activity = WorkActivity()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)

    mock_load_template.assert_called_once_with(mock_template, "en")
    mock_fill_template.assert_called_once_with("template_content", mock_data_callback.return_value)
    mock_send_mail.assert_called_once_with({
        'mail_subject': 'Test Subject',
        'mail_body': 'Test Body',
        'mail_recipients': ['test@example.com'],
        'mail_cc': [],
        'mail_bcc': []
    })


    mock_settings_false = {1: MagicMock(subscribe_email=False)}
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings_false, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()

    mock_target_false = MagicMock(id=1, email="test@example.com", confirmed_at=False)
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target_false], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()

    mock_send_mail.reset_mock()
    mock_send_mail.return_value = False
    res = activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)
    assert res == 0

    mock_logger = mocker.patch("weko_workflow.api.current_app.logger.error")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", side_effect=Exception("Template error"))
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_logger.assert_called_once()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_with_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_notification_context_with_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"
    recid = MagicMock(pid_value="1234567890")

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name, recid)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/records/1234567890"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_without_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__create_notification_context_without_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/workflow/activity/detail/123"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test__get_settings_for_targets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__get_settings_for_targets(app, users, db_user_profile, db_notification_user_settings):
    set_target_id = {users[2]["id"]}
    activity_obj = WorkActivity()
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == None

    actor_id = users[2]["id"]
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id, actor_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == users[2]["obj"]


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_non_extract_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_non_extract_files(app, mocker):
    activity = WorkActivity()

    # Mock the `get_activity_metadata` method
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": True},
            {"filename": "file2.txt", "non_extract": False},
            {"filename": "file3.txt", "non_extract": True}
        ]
    }))

    # metadata is available
    result = activity.get_non_extract_files(activity_id=1)
    assert result == ["file1.txt", "file3.txt"]

    # metadata is None
    mocker.patch.object(activity, 'get_activity_metadata', return_value=None)
    result = activity.get_non_extract_files(activity_id=1)
    assert result is None

    # no files have "non_extract" set to True
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": False},
            {"filename": "file2.txt", "non_extract": False}
        ]
    }))
    result = activity.get_non_extract_files(activity_id=1)
    assert result == []

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_UpdateItem_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_UpdateItem_publish(app, db_records, mocker):
    mock_update_es_data = mocker.patch("weko_deposit.api.WekoIndexer.update_es_data")

    updated_item = UpdateItem()
    dep = db_records[0][6]
    updated_item.publish(dep, PublishStatus.PRIVATE.value)
    assert dep.get('publish_status') == PublishStatus.PRIVATE.value
    mock_update_es_data.assert_called_once_with(
        dep, update_revision=False, field="publish_status")

    mock_update_es_data.reset_mock()
    updated_item.publish(dep, PublishStatus.PUBLIC.value)
    assert dep.get('publish_status') == PublishStatus.PUBLIC.value
    mock_update_es_data.assert_called_once_with(
        dep, update_revision=False, field="publish_status")

# def __create_self_user_id_json(self_user_id)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test___create_self_user_id_json -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test___create_self_user_id_json(app):
    activity = WorkActivity()
    self_user_id = 123
    # WEKO_ITEMS_UI_PROXY_POSTING is False
    # 末尾要素の判定は SQL 側(__is_last_shared_user)で行うため、フラグを参照せず末尾に ] を連結しない
    app.config['WEKO_ITEMS_UI_PROXY_POSTING'] = False
    result = activity._WorkActivity__create_self_user_id_json(self_user_id)
    assert result == '{"user": 123}'

    # WEKO_ITEMS_UI_PROXY_POSTING is True
    app.config['WEKO_ITEMS_UI_PROXY_POSTING'] = True
    result = activity._WorkActivity__create_self_user_id_json(self_user_id)
    assert result == '{"user": 123}'

# def query_activities_by_tab_is_wait(query)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_wait -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_wait(users, db):
    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        # temp_data の JSON パス修正・末尾要素条件(複数化フラグ無効の既定)により
        # SQL が変わったため、SQL 全文の一致ではなく構造で確認する
        ret = WorkActivity.query_activities_by_tab_is_wait(query, False, True, [1])
        sql = compile_sql(ret)
        # 代理投稿者(個人)・owner の条件が 6 箇所に出現し、誤ったパス指定が残っていない
        assert "'metainfo'" not in sql
        assert sql.count("#>> '{metainfo,owner}'") == 6
        assert sql.count("#> '{metainfo,shared_user_ids}'") >= 6
        # 複数化フラグ無効ではロール条件が付かない
        assert "CAST(workflow_activity.shared_role_ids" not in sql
        assert "{metainfo,shared_role_ids}" not in sql
        # コミュニティ管理者向けの NOT EXISTS 条件
        assert "NOT (EXISTS" in sql
        assert "jsonb_array_elements_text(records_metadata.json -> 'path')" in sql

    # admin user
    with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
        ret = WorkActivity.query_activities_by_tab_is_wait(query, True, False, [1])
        sql = compile_sql(ret)
        assert "'metainfo'" not in sql
        assert sql.count("#>> '{metainfo,owner}'") == 6
        assert "NOT (EXISTS" not in sql

    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        expected = "AND workflow_activity.activity_login_user = %(activity_login_user_1)s " \
                    "AND (" \
                        "workflow_flow_action_role.action_user != %(action_user_1)s " \
                        "AND workflow_flow_action_role.action_user_exclude = %(action_user_exclude_1)s " \
                        "OR workflow_flow_action_role.action_role NOT IN (%(action_role_1)s) " \
                        "AND workflow_flow_action_role.action_role_exclude = %(action_role_exclude_1)s " \
                        "OR workflow_activity_action.action_handler NOT IN (%(action_handler_1)s))"
        ret = WorkActivity.query_activities_by_tab_is_wait(query, False, False, [])
        assert str(ret).find(expected) != -1

    # admin user
    with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
        admin_expected = expected.replace(
            "%(action_handler_1)s", "%(action_handler_1)s, %(action_handler_2)s"
        )
        ret = WorkActivity.query_activities_by_tab_is_wait(query, True, False, [])
        assert str(ret).find(admin_expected) != -1

# def query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_all(users, db):
    is_community_admin=False
    community_user_ids=[]
    comadmin_index_list = []
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                )
            )
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%') AND workflow_flow_action.action_id != ?"
        ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids, comadmin_index_list)
        assert str(ret).find(expected)

        is_community_admin = True
        community_user_ids = [3]
        expected = "(workflow_activity.activity_update_user LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids, comadmin_index_list)
        assert str(ret).find(expected)

# def query_activities_by_tab_is_todo(query, is_admin, is_community_admin, community_user_ids, comadmin_index_list)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_todo(users, db):
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        is_community_admin = False
        is_community_admin = False
        community_user_ids = []
        comadmin_index_list = []
        query = db.session.query(
                _Activity,
                _FlowActionRole
            )
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, is_community_admin, is_community_admin, community_user_ids, comadmin_index_list)
        assert str(ret).find(expected)
        is_community_admin = True
        current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
        expected = "(workflow_activity.action_handler LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, is_community_admin, is_community_admin, community_user_ids, comadmin_index_list)
        assert str(ret).find(expected)

        current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, is_community_admin, is_community_admin, community_user_ids, comadmin_index_list)
        assert str(ret).find(expected)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (4, 6, 'deny', True),
    (5, 4, 'allow', True),
    (7, 5, 'deny', False),
    (6, 3, 'allow', False),
])
def test_WorkActivity_get_activity_action_role(app, activity_with_roles, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles["activity"]
    item_metadata = activity_with_roles['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    _, users = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    print(users)
    assert (owner_id in users[expected_index]) == expected_included

# for roles
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (6, 3, 'allow', True),
    (5, 4, 'deny', True),
])
def test_WorkActivity_get_activity_action_role2(app, activity_with_roles_for_request_mail, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles_for_request_mail["activity"]
    item_metadata = activity_with_roles_for_request_mail['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    roles, _ = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    assert (owner_id in roles[expected_index]) == expected_included

# for request_mail
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (7, 5, 'allow', True),
    (4, 6, 'deny', True),
    (3, 2, 'allow', True)
])
def test_WorkActivity_get_activity_action_role3(app, activity_with_roles_for_request_mail, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles_for_request_mail["activity"]
    item_metadata = activity_with_roles_for_request_mail['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    _, users = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    assert (owner_id in users[expected_index]) == expected_included

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_query_activities_by_tab_is_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_item_registrant, users_idx, expected_activity_included', [
    (True, 0, True),
    (True, 4, False),
    (False, 0, False),
    (False, 4, False),
])
def test_WorkActivity_query_activities_by_tab_is_todo(app, workflow, db, users, item_type, action_item_registrant, users_idx, expected_activity_included):
    with app.test_request_context():
        login_user(users[users_idx]["obj"])

        # flow action role
        flow_actions = workflow['flow_action']
        flow_action_roles = [
            FlowActionRole(id = 4,
                        flow_action_id = flow_actions[5].id,
                        action_user_exclude = False,
                        action_item_registrant = action_item_registrant),
        ]
        with db.session.begin_nested():
            db.session.add_all(flow_action_roles)
        db.session.commit()

        # item_metadata
        item_metdata = ItemsMetadata.create(
            data = {
                "id": "1",
                "pid": {
                    "type": "depid",
                    "value": "1",
                    "revision_id": 0
                },
                "lang": "ja",
                "owner": str(users[0]["obj"].id),
                "title": "sample01",
                "owners": [
                    users[0]["obj"].id
                ],
                "status": "published",
                "$schema": "/items/jsonschema/" + str(item_type[0].get("id")),
                "pubdate": "2020-08-29",
                "created_by": users[0]["obj"].id,
                "owners_ext": {
                    "email": "sample@nii.ac.jp",
                    "username": "sample",
                    "displayname": "sample"
                },
                "shared_user_ids": [],
                "item_1617186331708": [
                    {
                    "subitem_1551255647225": "sample01",
                    "subitem_1551255648112": "ja"
                    }
                ],
                "item_1617258105262": {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper"
                }
            },
            item_type_id = item_type[0].get("id"),
        )

        # set activity
        activity = Activity(
            activity_id='1', workflow_id=workflow["workflow"].id,
            flow_id=workflow["flow"].id,
            action_id=4,
            activity_login_user=users[0]['obj'].id,
            activity_status=ActionStatusPolicy.ACTION_BEGIN,
            activity_update_user=1,
            activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='test', shared_user_ids=[], extra_info={},
            action_order=6, item_id=item_metdata.model.id,
        )
        request_mail = ActivityRequestMail(
            activity_id=activity.activity_id,
            request_maillist=users[users_idx]["email"]
        )
        with db.session.begin_nested():
            db.session.add(activity)
            db.session.add(request_mail)
        db.session.commit()

        activity_action = ActivityAction(activity_id=activity.activity_id,
                                        action_id=4,action_status="M",
                                        action_handler=1, action_order=6)

        with db.session.begin_nested():
            db.session.add(activity_action)
        db.session.commit()
        is_community_admin = False
        community_user_ids = []
        comadmin_index_list = []
        actual_query = WorkActivity.query_activities_by_tab_is_todo(
            Activity.query, False, is_community_admin, community_user_ids, comadmin_index_list)
        actual = actual_query.all()

        assert (len(actual) > 0) == expected_activity_included


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_query_activities_by_tab_is_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_idx, expected_included', [
    (0, True),
    (4, False),
])
def test_WorkActivity_query_activities_by_tab_is_all(db,app, users, activity_with_roles, users_idx, expected_included):
    with app.test_request_context():
        login_user(users[users_idx]["obj"])
        activity = activity_with_roles["activity"]
        request_mail = ActivityRequestMail(
            activity_id=activity.activity_id,
            request_maillist=users[users_idx]["email"]
        )
        with db.session.begin_nested():
            db.session.add(request_mail)
        db.session.commit()

        actual_query = WorkActivity.query_activities_by_tab_is_all(
            Activity.query, False, [], [])
        actual = actual_query.all()
        assert (len(actual) > 0) == expected_included

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_request_mail_list_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_request_mail_list_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _request_maillist1 = []
    _request_maillist2 = [{"email": "test@example.com", "author_id": ""}]
    activity.create_or_update_activity_request_mail("1", _request_maillist1, True)
    assert activity.get_activity_request_mail("1")
    activity.create_or_update_activity_request_mail("1", _request_maillist2, True)
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2
    activity.create_or_update_activity_request_mail("1111111", _request_maillist1, "aaa")
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2

# def get_user_ids_of_request_mails_by_activity_id
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_user_ids_of_request_mails_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_user_ids_of_request_mails_by_activity_id(workflow, users, mocker):
    activity = WorkActivity()
    activityrequestmails = [
        ActivityRequestMail(
        id = 1,
        activity_id = 1,
        display_request_button = True,
        request_maillist = []
    ),
        ActivityRequestMail(
            id = 2,
            activity_id = 2,
            display_request_button = False,
            request_maillist = [{}]
    ),
        ActivityRequestMail(
            id = 3,
            activity_id = 3,
            display_request_button = True,
            request_maillist = [{"email":"not_user","author_id":""},
                                {"email":"user@test.org","author_id":""},
                                {"email":"contributor@test.org","author_id":""}]
    )]
    with patch("weko_workflow.api.WorkActivity.get_activity_detail", return_value = _Activity(extra_info={"record_id":1, "is_restricted_access":True})):
        mock = mocker.patch("weko_workflow.api.WorkActivity.get_user_ids_of_request_mails_by_record_id")
        activity.get_user_ids_of_request_mails_by_activity_id(1)
        mock.assert_called()
    mocker.patch("weko_workflow.api.WorkActivity.get_activity_detail", return_value = _Activity(extra_info={}))
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = None):
        assert activity.get_user_ids_of_request_mails_by_activity_id(1) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[0]):
        assert activity.get_user_ids_of_request_mails_by_activity_id(1) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[1]):
        assert activity.get_user_ids_of_request_mails_by_activity_id(2) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[2]):
        ids = activity.get_user_ids_of_request_mails_by_activity_id(3)
        assert ids == [User.query.filter_by(email="contributor@test.org").one_or_none().id]

# def get_user_ids_of_request_mails_by_record_id
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_user_ids_of_request_mails_by_record_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_user_ids_of_request_mails_by_record_id(workflow, users, mocker):
    activity = WorkActivity()
    requestmails = [[],[{}],[{"email":"not_user","author_id":""},
                                {"email":"user@test.org","author_id":""},
                                {"email":"contributor@test.org","author_id":""}]]
    mocker.patch("weko_workflow.api.PersistentIdentifier.get")
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_assigned_object")
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=None):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[0]):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[1]):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[2]):
        ids = activity.get_user_ids_of_request_mails_by_record_id(0)
        assert ids == [User.query.filter_by(email="contributor@test.org").one_or_none().id]



# def check_user_role_for_mail
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_check_user_role_for_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_user_role_for_mail(users):
    activity = WorkActivity()
    # user is admin
    roles={'allow':[5],'deny':[]}
    assert activity.check_user_role_for_mail(users[2]["id"], roles)

    # user is cont, cont in allow
    roles={'allow':[3],'deny':[]}
    assert activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont not in allow
    roles={'allow':[2],'deny':[]}
    assert not activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont in deny
    roles={'allow':[],'deny':[3]}
    assert not activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont not in deny
    roles={'allow':[],'deny':[2]}
    assert activity.check_user_role_for_mail(users[0]["id"], roles)

# def get_recirds_for_request_mail_by_mailaddress
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_recirds_for_request_mail_by_mailaddress -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_recirds_for_request_mail_by_mailaddress(db,mocker):
    activity = WorkActivity()
    request_mail_list=[
        _RequestMailList(item_id="1234",mail_list=[{"email": "wekosoftware@nii.ac.jp", "author_id": ""}]),
        _RequestMailList(item_id="1235",mail_list=[{"email": "wekosoftware@nii.ac.jp", "author_id": ""}])
    ]
    mocker.patch("weko_workflow.api.RequestMailList.get_request_mail_by_mailaddress",return_value = request_mail_list)

    with patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value = PersistentIdentifier(pid_value = 1)):
        recids_list = activity.get_recids_for_request_mail_by_mailaddress("wekosoftware@nii.ac.jp")
        assert recids_list
    assert not activity.get_recids_for_request_mail_by_mailaddress("wekosoftware@nii.ac.jp")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_item_application_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_item_application_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _item_application1 = {}
    _item_application2 = {"workflow":"1", "terms":"term_free", "termsDescription":"test"}

    # create
    activity.create_or_update_activity_item_application("1", _item_application1, True)
    assert activity.get_activity_item_application("1")

    # update
    activity.create_or_update_activity_item_application("1", _item_application2, True)
    assert activity.get_activity_item_application("1").item_application == _item_application2

    # error
    activity.create_or_update_activity_item_application("1111111", _item_application1, "aaaaa")
    assert activity.get_activity_item_application("1").item_application == _item_application2

    # not hit search
    assert not activity.get_activity_item_application("1111")



import logging

from sqlalchemy import text
from sqlalchemy.sql.elements import False_

_PROXY_FLAG = "WEKO_ITEMS_UI_PROXY_POSTING"
_ALL_FUNCS = (("is_wait", 6), ("is_all", 1), ("is_todo", 2))


def _expanded_temp_data():
    """temp_data を展開した式の SQL 表現."""
    return "CAST(workflow_activity.temp_data #>> '{}' AS JSONB)"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_json_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_json_path(app, db, users, workflow):
    """temp_data が文字列スカラー・オブジェクトのいずれでも、
    metainfo.shared_user_ids・metainfo.owner で一覧に含まれる."""
    env = build_proxy_env(app)
    set_proxy_posting(app, True)

    def make(temp_data):
        return create_proxy_activity(
            workflow, env.U_O, shared_user_ids=[], temp_data=temp_data)

    shared = {"metainfo": {"shared_user_ids": [{"user": env.U_P1.id}]}}
    owner = {"metainfo": {"owner": str(env.U_P2.id)}}
    # 実運用と同じ保存形式(json.dumps した文字列 = JSONB の文字列スカラー)
    a1 = make(json.dumps(shared))
    a2 = make(json.dumps(owner))
    # オブジェクトとして保存した形式
    a1o = make(shared)
    a2o = make(owner)

    # 1. jsonb_typeof(temp_data)
    def typeof(activity):
        return db.session.execute(
            text("SELECT jsonb_typeof(temp_data) FROM workflow_activity "
                 "WHERE activity_id = :a"), {"a": activity.activity_id}
        ).scalar()
    assert typeof(a1) == "string"
    assert typeof(a2) == "string"
    assert typeof(a1o) == "object"
    assert typeof(a2o) == "object"

    # 2. All タブ・Todo タブ
    all_ids = {a1.activity_id, a2.activity_id, a1o.activity_id, a2o.activity_id}
    for tab in ("all", "todo"):
        ids = list_activity_ids(tab, env.U_P1)
        assert {a1.activity_id, a1o.activity_id} <= ids
        ids = list_activity_ids(tab, env.U_P2)
        assert {a2.activity_id, a2o.activity_id} <= ids
        ids = list_activity_ids(tab, env.U_N)
        assert not (all_ids & ids)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_json_path_sql -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("proxy_posting", [True, False])
def test_query_activities_json_path_sql(app, db, users, proxy_posting):
    """生成 SQL で temp_data を展開してからパス指定していること."""
    env = build_proxy_env(app)
    app.config["WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY"] = False
    set_proxy_posting(app, proxy_posting)
    expanded = _expanded_temp_data()
    user_json = '{"user": %d}' % env.U_N.id

    for func_name, n in _ALL_FUNCS:
        sql = compile_sql(build_func_query(func_name, env.U_N))
        # 誤ったパス指定が残っていない
        assert "'metainfo'" not in sql
        # 展開後の式に対するパス指定(not_() 内の 3 箇所を含む)
        assert sql.count(expanded + " #>> '{metainfo,owner}'") == n
        # temp_data の列に直接 #>>・#> でパスを指定した箇所が無い
        assert "workflow_activity.temp_data #>> '{metainfo" not in sql
        assert "workflow_activity.temp_data #> '{metainfo" not in sql
        # 代理投稿者条件の比較値(末尾に ] を連結しない)
        assert user_json in sql
        assert user_json + "]" not in sql

        if proxy_posting:
            # 配列全体への文字列 LIKE
            assert sql.count(
                "CAST(workflow_activity.shared_user_ids AS VARCHAR)") == n
            assert sql.count(
                expanded + " #>> '{metainfo,shared_user_ids}'") == n
            assert "jsonb_typeof(" not in sql
            assert "@>" not in sql
        else:
            # jsonb_typeof(...) = 'array' を先に評価する入れ子の CASE と @>
            assert "CAST(workflow_activity.shared_user_ids AS VARCHAR)" not in sql
            assert sql.count(
                "jsonb_typeof(workflow_activity.shared_user_ids) = 'array'") == n
            assert sql.count(
                "jsonb_typeof(" + expanded
                + " #> '{metainfo,shared_user_ids}') = 'array'") == n
            assert sql.index("jsonb_typeof(") < sql.index("jsonb_array_length(")
            assert sql.count("@>") == 2 * n
            # temp_data 側の末尾要素の抽出は #>(jsonb を返す演算子)
            assert expanded + " #> '{metainfo,shared_user_ids}'" in sql
            assert expanded + " #>> '{metainfo,shared_user_ids}'" not in sql

    # is_wait は NOT で否定された 3 箇所の条件にも同じ展開とパスが用いられる
    sql = compile_sql(build_func_query("is_wait", env.U_N))
    if proxy_posting:
        assert sql.count("NOT LIKE") == 6


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_last_element -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_last_element(app, db, users, workflow):
    """複数化フラグ無効時は配列の物理的な末尾要素のみに一致する."""
    env = build_proxy_env(app)
    p1, p2 = env.U_P1.id, env.U_P2.id
    assert p1 < p2
    ordered = [{"user": p1}, {"user": p2}]
    reverse = [{"user": p2}, {"user": p1}]
    # temp_data は文字列スカラー(json.dumps した文字列)で保存する
    a3 = create_proxy_activity(
        workflow, env.U_O, shared_user_ids=ordered,
        temp_data=json.dumps({"metainfo": {}}))
    a4 = create_proxy_activity(
        workflow, env.U_O, shared_user_ids=[],
        temp_data=json.dumps({"metainfo": {"shared_user_ids": ordered}}))
    a3r = create_proxy_activity(
        workflow, env.U_O, shared_user_ids=reverse,
        temp_data=json.dumps({"metainfo": {}}))
    a4r = create_proxy_activity(
        workflow, env.U_O, shared_user_ids=[],
        temp_data=json.dumps({"metainfo": {"shared_user_ids": reverse}}))
    ids = {k: v.activity_id for k, v in
           dict(a3=a3, a4=a4, a3r=a3r, a4r=a4r).items()}
    four = set(ids.values())

    # 1. 複数化フラグ有効: 配列全体に一致
    set_proxy_posting(app, True)
    for tab in ("all", "todo"):
        for user in (env.U_P1, env.U_P2):
            assert four <= list_activity_ids(tab, user)

    # 2. 複数化フラグ無効: 保存順の物理的な末尾のみに一致(最大IDではない)
    set_proxy_posting(app, False)
    for tab in ("all", "todo"):
        found = list_activity_ids(tab, env.U_P2)
        assert {ids["a3"], ids["a4"]} <= found
        assert not ({ids["a3r"], ids["a4r"]} & found)
        found = list_activity_ids(tab, env.U_P1)
        assert {ids["a3r"], ids["a4r"]} <= found
        assert not ({ids["a3"], ids["a4"]} & found)

    # 3. __create_self_user_id_json はフラグを参照しない
    for flag in (True, False):
        set_proxy_posting(app, flag)
        assert WorkActivity._WorkActivity__create_self_user_id_json(p1) \
            == json.dumps({"user": p1})
        assert "]" not in WorkActivity._WorkActivity__create_self_user_id_json(p1)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_null_safe -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("proxy_posting", [True, False])
def test_query_activities_null_safe(app, db, users, workflow, proxy_posting):
    """NULL・空配列・配列以外の行で例外が発生せず、条件不成立となる."""
    env = build_proxy_env(app)
    set_proxy_posting(app, proxy_posting)
    mk = lambda **kw: create_proxy_activity(workflow, env.U_O, **kw)
    rows = []
    # A5: カラム・temp_data とも NULL
    rows.append(mk(shared_user_ids=None, temp_data=None))
    # A6: 空配列
    rows.append(mk(shared_user_ids=[], temp_data=json.dumps(
        {"metainfo": {"shared_user_ids": []}})))
    # A7: owner・shared_user_ids キーなし
    rows.append(mk(temp_data=json.dumps({"metainfo": {}})))
    # A8: JSON の null
    a8 = mk(temp_data=json.dumps({"metainfo": {"shared_user_ids": None}}))
    set_raw_json(a8.activity_id, "shared_user_ids", "null")
    rows.append(a8)
    # A9: JSON オブジェクト
    a9 = mk(temp_data=json.dumps({"metainfo": {"shared_user_ids": {"foo": 1}}}))
    set_raw_json(a9.activity_id, "shared_user_ids", '{"foo": 1}')
    rows.append(a9)
    # A10: JSON 文字列
    a10 = mk(temp_data=json.dumps({"metainfo": {"shared_user_ids": "x"}}))
    set_raw_json(a10.activity_id, "shared_user_ids", '"x"')
    rows.append(a10)
    # A11: 展開後が JSON の null
    rows.append(mk(temp_data=json.dumps(None)))
    # A12: 展開後が JSON の文字列
    rows.append(mk(temp_data=json.dumps("abc")))
    row_ids = {r.activity_id for r in rows}

    # 3 タブとも例外が発生せず(cannot get array length of a non-array を含む)、
    # いずれの行も代理投稿者・owner 条件で一覧に含まれない
    for tab in ("wait", "all", "todo"):
        found = list_activity_ids(tab, env.U_P1)
        assert not (row_ids & found)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_role_condition -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_role_condition(app, db, users, workflow):
    """所属ロールが shared_role_ids に含まれるアクティビティが一覧に含まれる."""
    env = build_proxy_env(app)
    set_proxy_posting(app, True)
    r_l = create_role_with_id_prefix(env.R_A)
    assert rid(r_l).startswith(rid(env.R_A)) and rid(r_l) != rid(env.R_A)
    mk = lambda **kw: create_proxy_activity(workflow, env.U_O, **kw)
    a8 = mk(shared_role_ids=[rid(env.R_A)])
    a9 = mk(shared_role_ids=None, temp_data=json.dumps(
        {"metainfo": {"shared_role_ids": [rid(env.R_A)]}}))
    a9o = mk(shared_role_ids=None, temp_data={
        "metainfo": {"shared_role_ids": [rid(env.R_A)]}})
    a10 = mk(shared_role_ids=[rid(r_l)])
    a10t = mk(shared_role_ids=None, temp_data=json.dumps(
        {"metainfo": {"shared_role_ids": [rid(r_l)]}}))

    for tab in ("all", "todo"):
        found = list_activity_ids(tab, env.U_G)
        assert {a8.activity_id, a9.activity_id, a9o.activity_id} <= found
        # json.dumps(rid) による引用符付きの比較で、"1" が "12" に誤一致しない
        assert not ({a10.activity_id, a10t.activity_id} & found)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_role_condition_not_applied -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_role_condition_not_applied(app, db, users, workflow):
    """ロールなし・複数化フラグ無効・NULL の行はロール条件で一覧に含まれない."""
    env = build_proxy_env(app)
    app.config["WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY"] = False
    mk = lambda **kw: create_proxy_activity(workflow, env.U_O, **kw)
    a8 = mk(shared_role_ids=[rid(env.R_A)])
    a9 = mk(shared_role_ids=None, temp_data=json.dumps(
        {"metainfo": {"shared_role_ids": [rid(env.R_A)]}}))
    role_cond_sql = "CAST(workflow_activity.shared_role_ids"

    # 1. 複数化フラグ有効・ロールなし(U_N)
    set_proxy_posting(app, True)
    for tab in ("wait", "all", "todo"):
        found = list_activity_ids(tab, env.U_N)
        assert not ({a8.activity_id, a9.activity_id} & found)
    for func_name, _ in _ALL_FUNCS:
        sql = compile_sql(build_func_query(func_name, env.U_N))
        assert role_cond_sql not in sql
        assert "{metainfo,shared_role_ids}" not in sql

    # 2. 複数化フラグ無効・ロールあり(U_G)
    set_proxy_posting(app, False)
    for tab in ("wait", "all", "todo"):
        found = list_activity_ids(tab, env.U_G)
        assert not ({a8.activity_id, a9.activity_id} & found)
    for func_name, _ in _ALL_FUNCS:
        sql = compile_sql(build_func_query(func_name, env.U_G))
        assert role_cond_sql not in sql
        assert "{metainfo,shared_role_ids}" not in sql

    # 3. shared_role_ids が NULL で temp_data にもロールを持たない行 A11
    set_proxy_posting(app, True)
    a11 = mk(shared_role_ids=None, temp_data=json.dumps({"metainfo": {}}))
    for tab in ("all", "todo"):
        assert a11.activity_id not in list_activity_ids(tab, env.U_G)

    # 4. __get_self_role_ids
    get_roles = WorkActivity._WorkActivity__get_self_role_ids
    with patch("flask_login.utils._get_user", return_value=env.U_G):
        assert get_roles() == [rid(env.R_A)]
    with patch("flask_login.utils._get_user", return_value=env.U_N):
        assert get_roles() == []
    set_proxy_posting(app, False)
    with patch("flask_login.utils._get_user", return_value=env.U_G):
        assert get_roles() == []

    # 5. __is_shared_role([]) は false() を返す(coalesce で包まれない)
    result = WorkActivity._WorkActivity__is_shared_role([])
    assert isinstance(result, False_)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_role_condition_sql -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_role_condition_sql(app, db, users):
    """ロール条件が 9 箇所に追加され、引用符付き比較・ESCAPE となる."""
    from .helpers_proxy import create_user
    env = build_proxy_env(app)
    app.config["WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY"] = False
    set_proxy_posting(app, True)
    user = create_user("proxy_two_roles@test.org", [env.R_A, env.R_B])
    expanded = _expanded_temp_data()

    for func_name, n in _ALL_FUNCS:
        sql = compile_sql(build_func_query(func_name, user))
        # 所属ロール数(2)だけ、カラムの文字列化と temp_data の条件が OR で連結される
        assert sql.count("CAST(workflow_activity.shared_role_ids AS VARCHAR)") == 2 * n
        assert sql.count(
            expanded + " #>> '{metainfo,shared_role_ids}'") == 2 * n
        # 比較値はダブルクォート付き
        for role in (env.R_A, env.R_B):
            assert sql.count("'\"%s\"'" % rid(role)) == 2 * n
        # autoescape による ESCAPE 句(カラム・temp_data × 2 ロール)
        assert sql.count("ESCAPE '/'") == 4 * n
        # OR で連結した式全体が coalesce(..., false) で包まれている
        assert sql.count(
            "coalesce((CAST(workflow_activity.shared_role_ids AS VARCHAR) LIKE") == n
        assert sql.count(", false)") >= n


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_role_condition_null_wait -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_role_condition_null_wait(app, db, users, workflow):
    """shared_role_ids が NULL の旧行などがタブ「Wait」から落ちない."""
    env = build_proxy_env(app)
    app.config["WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY"] = False
    set_proxy_posting(app, True)
    r_l = create_role_with_id_prefix(env.R_A)
    # タブ「Wait」の他の条件を、ロール条件に影響されない形で満たすため、
    # U_G の所属しないロールを持つ FlowActionRole をアイテム登録アクションに追加する
    add_flow_action_role(workflow, 3, 2, action_role=r_l.id)

    other = [{"user": env.U_P2.id}]

    def temp(**metainfo_extra):
        metainfo = {"owner": str(env.U_O.id), "shared_user_ids": other}
        metainfo.update(metainfo_extra)
        return json.dumps({"metainfo": metainfo})

    def make_rows(login_user):
        """擬似行 A〜F を作成する(shared_role_ids の組み合わせ)."""
        mk = lambda **kw: create_proxy_activity(
            workflow, login_user, shared_user_ids=other, **kw)
        return dict(
            # A: shared_role_ids が NULL の旧行(ロール条件の両項が NULL)
            A=mk(shared_role_ids=None, temp_data=temp()),
            # B: カラム側で該当
            B=mk(shared_role_ids=[rid(env.R_A)], temp_data=temp()),
            # C: temp_data 側で該当
            C=mk(shared_role_ids=None, temp_data=temp(shared_role_ids=[rid(env.R_A)])),
            # D: カラムが空配列
            D=mk(shared_role_ids=[], temp_data=temp()),
            # E: temp_data が空配列
            E=mk(shared_role_ids=None, temp_data=temp(shared_role_ids=[])),
            # F: U_G が所属しない別ロール
            F=mk(shared_role_ids=[rid(r_l)], temp_data=temp()),
        )

    def ids_of(rows, *names):
        return {rows[name].activity_id for name in names}

    # 1・3. タブ「Wait」は、U_G が申請者の行で確認する(ロール条件以外の条件を満たす)
    rows_g = make_rows(env.U_G)
    found = list_activity_ids("wait", env.U_G)
    # 1. A・D・E・F は coalesce により偽に正規化されて落ちない。B・C はロール該当のため除外
    assert ids_of(rows_g, "A", "D", "E", "F") <= found
    assert not (ids_of(rows_g, "B", "C") & found)

    # 3. 複数化フラグ無効: ロール条件が false() となり、B・C も除外されない
    set_proxy_posting(app, False)
    found = list_activity_ids("wait", env.U_G)
    assert ids_of(rows_g, "A", "B", "C", "D", "E", "F") <= found
    set_proxy_posting(app, True)

    # 2. All タブ・Todo タブでは B・C のみ含まれる
    #    (申請者(activity_login_user)が U_G の行は申請者条件で含まれるため、申請者を U_O とした行で確認する)
    rows_o = make_rows(env.U_O)
    for tab in ("all", "todo"):
        found = list_activity_ids(tab, env.U_G)
        assert ids_of(rows_o, "B", "C") <= found
        assert not (ids_of(rows_o, "A", "D", "E", "F") & found)

    # 4. ロールを持たない U_N: ロール条件が false() となり、B'・C' も除外されない
    rows_n = make_rows(env.U_N)
    found = list_activity_ids("wait", env.U_N)
    assert ids_of(rows_n, "A", "B", "C", "D", "E", "F") <= found


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_is_shared_role_coalesce -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_shared_role_coalesce(app, db, users, workflow):
    """__is_shared_role の戻り値が coalesce(or_(...), false()) で NULL とならない."""
    env = build_proxy_env(app)
    app.config["WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY"] = False
    set_proxy_posting(app, True)
    r_l = create_role_with_id_prefix(env.R_A)
    other = [{"user": env.U_P2.id}]

    def temp(**metainfo_extra):
        metainfo = {"owner": str(env.U_O.id), "shared_user_ids": other}
        metainfo.update(metainfo_extra)
        return json.dumps({"metainfo": metainfo})

    mk = lambda **kw: create_proxy_activity(
        workflow, env.U_O, shared_user_ids=other, **kw)
    rows = dict(
        A=mk(shared_role_ids=None, temp_data=temp()),
        B=mk(shared_role_ids=[rid(env.R_A)], temp_data=temp()),
        C=mk(shared_role_ids=None, temp_data=temp(shared_role_ids=[rid(env.R_A)])),
        D=mk(shared_role_ids=[], temp_data=temp()),
        E=mk(shared_role_ids=None, temp_data=temp(shared_role_ids=[])),
        F=mk(shared_role_ids=[rid(r_l)], temp_data=temp()),
    )
    is_shared_role = WorkActivity._WorkActivity__is_shared_role
    role_ids = [rid(env.R_A), rid(env.R_B)]

    # 1. 最外が coalesce(...) で、第 2 引数が false
    expr = is_shared_role(role_ids)
    sql = compile_sql(expr)
    assert sql.startswith("coalesce(")
    assert sql.endswith(", false)")
    assert sql.count("CAST(workflow_activity.shared_role_ids AS VARCHAR)") == 2
    assert sql.count(
        _expanded_temp_data() + " #>> '{metainfo,shared_role_ids}'") == 2
    for role_id in role_ids:
        assert "'\"%s\"'" % role_id in sql

    # 2. ロール条件が空のときは false()(coalesce で包まない)
    assert isinstance(is_shared_role([]), False_)

    # 3. 行ごとの値(NULL にならない)
    values = dict(db.session.query(_Activity.activity_id, expr).all())
    for name in ("A", "D", "E", "F"):
        assert values[rows[name].activity_id] is False
    for name in ("B", "C"):
        assert values[rows[name].activity_id] is True

    # 4. not_() で包んでも NULL にならない
    values = dict(db.session.query(_Activity.activity_id, not_(expr)).all())
    for name in ("A", "D", "E", "F"):
        assert values[rows[name].activity_id] is True
    for name in ("B", "C"):
        assert values[rows[name].activity_id] is False

    # 5. 3 関数の生成 SQL: ロール条件のみ coalesce で包まれる
    for func_name, n in _ALL_FUNCS:
        sql = compile_sql(build_func_query(func_name, env.U_G))
        assert sql.count("coalesce(") == n
        assert sql.count(
            "coalesce((CAST(workflow_activity.shared_role_ids AS VARCHAR) LIKE") == n
        # owner・temp_data 側の shared_user_ids の条件は coalesce で包まれない
        assert "coalesce(" + _expanded_temp_data() not in sql
        assert "coalesce(CAST(workflow_activity.shared_user_ids" not in sql


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_shared_role_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_shared_role_ids(app, db, users, item_type, workflow, caplog):
    """init_activity が shared_role_ids を検証せずカラムへ保存する."""
    env = build_proxy_env(app)
    groups = create_group_roles(11)
    set_proxy_posting(app, True)
    role_deleted = "999999"
    base = {"workflow_id": workflow["workflow"].id,
            "flow_id": workflow["flow"].id}

    def run(**extra):
        activity = WorkActivity().init_activity(dict(base, **extra))
        return Activity.query.filter_by(
            activity_id=activity.activity_id).one()

    with app.test_request_context():
        login_user(users[2]["obj"])
        caplog.set_level(logging.WARNING)

        # 1. shared_user_ids と shared_role_ids の保存
        saved = run(shared_user_ids=[{"user": env.U_P1.id}],
                    shared_role_ids=[rid(env.R_A)])
        assert saved.shared_role_ids == [rid(env.R_A)]
        assert saved.shared_user_ids == [{"user": env.U_P1.id}]

        # 2. キーなし -> NULL
        assert run().shared_role_ids is None

        # 3. None -> NULL
        assert run(shared_role_ids=None).shared_role_ids is None

        # 4. 指定不可となったロール: 検証せず保存し、拒否ログも出力しない
        caplog.clear()
        saved = run(shared_role_ids=[rid(env.R_X)])
        assert saved.shared_role_ids == [rid(env.R_X)]
        assert "Rejected shared role id" not in caplog.text

        # 5. 上限(10)を超える 11 件でも拒否しない
        ids = [rid(g) for g in groups]
        assert len(ids) == 11
        assert run(shared_role_ids=ids).shared_role_ids == ids

        # 6. 存在しないロールID
        assert run(shared_role_ids=[role_deleted]).shared_role_ids == [role_deleted]

        # 7. 複数化フラグ無効でも init_activity は複数化フラグを参照しない
        set_proxy_posting(app, False)
        assert run(shared_role_ids=[rid(env.R_A)]).shared_role_ids == [rid(env.R_A)]


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_params_for_registrant_actor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_params_for_registrant_actor(app, db, users, db_records, caplog):
    """actor が操作者のまま維持され、宛先が代理投稿者(個人)のみとなる."""
    env = build_proxy_env(app)
    caplog.set_level(logging.WARNING)

    def make_activity(update_user):
        return MagicMock(
            activity_login_user=env.U_O.id,
            activity_update_user=update_user,
            shared_user_ids=[{"user": env.U_P1.id}, {"user": env.U_P2.id}],
            shared_role_ids=[rid(env.R_A)],
            item_id=db_records[2][2].id,
        )

    def get_params(activity):
        with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_profile:
            mock_profile.side_effect = lambda uid: MagicMock(
                username="name_{}".format(uid))
            result = WorkActivity()._get_params_for_registrant(activity)
            return result, mock_profile

    # 1. 登録者が操作(複数化フラグ有効)
    set_proxy_posting(app, True)
    (targets, recid, actor_id, actor_name), mock_profile = get_params(
        make_activity(env.U_O.id))
    assert actor_id == env.U_O.id  # shared_user_ids[0] に上書きされない
    assert targets == {env.U_P1.id, env.U_P2.id}
    assert actor_name == "name_{}".format(env.U_O.id)
    assert env.U_G.id not in targets
    assert recid == db_records[2][0]

    # 2. 代理投稿者が操作
    (targets, recid, actor_id, actor_name), mock_profile = get_params(
        make_activity(env.U_P2.id))
    assert actor_id == env.U_P2.id
    assert targets == {env.U_O.id, env.U_P1.id}
    assert actor_name == "name_{}".format(env.U_P2.id)
    assert env.U_G.id not in targets

    # 3. 複数化フラグ無効: 宛先は末尾 1 名のみ
    set_proxy_posting(app, False)
    (targets, recid, actor_id, actor_name), mock_profile = get_params(
        make_activity(env.U_O.id))
    assert actor_id == env.U_O.id
    assert targets == {env.U_P2.id}
    assert env.U_G.id not in targets

    # 4. 操作者が特定できない場合は activity_login_user にフォールバック
    set_proxy_posting(app, True)
    caplog.clear()
    (targets, recid, actor_id, actor_name), mock_profile = get_params(
        make_activity(None))
    assert actor_id == env.U_O.id
    assert targets == {env.U_P1.id, env.U_P2.id}
    assert ("Actor id is not resolved for notification. "
            "Fallback to activity_login_user.") in caplog.text


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_params_for_approver_actor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_params_for_approver_actor(app, db, users, db_register_full_action, db_records, db_user_profile, caplog):
    """actor が代理投稿者配列の先頭に上書きされない."""
    env = build_proxy_env(app)
    set_proxy_posting(app, True)
    caplog.set_level(logging.WARNING)
    flow_define = db_register_full_action["flow_define"]

    def make_activity(update_user):
        return MagicMock(
            activity_login_user=env.U_O.id,
            activity_update_user=update_user,
            shared_user_ids=[{"user": env.U_P1.id}, {"user": env.U_P2.id}],
            shared_role_ids=[rid(env.R_A)],
            activity_community_id=None,
            item_id=db_records[2][2].id,
            flow_define=flow_define,
            action_order=3,
        )

    activity = WorkActivity()
    with patch("weko_workflow.api.UserProfile.get_by_userid") as mock_profile:
        mock_profile.side_effect = lambda uid: MagicMock(username="name_{}".format(uid))
        # 1. 代理投稿者配列の先頭(U_P1)ではなく、操作者が actor となる
        targets, recid, actor_id, actor_name = activity._get_params_for_approver(
            make_activity(env.U_O.id))
        assert actor_id == env.U_O.id
        assert actor_id != env.U_P1.id
        assert actor_name == "name_{}".format(env.U_O.id)
        assert env.U_G.id not in targets

        # 2. 操作者が特定できない場合は activity_login_user にフォールバック
        caplog.clear()
        targets, recid, actor_id, actor_name = activity._get_params_for_approver(
            make_activity(None))
        assert actor_id == env.U_O.id
        assert ("Actor id is not resolved for notification. "
                "Fallback to activity_login_user.") in caplog.text
