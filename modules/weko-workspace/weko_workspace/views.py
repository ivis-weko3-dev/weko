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
from weko_workflow.headless.activity import HeadlessActivity
from weko_index_tree.models import Index
from flask_login import current_user

from .utils import *
from .models import *

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
@workspace_blueprint.route("/get_workspace_itemlist", methods=['GET'])
@login_required
def get_workspace_itemlist():
    print("==========guan.shuang get_workspace_itemlist start=========")

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
        # print(f"recid : {recid}")

        # "title": None,  # タイトル
        workspaceItem["title"] = hit["metadata"].get("title", [])[0]
        # print("title : " + workspaceItem["title"])

        # "favoriteSts": None,  # お気に入りステータス状況
        workspaceItem["favoriteSts"] = get_workspace_status_management(recid)[0] if get_workspace_status_management(recid) else False
        # print("favoriteSts : " + str(workspaceItem["favoriteSts"]))

        # "readSts": None,  # 既読未読ステータス状況
        workspaceItem["readSts"] = get_workspace_status_management(recid)[1] if get_workspace_status_management(recid) else False
        # print("readSts : " + str(workspaceItem["readSts"]))

        # TODO "peerReviewSts": None,  # 査読チェック状況

        # "doi": None,  # DOIリンク
        identifiers = hit["metadata"].get("identifier", [])
        if identifiers:
            workspaceItem["doi"] = identifiers[0].get("value", "")
        else:
            workspaceItem["doi"] = ""
        # print(f"workspaceItem[doi] : {workspaceItem['doi']}")

        # "resourceType": None,  # リソースタイプ
        workspaceItem["resourceType"] = hit["metadata"].get("type", [])[0]
        # print(f"resourceType : {hit['metadata'].get('type', [])[0]}")

        #  "authorlist": None,   著者リスト[著者名]
        workspaceItem["authorlist"] = hit["metadata"]["creator"]["creatorName"] if "creator" in hit["metadata"] and hit["metadata"]["creator"]["creatorName"] else None
        if workspaceItem["authorlist"] is not None:
            workspaceItem["authorlist"].append("作成者02")
            workspaceItem["authorlist"].append("作成者03")
        # print("authorlist : " + str(workspaceItem["authorlist"]))

        # "accessCnt": None,  # アクセス数
        workspaceItem["accessCnt"] = get_accessCnt_downloadCnt(recid)[0]
        # print("accessCnt : " + str(workspaceItem["accessCnt"]))

        # "downloadCnt": None,  # ダウンロード数
        workspaceItem["downloadCnt"] = get_accessCnt_downloadCnt(recid)[1]
        # print("downloadCnt : " + str(workspaceItem["downloadCnt"]))

        # "itemStatus": None,  # アイテムステータス
        workspaceItem["itemStatus"] = get_item_status(recid)
        # print("itemStatus : " + str(workspaceItem["itemStatus"]))

        # "publicationDate": None,  # 出版年月日
        workspaceItem["publicationDate"] = hit["metadata"]["publish_date"]
        # print(f"publicationDate : " + workspaceItem["publicationDate"])

        # "magazineName": None,  # 雑誌名
        workspaceItem["magazineName"] = hit["metadata"]["sourceTitle"][0] if "sourceTitle" in hit["metadata"] else None
        # print("magazineName : "  + str(workspaceItem["magazineName"]))

        # "conferenceName": None,  # 会議名
        conference = hit["metadata"].get("conference", [])
        if conference and conference["conferenceName"]:
            workspaceItem["conferenceName"] = conference["conferenceName"][0]
        else:
            workspaceItem["conferenceName"] = None

        # print("conferenceName : " + str(workspaceItem["conferenceName"]))

        # "volume": None,  # 巻
        workspaceItem["volume"] = (
            hit["metadata"].get("volume", [])[0]
            if hit["metadata"].get("volume", [])
            else None
        )
        # print("volume : " + str(workspaceItem["volume"]))

        # "issue": None,  # 号
        workspaceItem["issue"] = (
            hit["metadata"].get("issue", [])[0]
            if hit["metadata"].get("issue", [])
            else None
        )
        # print("issue : " + str(workspaceItem["issue"]))

        # "funderName": None,  # 資金別情報機関名
        fundingReference = hit["metadata"].get("fundingReference", [])
        if fundingReference and fundingReference["funderName"]:
            workspaceItem["funderName"] = fundingReference["funderName"][0]
        else:
            workspaceItem["funderName"] = None

        # print("funderName : " + str(workspaceItem["funderName"]))

        # "awardTitle": None,  # 資金別情報課題名
        if fundingReference and fundingReference["awardTitle"]:
            workspaceItem["awardTitle"] = fundingReference["awardTitle"][0]
        else:
            workspaceItem["awardTitle"] = None

        # print("awardTitle : " + str(workspaceItem["awardTitle"]))

        # TODO "fbEmailSts": None,  # フィードバックメールステータス
        # ①ログインユーザーのメールアドレスは2.1.2.2の
        # 取得結果の著者リストに存在すればtrueを設定する。逆にfalse。
        # ②2.1.2.2の取得結果のアイテムID(_id)でfeedback_mail_listテーブルのmail_list項目を取得して、
        # ログインユーザーのメールアドレスは該当リストに存在すればtrueを設定する。逆にfalse。
        workspaceItem["fbEmailSts"] = False if current_user.email else False
        # print("fbEmailSts : " + str(workspaceItem["fbEmailSts"]))

        # "connectionToPaperSts": None,  # 論文への関連チェック状況
        # "connectionToDatasetSts": None,  # 根拠データへの関連チェック状況

        # "relation": None,  # 関連情報リスト
        relations = []
        relationLen = len(hit["metadata"]["relation"]["relatedTitle"]) if "relation" in hit["metadata"] else None
        # print("relationLen : " + str(relationLen))

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
        # print("relation : " + str(workspaceItem["relation"]))

        # file情報
        # print("file : ")
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
                # print("fileSts : " + str(workspaceItem["fileSts"]))

                # "fileCnt": None,  # 本文ファイル数
                workspaceItem["fileCnt"] = fileCnt
                # print("fileCnt : " + str(workspaceItem["fileCnt"]))

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
        # print("publicCnt : " + str(workspaceItem["publicCnt"]))
        # print("embargoedCnt : " + str(workspaceItem["embargoedCnt"]))
        # print("restrictedPublicationCnt : " + str(workspaceItem["restrictedPublicationCnt"]))

        if str(workspaceItem):
            workspaceItemList.append(workspaceItem)
        # print("------------------------------------")

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


