# -*- coding: utf-8 -*-
"""代理投稿者・代理投稿グループのテスト用ヘルパー.

ユーザー・ロール・アクティビティを、テスト関数内でローカルに作成するための関数群。
共有フィクスチャ(users 等)は変更しない。
"""
import itertools
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from flask import current_app
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user
from invenio_db import db
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from weko_workflow.api import WorkActivity
from weko_workflow.models import Activity, FlowAction, FlowActionRole

# 学認 mAP 設定
MAP_IDP_ENTITY_ID = "https://idp.example.org/idp/shibboleth"
MAP_GROUP_PREFIX = "jc_idp_example_org_gr_"

# 未指定を表す番兵(temp_data を指定しない場合はモデルの既定値を使う)
UNSET = object()

_activity_seq = itertools.count(1)
_user_seq = itertools.count(1)


def enable_map(app):
    """学認 mAP 設定を有効にする(グループプレフィックスは MAP_GROUP_PREFIX)."""
    app.config["WEKO_ACCOUNTS_IDP_ENTITY_ID"] = MAP_IDP_ENTITY_ID


def disable_map(app):
    """学認 mAP 未設定とする."""
    app.config["WEKO_ACCOUNTS_IDP_ENTITY_ID"] = ""


def set_proxy_posting(app, enabled):
    """複数化フラグ(WEKO_ITEMS_UI_PROXY_POSTING)を設定する."""
    app.config["WEKO_ITEMS_UI_PROXY_POSTING"] = enabled


def rid(role):
    """ロールIDは常に str(role.id) の文字列で扱う."""
    return str(role.id)


def create_role(name, role_id=None):
    """ロールを作成する.

    Args:
        name (str): ロール名。
        role_id: 明示するロールID(未指定ならDBの採番)。
    """
    role = Role(name=name) if role_id is None else Role(id=role_id, name=name)
    db.session.add(role)
    db.session.commit()
    return role


def get_or_create_role(name):
    """名前でロールを取得し、無ければ作成する."""
    role = Role.query.filter_by(name=name).one_or_none()
    return role or create_role(name)


def create_role_with_id_prefix(base_role, suffix="2", name="jc_idp_example_org_gr_Long"):
    """ロールIDが base_role のIDを先頭に含む別ロールを作成する(例: "1" に対し "12")."""
    id_type = Role.id.type.python_type
    return create_role(name, role_id=id_type(rid(base_role) + suffix))


def create_user(email, roles=()):
    """ユーザーを作成し、ロールを付与する."""
    user = create_test_user(email=email)
    ds = current_app.extensions["invenio-accounts"].datastore
    for role in roles:
        ds.add_role_to_user(user, role)
    db.session.commit()
    return user


def build_proxy_env(app, with_roles_only=False):
    """共通ユーザー・ロールを作成する.

    ユーザーIDは作成順に増える(id(U_P1) < id(U_P2) < id(U_P3))。
    Role/User は呼び出しごとに新規作成するため、共有フィクスチャは変更しない。

    Returns:
        SimpleNamespace: R_A, R_a, R_B, R_N, R_U, R_X, U_O, U_P1, U_P2, U_P3,
            U_G, U_N, U_CB, U_WC, U_S, U_C。
    """
    enable_map(app)
    env = SimpleNamespace()
    env.R_A = create_role(MAP_GROUP_PREFIX + "Alpha")
    env.R_a = create_role(MAP_GROUP_PREFIX + "alphabet")
    env.R_B = create_role(MAP_GROUP_PREFIX + "Beta")
    env.R_N = get_or_create_role("Original Role")
    env.R_U = create_role("JC_IDP_EXAMPLE_ORG_GR_Alpha")
    # 保存した後にロール名を変更して、指定不可となったロールを作る
    env.R_X = create_role(MAP_GROUP_PREFIX + "Gamma")
    env.R_X.name = "Former Gamma"
    db.session.commit()
    if with_roles_only:
        return env

    n = next(_user_seq)
    env.U_O = create_user("proxy_owner{}@test.org".format(n))
    env.U_P1 = create_user("proxy_p1_{}@test.org".format(n))
    env.U_P2 = create_user("proxy_p2_{}@test.org".format(n))
    env.U_P3 = create_user("proxy_p3_{}@test.org".format(n))
    env.U_G = create_user("proxy_group{}@test.org".format(n), [env.R_A])
    env.U_N = create_user("proxy_none{}@test.org".format(n))
    # 登録者判定の 3 キーのうち owner 以外のキーのみ一致するユーザー
    env.U_CB = create_user("proxy_createdby{}@test.org".format(n))
    env.U_WC = create_user("proxy_creatorid{}@test.org".format(n))
    env.U_S = create_user(
        "proxy_super{}@test.org".format(n),
        [get_or_create_role("System Administrator")])
    env.U_C = create_user(
        "proxy_comadmin{}@test.org".format(n),
        [get_or_create_role("Community Administrator")])
    return env


def create_group_roles(count, prefix="G"):
    """jc_idp_example_org_gr_ で始まるロールを count 件作成する(上限超過の確認用)."""
    return [create_role("{}{}{}".format(MAP_GROUP_PREFIX, prefix, i + 1))
            for i in range(count)]


