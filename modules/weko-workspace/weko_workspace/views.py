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

"""Blueprint for weko-workspace."""

import json
import os
import re
import shutil
import sys
import traceback
import requests
import copy

from collections import OrderedDict
from datetime import datetime
from functools import wraps
from typing import List

from flask import (
    Response,
    Blueprint,
    abort,
    current_app,
    has_request_context,
    jsonify,
    make_response,
    render_template,
    request,
    session,
    url_for,
    send_file,
)
from flask_babelex import gettext as _
from flask_login import current_user, login_required

from weko_admin.models import AdminSettings
from weko_workflow.api import WorkActivity, WorkFlow
from weko_workflow.errors import InvalidInputRESTError
from weko_items_ui.utils import is_schema_include_key
from flask_wtf import FlaskForm
from weko_workflow.utils import auto_fill_title, is_show_autofill_metadata, \
    is_hidden_pubdate, get_activity_display_info, get_cache_data
# get_cinii_record_data, \
#     get_jalc_record_data, get_datacite_record_data
from weko_workflow.models import ActionStatusPolicy
from weko_workflow.views import check_authority_action
from weko_user_profiles.views import get_user_profile_info
from weko_records_ui.utils import get_list_licence
from weko_accounts.utils import login_required_customize



from .utils import *

workspace_blueprint = Blueprint(
    "weko_workspace",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/workspace",
)

blueprint_itemapi = Blueprint(
    "weko_workspace_api",
    __name__,
    url_prefix="/workspaceAPI",
)