@workspace_blueprint.route("/updateStatus", methods=['POST'])
@login_required
def update_workspace_status_management():
    print("==========guan.shuang update_workspace_status_management start=========")
    data = request.get_json()

    user_id = current_user.id

    item_recid = data.get('itemRecid')  # 使用 itemRecid
    # print("item_recid : " + str(item_recid))

    favorite_sts = data.get('favoriteSts')
    # print("favorite_sts : " + str(favorite_sts))

    read_sts = data.get('readSts')
    # print("read_sts : " + str(read_sts))

    type = data.get('type')
    # print("type : " + str(type))

    result = get_workspace_status_management(item_recid)
    print("result : " + str(result))

    if not result:
        insert_workspace_status(
            user_id=user_id,
            recid=item_recid,
            is_favorited=data.get('favoriteSts', False) if type == '1' else False,
            is_read=data.get('readSts', False) if type == '2' else False
        )
    else:
        if type == '1':
            update_workspace_status(
                user_id=user_id,
                recid=item_recid,
                is_favorited=data.get('favoriteSts')
            )
        elif type == '2':
            update_workspace_status(
                user_id=user_id,
                recid=item_recid,
                is_read=data.get('readSts')
            )
        else:
            return jsonify({'success': False, 'message': 'Invalid type'}), 400

    return jsonify({'success': True})


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
        workflow = WorkFlow()
        workflow_detail = workflow.get_workflow_by_id(settings.work_flow_id)
        
        item_type = ItemTypes.get_by_id(workflow_detail.itemtype_id)
        user_id = current_user.id if hasattr(current_user , 'id') else None
        user_profile = None
        if user_id:
            
            user_profile={}
            user_profile['results'] = get_user_profile_info(int(user_id))

        if item_type is None:
            return render_template('weko_items_ui/iframe/error.html',
                                    error_type='no_itemtype'),404
        need_file, need_billing_file = is_schema_include_key(item_type.schema)


        json_schema = '/items/jsonschema/{}'.format(workflow_detail.itemtype_id)
        schema_form = '/items/schemaform_simple/{}'.format(workflow_detail.itemtype_id)
        record = {}
        files = []
        endpoints = {}

        form = FlaskForm(request.form)
        institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
        position_list = WEKO_USERPROFILES_POSITION_LIST
        
        item_type_name = get_item_type_name(workflow_detail.itemtype_id)
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)



        return render_template(
            'weko_workspace/item_register.html',
            need_file=need_file,
            need_billing_file=need_billing_file,
            records=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=workflow_detail.itemtype_id,
            itemtype_id=workflow_detail.itemtype_id,
            files=files,
            licences=current_app.config.get('WEKO_RECORDS_UI_LICENSE_DICT'),

            institute_position_list=institute_position_list,
            position_list=position_list,
            endpoints=endpoints,
            cur_step='item_login',
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],

            is_auto_set_index_action=True,
            item_save_uri='/items/iframe/model/save',
            page=None,

            is_show_autofill_metadata=show_autofill_metadata,
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