def create_proxy_activity(
        wf, login_user, shared_user_ids=UNSET, shared_role_ids=UNSET,
        temp_data=UNSET, item_id=None, action_id=3, action_order=2, **kwargs):
    """アクティビティ行を作成する.

    Args:
        wf (dict): ``workflow`` フィクスチャの戻り値。
        login_user (User): activity_login_user。
        shared_user_ids, shared_role_ids, temp_data: カラムに保存する値を
            そのまま指定する(temp_data の文字列スカラーは ``json.dumps`` した
            文字列を渡す)。未指定はモデルの既定値。
        item_id (uuid): 紐づくアイテムID。
    """
    n = next(_activity_seq)
    values = dict(
        activity_id="A-20260101-{:05d}".format(n),
        workflow_id=wf["workflow"].id,
        flow_id=wf["flow"].id,
        action_id=action_id,
        action_order=action_order,
        activity_login_user=login_user.id,
        activity_update_user=login_user.id,
        activity_start=datetime.utcnow(),
        item_id=item_id,
        extra_info={},
    )
    if shared_user_ids is not UNSET:
        values["shared_user_ids"] = shared_user_ids
    if shared_role_ids is not UNSET:
        values["shared_role_ids"] = shared_role_ids
    if temp_data is not UNSET:
        values["temp_data"] = temp_data
    values.update(kwargs)
    activity = Activity(**values)
    db.session.add(activity)
    db.session.commit()
    return activity


def set_raw_json(activity_id, column, raw_json):
    """JSONB カラムへ、JSON の ``null`` などをそのまま保存する.

    ORM では None が SQL の NULL になる(none_as_null=True)ため、
    JSON の null・オブジェクト・文字列を直接保存する用途で使う。

    Args:
        activity_id (str): アクティビティID。
        column (str): ``shared_user_ids`` / ``shared_role_ids`` / ``temp_data``。
        raw_json (str): JSON 文字列(例: ``'null'``・``'{"foo": 1}'``)。
    """
    assert column in ("shared_user_ids", "shared_role_ids", "temp_data")
    db.session.execute(
        text("UPDATE workflow_activity SET {} = CAST(:v AS JSONB) "
             "WHERE activity_id = :a".format(column)),
        {"v": raw_json, "a": activity_id})
    db.session.commit()


def compile_sql(query):
    """Query を PostgreSQL の方言・literal_binds で SQL 文字列にする."""
    statement = query.statement if hasattr(query, "statement") else query
    try:
        return str(statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    except NotImplementedError:
        # 空リストの IN など literal_binds で描画できない値がある場合は、
        # バインド値を手動で文字列に置換する
        compiled = statement.compile(dialect=postgresql.dialect())
        sql = str(compiled)
        for key, value in compiled.params.items():
            if isinstance(value, (list, tuple)):
                literal = "(" + ", ".join(repr(v) for v in value) + ")"
            elif isinstance(value, str):
                literal = "'" + value.replace("'", "''") + "'"
            else:
                literal = str(value)
            sql = sql.replace("%(" + key + ")s", literal)
        return sql.replace("%%", "%")


def build_tab_query(tab, user, is_community_admin=False):
    """タブごとの一覧クエリを組み立てる(get_activity_list と同じ組み立て).

    Args:
        tab (str): ``wait`` / ``all`` / ``todo``。
        user (User): ログインユーザー(current_user をこの値に差し替える)。
    """
    with patch("flask_login.utils._get_user", return_value=user):
        query = WorkActivity._WorkActivity__common_query_activity_list()
        if tab == "wait":
            return WorkActivity.query_activities_by_tab_is_wait(
                query, False, is_community_admin, [])
        query = WorkActivity.query_activities_by_tab_is_all(
            query, is_community_admin, [], [])
        if tab == "todo":
            query = WorkActivity.query_activities_by_tab_is_todo(
                query, False, is_community_admin, [], [])
        return query


def build_func_query(func_name, user, is_community_admin=False):
    """一覧クエリ関数を単体で呼び出した Query を返す(タブの連鎖はしない).

    Args:
        func_name (str): ``is_wait`` / ``is_all`` / ``is_todo``。
        user (User): ログインユーザー(current_user をこの値に差し替える)。
    """
    with patch("flask_login.utils._get_user", return_value=user):
        query = WorkActivity._WorkActivity__common_query_activity_list()
        if func_name == "is_wait":
            return WorkActivity.query_activities_by_tab_is_wait(
                query, False, is_community_admin, [])
        if func_name == "is_all":
            return WorkActivity.query_activities_by_tab_is_all(
                query, is_community_admin, [], [])
        return WorkActivity.query_activities_by_tab_is_todo(
            query, False, is_community_admin, [], [])


def list_activity_ids(tab, user, is_community_admin=False):
    """タブの一覧に含まれるアクティビティIDの集合を返す.

    クエリの実行も current_user を差し替えた状態で行う。
    """
    with patch("flask_login.utils._get_user", return_value=user):
        query = build_tab_query(tab, user, is_community_admin)
        return {row[0].activity_id for row in query.all()}


def add_flow_action_role(wf, action_id, action_order, **kwargs):
    """ワークフローのフローアクションに FlowActionRole を追加する."""
    flow_action = FlowAction.query.filter_by(
        flow_id=wf["flow"].flow_id, action_id=action_id,
        action_order=action_order).one()
    role = FlowActionRole(flow_action_id=flow_action.id, **kwargs)
    db.session.add(role)
    db.session.commit()
    return role