# 2.1. アイテム一覧情報取得API
@workspace_blueprint.route("/")
@login_required
def get_workspace_itemlist():
    print("==========guan.shuang workspace start=========")

    # 変数初期化
    # 　JSON条件
    # jsonCondition = {"name": "Alice", "age": 25, "is_student": False}
    workspaceItemList = []

    # 1,デフォルト絞込み条件取得処理
    # reqeustからのパラメータを確認する。
    # パラメータなし、1,デフォルト絞込み条件取得処理へ。
    # パラメータあり、1,デフォルト絞込み条件取得処理をスキップ。
    if request.args:
        jsonCondition = request.args.to_dict()
    else:
        # 1,デフォルト絞込み条件取得処理
        jsonCondition = get_workspace_filterCon()

    # 2,ESからアイテム一覧取得処理
    records_data = get_es_itemlist(jsonCondition)
    # →ループ処理
    for hit in records_data["hits"]["hits"]:

        workspaceItem = copy.deepcopy(current_app.config["WEKO_WORKSPACE_ITEM"])

        # "recid": None,  # レコードID
        recid = hit["id"]
        workspaceItem["recid"] = str(recid)
        print(f"recid : {recid}")

        # "title": None,  # タイトル
        workspaceItem["title"] = hit["metadata"].get("title", [])[0]
        print("title : " + workspaceItem["title"])

        # "favoriteSts": None,  # お気に入りステータス状況
        workspaceItem["favoriteSts"] = get_workspace_status_management(recid)[0] if get_workspace_status_management(recid) else False
        print("favoriteSts : " + str(workspaceItem["favoriteSts"]))

        # "readSts": None,  # 既読未読ステータス状況
        workspaceItem["readSts"] = get_workspace_status_management(recid)[1] if get_workspace_status_management(recid) else False
        print("readSts : " + str(workspaceItem["readSts"]))

        # TODO "peerReviewSts": None,  # 査読チェック状況

        # "doi": None,  # DOIリンク
        identifiers = hit["metadata"].get("identifier", [])
        if identifiers:
            workspaceItem["doi"] = identifiers[0].get("value", "")
        else:
            workspaceItem["doi"] = ""
        print(f"workspaceItem[doi] : {workspaceItem['doi']}")

        # "resourceType": None,  # リソースタイプ
        workspaceItem["resourceType"] = hit["metadata"].get("type", [])[0]
        print(f"resourceType : {hit['metadata'].get('type', [])[0]}")

        #  "authorlist": None,   著者リスト[著者名]
        workspaceItem["authorlist"] = hit["metadata"]["creator"]["creatorName"] if "creator" in hit["metadata"] and hit["metadata"]["creator"]["creatorName"] else None
        if workspaceItem["authorlist"] is not None:
            workspaceItem["authorlist"].append("作成者02")
            workspaceItem["authorlist"].append("作成者03")
        print("authorlist : " + str(workspaceItem["authorlist"]))

        # "accessCnt": None,  # アクセス数
        workspaceItem["accessCnt"] = get_accessCnt_downloadCnt(recid)[0]
        print("accessCnt : " + str(workspaceItem["accessCnt"]))

        # "downloadCnt": None,  # ダウンロード数
        workspaceItem["downloadCnt"] = get_accessCnt_downloadCnt(recid)[1]
        print("downloadCnt : " + str(workspaceItem["downloadCnt"]))

        # "itemStatus": None,  # アイテムステータス
        workspaceItem["itemStatus"] = get_item_status(recid)
        print("itemStatus : " + str(workspaceItem["itemStatus"]))

        # "publicationDate": None,  # 出版年月日
        workspaceItem["publicationDate"] = hit["metadata"]["publish_date"]
        print(f"publicationDate : " + workspaceItem["publicationDate"])

        # "magazineName": None,  # 雑誌名
        workspaceItem["magazineName"] = hit["metadata"]["sourceTitle"][0] if "sourceTitle" in hit["metadata"] else None
        print("magazineName : "  + str(workspaceItem["magazineName"]))

        # "conferenceName": None,  # 会議名
        conference = hit["metadata"].get("conference", [])
        if conference and conference["conferenceName"]:
            workspaceItem["conferenceName"] = conference["conferenceName"][0]
        else:
            workspaceItem["conferenceName"] = None

        print("conferenceName : " + str(workspaceItem["conferenceName"]))

        # "volume": None,  # 巻
        workspaceItem["volume"] = (
            hit["metadata"].get("volume", [])[0]
            if hit["metadata"].get("volume", [])
            else None
        )
        print("volume : " + str(workspaceItem["volume"]))

        # "issue": None,  # 号
        workspaceItem["issue"] = (
            hit["metadata"].get("issue", [])[0]
            if hit["metadata"].get("issue", [])
            else None
        )
        print("issue : " + str(workspaceItem["issue"]))

        # "funderName": None,  # 資金別情報機関名
        fundingReference = hit["metadata"].get("fundingReference", [])
        if fundingReference and fundingReference["funderName"]:
            workspaceItem["funderName"] = fundingReference["funderName"][0]
        else:
            workspaceItem["funderName"] = None

        print("funderName : " + str(workspaceItem["funderName"]))

        # "awardTitle": None,  # 資金別情報課題名
        if fundingReference and fundingReference["awardTitle"]:
            workspaceItem["awardTitle"] = fundingReference["awardTitle"][0]
        else:
            workspaceItem["awardTitle"] = None

        print("awardTitle : " + str(workspaceItem["awardTitle"]))

        # TODO "fbEmailSts": None,  # フィードバックメールステータス
        # ①ログインユーザーのメールアドレスは2.1.2.2の
        # 取得結果の著者リストに存在すればtrueを設定する。逆にfalse。
        # ②2.1.2.2の取得結果のアイテムID(_id)でfeedback_mail_listテーブルのmail_list項目を取得して、
        # ログインユーザーのメールアドレスは該当リストに存在すればtrueを設定する。逆にfalse。
        workspaceItem["fbEmailSts"] = False if current_user.email else False
        print("fbEmailSts : " + str(workspaceItem["fbEmailSts"]))

        # "connectionToPaperSts": None,  # 論文への関連チェック状況
        # "connectionToDatasetSts": None,  # 根拠データへの関連チェック状況

        # "relation": None,  # 関連情報リスト
        relations = []
        relationLen = len(hit["metadata"]["relation"]["relatedTitle"]) if "relation" in hit["metadata"] else None
        print("relationLen : " + str(relationLen))

        if "relation" in hit["metadata"]:
            for i in range(relationLen):
                # "relationType": None,  # 関連情報タイプ
                workspaceItem["relationType"] = hit["metadata"].get("relation", [])["@attributes"]["relationType"][i][0]
                # print("relationType : " + hit["metadata"].get("relation", [])["@attributes"]["relationType"][i][0])

                # # "relationTitle": None,  # 関連情報タイトル
                workspaceItem["relationTitle"] = hit["metadata"].get("relation", [])["relatedTitle"][i]
                # print("relationTitle : " + hit["metadata"].get("relation", [])["relatedTitle"][i])

                # # "relationUrl": None,  # 関連情報URLやDOI
                workspaceItem["relationUrl"] = hit["metadata"].get("relation", [])["relatedIdentifier"][i]["value"]
                # print("relationUrl : "+ hit["metadata"].get("relation", [])["relatedIdentifier"][i]["value"])

                relation = {
                    "relationType": workspaceItem["relationType"],
                    "relationTitle": workspaceItem["relationTitle"],
                    "relationUrl": workspaceItem["relationUrl"],    
                }
                relations.append(relation)

        workspaceItem["relation"] = relations
        print("relation : " + str(workspaceItem["relation"]))

        # file情報
        print("file : ")
        fileObjNm = "item_" + hit["metadata"]["_item_metadata"]["item_type_id"] + "_file"
        fileObjNm = [key for key in hit["metadata"]["_item_metadata"].keys() if key.startswith(fileObjNm)]

        if fileObjNm is not None and len(fileObjNm) > 0:
            file = fileObjNm[0]

            fileList = []
            fileList = hit["metadata"].get("_item_metadata", [])[file]["attribute_value_mlt"]

            publicCnt = 0
            embargoedCnt = 0
            restrictedPublicationCnt = 0

            fileCnt = len(fileList)
            if fileCnt > 0:
                # "fileSts": None,  # 本文ファイル有無ステータス
                workspaceItem["fileSts"] = True
                print("fileSts : " + str(workspaceItem["fileSts"]))

                # "fileCnt": None,  # 本文ファイル数
                workspaceItem["fileCnt"] = fileCnt
                print("fileCnt : " + str(workspaceItem["fileCnt"]))

                accessrole_date_list = [
                    {
                        "accessrole": item["accessrole"],
                        "dateValue": item["date"][0]["dateValue"],
                    }
                    for item in fileList
                    if "accessrole" in item and "date" in item
                ]
                # print("accessrole_date_list : ")
                # print(accessrole_date_list)

                for accessrole_date in accessrole_date_list:
                    # print("accessrole : " + accessrole_date["accessrole"])
                    # print("dateValue : " + accessrole_date["dateValue"])

                    # "publicSts": None,  # 公開ファイル有無ステータス
                    # "publicCnt": None,  # 公開ファイル数
                    if accessrole_date["dateValue"] <= hit["metadata"]["publish_date"]:
                        publicCnt += 1

                    # "embargoedSts": None,  # エンバーゴ有無ステータス
                    # "embargoedCnt": None,  # エンバーゴ有数
                    if accessrole_date["dateValue"] > datetime.now().strftime("%Y%m%d"):
                        embargoedCnt += 1

                    # "restrictedPublicationSts": None,  # 制限公開有無ステータス
                    # "restrictedPublicationCnt": None,  # 制限公開ファイル数
                    if accessrole_date["accessrole"] == "open_access":
                        restrictedPublicationCnt += 1
            else:
                workspaceItem["fileSts"] = False
                workspaceItem["fileCnt"] = 0

        workspaceItem["publicCnt"] = publicCnt
        workspaceItem["embargoedCnt"] = embargoedCnt
        workspaceItem["restrictedPublicationCnt"] = restrictedPublicationCnt
        print("publicCnt : " + str(workspaceItem["publicCnt"]))
        print("embargoedCnt : " + str(workspaceItem["embargoedCnt"]))
        print("restrictedPublicationCnt : " + str(workspaceItem["restrictedPublicationCnt"]))

        if str(workspaceItem):
            workspaceItemList.append(workspaceItem)
        print("------------------------------------")

    # 7,ユーザー名と所属情報取得処理
    userInfo = get_userNm_affiliation()
    # print(userInfo[0])
    # print(userInfo[1])

    print("========workspaceItem end ========")

    print("==========guan.shuang workspace end=========")

    return render_template(
        current_app.config["WEKO_WORKSPACE_BASE_TEMPLATE"],
        username=userInfo[0],
        affiliation=userInfo[1],
        workspaceItemList=workspaceItemList,
    )


