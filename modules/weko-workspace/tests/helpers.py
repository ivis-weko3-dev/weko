import json
from os.path import dirname, join

def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# テスト用ユーザー・ロールの作成補助
# ---------------------------------------------------------------------------
# 学認 mAP 設定。グループプレフィックスは jc_idp_example_org_gr_ となる
IDP_ENTITY_ID = "https://idp.example.org/idp/shibboleth"
GROUP_PREFIX = "jc_idp_example_org_gr_"
ADMIN_ROLE_NAME = "System Administrator"


def get_or_create_role(name):
    """ロールを取得する。無ければ作成する。"""
    from flask import current_app
    from invenio_accounts.models import Role

    ds = current_app.extensions["invenio-accounts"].datastore
    role = Role.query.filter_by(name=name).first()
    if role is None:
        role = ds.create_role(name=name)
        ds.commit()
    return role


def new_user(email, role_names=()):
    """テスト関数内でローカルにユーザーを作成する(共有フィクスチャは変更しない)。"""
    from flask import current_app
    from invenio_accounts.testutils import create_test_user

    ds = current_app.extensions["invenio-accounts"].datastore
    user = create_test_user(email=email)
    for name in role_names:
        ds.add_role_to_user(user, get_or_create_role(name))
    ds.commit()
    return user


def reset_request_cache():
    """リクエスト単位で flask.g にキャッシュされる値を破棄する。"""
    from flask import g

    g.pop("_weko_user_role_ids", None)
    g.pop("_weko_shared_excluded_doc_ids", None)