@workspace_blueprint.route('/workflow_registration', methods=['POST'])
@login_required
def itemregister_save():
    # workflow_id = request_info.get("workflow_id")
    # when metadata format was XML, get id from admin setting
    # if workflow_id is None:
    #     settings = AdminSettings.get("sword_api_setting", dict_to_object=False)
    #     default_format = settings.get("default_format", "XML")
    #     data_format = settings.get("data_format")
    #     workflow_id = int(data_format.get(default_format, {}).get("workflow", "-1"))

    # metadata = item.get("metadata")
    # index = metadata.get("path")
    # files_info = metadata.pop("files_info", [{}])
    # files = [
    #     os.path.join(item.get("root_path"), file_info.get("url", {}).get("label"))
    #         for file_info
    #         in files_info[0].get("items", {})
    # ]
    # comment = metadata.get("comment")
    # link_data = item.get("link_data")
    # grant_data = item.get("grant_data")
    # item['path'] = ['1623632832836']
    # item['publish_status'] = 'public'
    result = {
        'result': '',
        'items': '',
        'error': ''
    }
    
    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    item = data.get('recordModel', '')
    grant_data = {}
    link_data = []
    comment = ""
    indexIdList = []
    files = item.get("item_30002_file35", [])
    settings = AdminSettings.get('workspace_workflow_settings')
    indexList = data.get('indexlist', '')
    for indexName in indexList:
        # indexs = Index().get_all()
        indexs = Index.query.filter_by(is_deleted=False).all()
        for index in indexs:
            if index.index_name == indexName or index.index_name_english == indexName:
                indexIdList.append(str(index.id))
    item['path'] = indexIdList
    index = indexIdList
    item['publish_status'] = '2'
    
    try:
        headless = HeadlessActivity()
        user_id=current_user.get_id()
        api_response = headless.auto(
            user_id= user_id, workflow_id=settings.work_flow_id,
            index=index, metadata=item, files=files, comment=comment,
            link_data=link_data, grant_data=grant_data
        )

        result['result'] = api_response
    except Exception as e:
        current_app.logger.info('itemregister_save', str(e))
        result['error'] = str(e)
    return jsonify(result)


# itemRegistration登録　ri 20250113 end