# 2.2. お気に入り既読未読ステータス更新API
@workspace_blueprint.route("/updateStatus")
@login_required
def update_workspace_status_management(statusTyp):
    return None


# 2.1. デフォルト絞込み条件更新API
@workspace_blueprint.route("/updateDefaultConditon")
@login_required
def update_workspace_default_conditon(buttonTyp, default_con):
    return None




# itemRegistration登録 ri 20250113 start
@workspace_blueprint.route('/item_registration', endpoint='itemregister')
@login_required
def itemregister():
        
    print("========== workspace item_register =========")
    need_billing_file = False
    need_file = False
    need_thumbnail = False
    settings = AdminSettings.get('workspace_workflow_settings')
    if settings.workFlow_select_flg == '0':
        # activity_id = WorkActivity().get_new_activity_id(),

        workflow = WorkFlow()
        workflow_detail = workflow.get_workflow_by_id(settings.work_flow_id)
        
        item_type = ItemTypes.get_by_id(workflow_detail.itemtype_id)
        user_id = current_user.id if hasattr(current_user , 'id') else None
        user_profile = None
        if user_id:
            
            user_profile={}
            user_profile['results'] = get_user_profile_info(int(user_id))
        activity = WorkActivity()
        post_activity = {
            'flow_id': workflow_detail.flow_id,
            'itemtype_id': workflow_detail.itemtype_id,
            'workflow_id': workflow_detail.id
        }

        # 保留
        try:
            rtn = activity.init_activity(post_activity)
            activity_id = rtn.activity_id
        except Exception as ex:
            current_app.logger.info('init_activity', str(ex))
            raise InvalidInputRESTError()


        if item_type is None:
            return render_template('weko_items_ui/iframe/error.html',
                                    error_type='no_itemtype'),404
        need_file, need_billing_file = is_schema_include_key(item_type.schema)


        json_schema = '/items/jsonschema/{}'.format(workflow_detail.itemtype_id)
        schema_form = '/items/schemaform_simple/{}'.format(workflow_detail.itemtype_id)
        record = {}
        files = []
        # need_billing_file = []
        # need_file = []
        endpoints = {}
        if "subitem_thumbnail" in json.dumps(item_type.schema):
            need_thumbnail = True

        form = FlaskForm(request.form)
        institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
        position_list = WEKO_USERPROFILES_POSITION_LIST
        
        list_license = get_list_licence()
        # ctx={'community': None, 'record_org': [], 'files_org': [], 'thumbnails_org': [], 'files_thumbnail': [], 'files': [], 'record': []}
        item_type_name = get_item_type_name(workflow_detail.itemtype_id)
        title = auto_fill_title(item_type_name)
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)
        is_hidden_pubdate_value = is_hidden_pubdate(item_type_name)


        #index
        # from invenio_records_rest.utils import obj_or_import_string
        # ctx = dict(
        #     'read_permission_factory': <Permission needs={Need(method='role', value='Repository Administrator'), Need(method='action', value='superuser-access'), Need(method='role', value='System Administrator'), Need(method='action', value='index-tree-access'), Need(method='role', value='Community Administrator')} excludes=set()>, 'create_permission_factory': <Permission needs={Need(method='role', value='Repository Administrator'), Need(method='action', value='superuser-access'), Need(method='role', value='System Administrator'), Need(method='action', value='index-tree-access'), Need(method='role', value='Community Administrator')} excludes=set()>, 'update_permission_factory': <Permission needs={Need(method='role', value='Repository Administrator'), Need(method='action', value='superuser-access'), Need(method='role', value='System Administrator'), Need(method='action', value='index-tree-access'), Need(method='role', value='Community Administrator')} excludes=set()>, 'delete_permission_factory': <Permission needs={Need(method='role', value='Repository Administrator'), Need(method='action', value='superuser-access'), Need(method='role', value='System Administrator'), Need(method='action', value='index-tree-access'), Need(method='role', value='Community Administrator')} excludes=set()>, 
        #     'record_class': <class 'weko_index_tree.api.Indexes'>, 'loaders': {'application/json': <function create_blueprint.<locals>.<lambda> at 0x7f2865602950>}
        # )
        
        # from weko_theme.utils import get_design_layout, has_widget_design
        # from invenio_i18n.ext import current_i18n

        action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail = \
            get_activity_display_info(activity_id)

        user_lock_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
        if action_endpoint in ['item_login',
                            'item_login_application',
                            'file_upload']:
            if not activity.get_activity_by_id(activity_id):
                pass
            if activity.get_activity_by_id(activity_id).action_status != ActionStatusPolicy.ACTION_CANCELED:
                cur_locked_val = str(get_cache_data(user_lock_key)) or str()
                if not cur_locked_val:
                    activity_session = dict(
                        activity_id=activity_id,
                        action_id=activity_detail.action_id,
                        action_version=cur_action.action_version,
                        action_status=ActionStatusPolicy.ACTION_DOING,
                        commond=''
                    )
                    session['activity_info'] = activity_session

        # be use for index tree and comment page.
        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)

        approval_record = []
        is_auto_set_index_action = True
        recid = None
        community_id = ""
        res_check = check_authority_action(str(activity_id), int(action_id),
                                    is_auto_set_index_action,
                                    activity_detail.action_order)
        if 'item_login' == action_endpoint or \
                'item_login_application' == action_endpoint or \
                'file_upload' == action_endpoint:
            cur_locked_val = str(get_cache_data(user_lock_key)) or str()
            if not cur_locked_val:
                session['itemlogin_id'] = activity_id
                session['itemlogin_activity'] = activity_detail
                session['itemlogin_item'] = item
                session['itemlogin_steps'] = steps
                session['itemlogin_action_id'] = action_id
                session['itemlogin_cur_step'] = action_endpoint
                session['itemlogin_record'] = approval_record
                session['itemlogin_histories'] = histories
                session['itemlogin_res_check'] = res_check
                session['itemlogin_pid'] = recid
                session['itemlogin_community_id'] = community_id

        return render_template(
            'weko_workspace/item_register.html',
            # usage_type='Application',
            need_file=need_file,
            need_billing_file=need_billing_file,
            records=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=workflow_detail.itemtype_id,
            itemtype_id=workflow_detail.itemtype_id,
            files=files,
            # activity_id = 'A-20250130-00084',
            licences=current_app.config.get('WEKO_RECORDS_UI_LICENSE_DICT'),
            activity_id = activity_id,

            # render_header_footer=render_header_footer,

            institute_position_list=institute_position_list,
            position_list=position_list,
            # action_endpoint_key={},
            action_id=3,
            # activity='Activity 11',
            endpoints=endpoints,
            # allow_multi_thumbnail=False,
            # application_item_type=False,
            # approval_email_key=['parentkey.subitem_advisor_mail_address', 'parentkey.subitem_guarantor_mail_address'],
            # auto_fill_data_type=None,
            # auto_fill_title='',
            # community_id='',
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            # error_type='item_login_error',
            # idf_grant_data=None,
            # idf_grant_method=current_app.config.get(
            #     'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD),
            is_auto_set_index_action=True,
            # is_enable_item_name_link=True,
            item_save_uri='/items/iframe/model/save',
            # item=None,
            # links=None,
            # list_license=list_license,
            # need_thumbnail=False,
            # out_put_report_title=current_app.config[
            #     'WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE'],
            page=None,
            # pid=None,
            # _id=None,
            # render_widgets=False,
            # res_check=0,
            steps=steps,
            # temporary_comment=None,
            # temporary_idf_grant_suffix=[],
            # temporary_idf_grant=0,
            # temporary_journal=None,
            # term_and_condition_content='',
            # user_profile=user_profile,
            # auto_fill_title=title,
            # is_hidden_pubdate=is_hidden_pubdate_value,
            is_show_autofill_metadata=show_autofill_metadata,
            # render_widgets=render_widgets,
            form=form
        )


@blueprint_itemapi.route('/get_auto_fill_record_data_ciniiapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_ciniiapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    # api_type = data.get('api_type', '')
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')

    try:
        api_response = get_cinii_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


@blueprint_itemapi.route('/get_auto_fill_record_data_jalcapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_jalcapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')
    try:
        api_response = get_jalc_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


@blueprint_itemapi.route('/get_auto_fill_record_data_dataciteapi', methods=['POST'])
@login_required_customize
def get_auto_fill_record_data_dataciteapi():
    """Get auto fill record data.

    :return: record model as json
    """
    result = {
        'result': '',
        'items': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')
    try:
        api_response = get_datacite_record_data(
            search_data, item_type_id)
        result['result'] = api_response
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


# itemRegistration登録　ri 20250113 end
