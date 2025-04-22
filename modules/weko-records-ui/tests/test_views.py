from unittest.mock import MagicMock
import pytest
import io
from flask import Flask, json, jsonify, session, url_for, make_response
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from mock import patch
from lxml import etree
from weko_deposit.api import WekoRecord
from werkzeug.exceptions import NotFound
from sqlalchemy.orm.exc import MultipleResultsFound
from jinja2.exceptions import TemplatesNotFound
from weko_redis import RedisConnection
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    FlowAction,
    FlowDefine,
    WorkFlow,
)
from weko_records_ui.views import (
    check_permission,
    citation,
    escape_newline,
    get_image_src,
    get_license_icon,
    json_string_escape,
    pid_value_version,
    publish,
    restore,
    check_file_permission,
    record_from_pid,
    default_view_method,
    url_to_link,
    xml_string_escape,
    escape_str,
    init_permission,
    file_version_update,
    set_pdfcoverpage_header,
    parent_view_method,
    doi_ish_view_method,
    check_file_permission_period,
    get_file_permission,
    check_content_file_clickable,
    get_usage_workflow,
    get_workflow_detail,
    preview_able,
    get_uri,
)

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def record_from_pid(pid_value):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_record_from_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_record_from_pid(app, records):
    indexer, results = records
    recid = results[0]["recid"]
    ret = record_from_pid(recid.pid_value)
    assert isinstance(ret, WekoRecord)

    ret = record_from_pid(0)
    assert ret == {}


# def url_to_link(field):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_url_to_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_url_to_link():
    assert url_to_link("file://localhost") == False
    assert url_to_link("http://localhost") == True
    assert url_to_link("https://localhost") == True
    assert url_to_link("https://localhost/records/123/files/file.pdf") == False


# def pid_value_version(pid_value):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_pid_value_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_pid_value_version():
    assert pid_value_version(1.1) == "1"
    assert pid_value_version(1.0) == "0"
    assert pid_value_version(1) == None
    assert pid_value_version("1") == None
    assert pid_value_version("1.1") == "1"
    
    pid_value_version(MagicMock())


# def publish(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_publish_acl_guest(client, records):
    url = url_for("invenio_records_ui.recid_publish", pid_value=1, _external=True)
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == "http://test_server/records/1"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_publish_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 302),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_publish_acl(client, records, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("invenio_records_ui.recid_publish", pid_value=1, _external=True)
    res = client.post(url)
    assert res.status_code == status_code
    assert res.location == "http://test_server/records/1"


# def export(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_export_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_export_acl_guest(client, records):
    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="json", _external=True
    )
    res = client.post(url)
    assert res.status_code == 405

    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="bibtex", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="oai_dc", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200

    url = url_for(
        "invenio_records_ui.recid_export",
        pid_value=1,
        format="jpcoar_1.0",
        _external=True,
    )
    res = client.get(url)
    assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_export_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_export_acl(client, records, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="json", _external=True
    )
    res = client.post(url)
    assert res.status_code == 405

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="bibtex", _external=True
    )
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for(
        "invenio_records_ui.recid_export", pid_value=1, format="oai_dc", _external=True
    )
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for(
        "invenio_records_ui.recid_export",
        pid_value=1,
        format="jpcoar_1.0",
        _external=True,
    )
    res = client.get(url)
    assert res.status_code == status_code


# def get_image_src(mimetype):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_image_src -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_image_src():
    assert get_image_src("text/plain") == "/static/images/icon/icon_16_txt.jpg"
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.slide"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.presentationml.template"
        )
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.template"
        )
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        == "/static/images/icon/icon_16_doc.jpg"
    )
    assert (
        get_image_src(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.template"
        )
        == "/static/images/icon/icon_16_doc.jpg"
    )
    assert get_image_src("application/msword") == "/static/images/icon/icon_16_doc.jpg"
    assert (
        get_image_src("application/vnd.ms-excel")
        == "/static/images/icon/icon_16_xls.jpg"
    )
    assert (
        get_image_src("application/vnd.ms-powerpoint")
        == "/static/images/icon/icon_16_ppt.jpg"
    )
    assert get_image_src("application/zip") == "/static/images/icon/icon_16_zip.jpg"
    assert get_image_src("audio/mpeg") == "/static/images/icon/icon_16_music.jpg"
    assert get_image_src("application/xml") == "/static/images/icon/icon_16_xml.jpg"
    assert get_image_src("image/jpeg") == "/static/images/icon/icon_16_picture.jpg"
    assert get_image_src("application/pdf") == "/static/images/icon/icon_16_pdf.jpg"
    assert get_image_src("video/x-flv") == "/static/images/icon/icon_16_flash.jpg"
    assert get_image_src("video/mpeg") == "/static/images/icon/icon_16_movie.jpg"
    assert get_image_src("application/json") == "/static/images/icon/icon_16_others.jpg"


# def get_license_icon(license_type):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_license_icon -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_license_icon(app):
    with app.test_request_context(headers=[("Accept-Language", "ja")]):
        assert get_license_icon("license_12") == (
            "static/images/default88x31(0).png",
            "Creative Commons CC0 1.0 Universal Public Domain Designation",
            "https://creativecommons.org/publicdomain/zero/1.0/",
        )
        assert get_license_icon("license_free") == ("", "", "#")


#     # In case of current lang is not JA, set to default.
#     current_lang = 'default' if current_i18n.language != 'ja' \
# def check_permission(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_permission(app, records, users):
    indexer, results = records
    record = results[0]["record"]

    assert check_permission(record) == False

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert check_permission(record) == True

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        assert check_permission(record) == False


# def check_file_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ],
)
def test_check_file_permission(app,records,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert check_file_permission(record,record['item_1617605131499'])==result


# def check_file_permission_period(record, fjson):
# Error
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_file_permission_period -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, True),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_check_file_permission_period(app,records,db_file_permission,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    fjson = record['item_1617605131499']['attribute_value_mlt'][0]
    # fjson = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': 'image/jpeg', 'filename': 'helloworld.pdf', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': 2700000.0, 'mimetype': 'image/jpeg', 'file_order': 0}
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert check_file_permission_period(record,fjson)==result

        # data1 = MagicMock()
        # data2 = MagicMock()
        # assert check_file_permission_period(record,fjson)


# def get_file_permission(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, None),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_get_file_permission(app,records,users,id,result,db_file_permission):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert get_file_permission(record,record['item_1617605131499']['attribute_value_mlt'][0])==result


# def check_content_file_clickable(record, fjson):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_check_content_file_clickable -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_check_content_file_clickable(app,records,users,id,result):
    indexer, results = records
    record = results[0]["record"]
    assert isinstance(record,WekoRecord)==True
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        assert check_content_file_clickable(record,record['item_1617605131499'])==result


# def get_usage_workflow(file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_usage_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_usage_workflow(app, users, workflows):
    _file_json = {
        'provide': [
            {
                'role_id': "3",
                'workflow_id': "2"
            }
            ,
            {
                'role_id': "none_loggin",
                'workflow_id': "3"
            }
        ]
    }
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        res = get_usage_workflow(_file_json)
        assert res=="2"
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        res = get_usage_workflow(_file_json)
        assert res==None

    data1 = MagicMock()
    data1.is_authenticated = False

    with patch("flask_login.utils._get_user", return_value=data1):
        res = get_usage_workflow(_file_json)
        assert res=="3"


# def get_workflow_detail(workflow_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_workflow_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_workflow_detail(app,workflows):
    wf = workflows['workflow']
    ret = get_workflow_detail(wf.id)
    assert isinstance(wf,WorkFlow)

    with pytest.raises(NotFound):
        ret = get_workflow_detail(0)
    

# def default_view_method(pid, record, filename=None, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_default_view_method -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
#     """Display default view.
#     def _get_rights_title(result, rights_key, rights_values, current_lang, meta_options):
def test_default_view_method(app, records, itemtypes, indexstyle, mocker, db_admin_settings):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    with app.test_request_context():
        with patch('weko_records_ui.views.check_original_pdf_download_permission', return_value=True):
            with patch("weko_records_ui.views.get_search_detail_keyword", return_value={}):
                with patch("weko_records_ui.views.get_index_link_list", return_value=[]):
                    # need to fix
                    with pytest.raises(Exception) as e:
                        res = default_view_method(recid, record, 'helloworld.pdf')
                    assert e.type==TemplatesNotFound
                    
                    mock_render_template = mocker.patch("weko_records_ui.views.render_template")
                    default_view_method(recid, record, template='weko_records_ui/detail.html')
                    args, kwargs = mock_render_template.call_args
                    # hide items: item_1617944105607, item_1617620223087.subitem_1565671169640
                    res_record = kwargs["record"]
                    assert "item_1617944105607" not in res_record
                    for d in res_record["item_1617620223087"]["attribute_value_mlt"]:
                        assert "subitem_1565671169640" not in d

# def doi_ish_view_method(parent_pid_value=0, version=0):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_doi_ish_view_method_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_doi_ish_view_method_acl_guest(app,client,records):
    url = url_for("weko_records_ui.doi_ish_view_method", parent_pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Fr%2F1'


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_doi_ish_view_method_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_doi_ish_view_method_acl(app,client,records,users,id,result):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.doi_ish_view_method", parent_pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/records/1.1'

    assert "302 FOUND" in doi_ish_view_method(parent_pid_value=1, version=1)


# def parent_view_method(pid_value=0):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_parent_view_method_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_parent_view_method_acl_guest(app,client,records):
    url = url_for("weko_records_ui.parent_view_method", pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Frecords%2Fparent%3A1'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_parent_view_method_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_parent_view_method_acl(app,client,records,users,id,result):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.parent_view_method", pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/records/1.1'


# def set_pdfcoverpage_header():
# Error
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_set_pdfcoverpage_header_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_set_pdfcoverpage_header_acl_guest(app, client, records, pdfcoverpagesetting):
    url = url_for("weko_records_ui.set_pdfcoverpage_header",_external=True)
    res = client.get(url)
    assert res.status_code == 308
    assert res.location == 'http://test_server/admin/pdfcoverpage/'

    res = client.post(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Frecords%2Fparent%3A1'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_set_pdfcoverpage_header_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, result",
    [
        (0, False),
        # (1, True),
        # (2, True),
        # (3, True),
        # (4, True),
        # (5, True),
        # (6, True),
        # (7, True),
    ],
)
def test_set_pdfcoverpage_header_acl(app, client, records, users, id, result, pdfcoverpagesetting):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.set_pdfcoverpage_header",_external=True)
    res = client.get(url)
    assert res.status_code == 308
    assert res.location == 'http://test_server/admin/pdfcoverpage/'

    data = {'availability':'enable', 'header-display':'string', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
    'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    res = client.post(url,data=data)
    assert res.status_code == 302
    assert res.location == 'http://test_server/admin/pdfcoverpage'

    data = {'availability':'enable', 'header-display':'image', 'header-output-string':'Weko Univ', 'header-display-position':'center', 'pdfcoverpage_form': '',
    'header-output-image': (io.BytesIO(b"some initial text data"), 'test.png')}
    res = client.post(url,data=data)
    assert res.status_code == 302
    assert res.location == 'http://test_server/admin/pdfcoverpage'


#     def handle_over_max_file_size(error):
# def file_version_update():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_file_version_update_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_version_update_acl_guest(client, records):
    url = url_for("weko_records_ui.file_version_update",_external=True)
    res = client.put(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server/login/?next=%2Ffile_version%2Fupdate'


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_file_version_update_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_file_version_update_acl(client, records, users, id, status_code):
    _data = {}
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_records_ui.file_version_update",_external=True)
    res = client.put(url)
    assert res.status_code == status_code
    assert json.loads(res.data) == {'status': 0, 'msg': 'Insufficient permission'}

    # need to fix
    with patch("weko_records_ui.views.has_update_version_role", return_value=True):
        with pytest.raises(Exception) as e:
            res = client.put(url, data=_data)
        assert e.type == MultipleResultsFound

        _data['bucket_id'] = 'none bucket'
        _data['key'] = 'none key'
        _data['version_id'] = 'version_id'
        res = client.put(url, data=_data)
        assert res.status_code == status_code
        assert json.loads(res.data) == {'status': 0, 'msg': 'Invalid data'}

        data1 = MagicMock()
        data1.is_show = 1

        with patch("invenio_files_rest.models.ObjectVersion.get", return_value=data1):
            file_version_update()

# def citation(record, pid, style=None, ln=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_citation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_citation(records):
    indexer, results = records
    record = results[0]["record"]
    assert citation(record,record.pid)==None


# def soft_delete(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.soft_delete", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_soft_delete_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 500), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 500), # generaluser
        (5, 500), # originalroleuser 
        (6, 200), # originalroleuser2
        (7, 500), # user
    ],
)
def test_soft_delete_acl(client, records, users, id, status_code):
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        url = url_for(
            "weko_records_ui.soft_delete", recid=1, _external=True
        )
        with patch("flask.templating._render", return_value=""):
            res = client.post(url)
            assert res.status_code == status_code


# def restore(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_restore_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_restore_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.restore", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_restore_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 500), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 500), # generaluser
        (5, 500), # originalroleuser 
        (6, 200), # originalroleuser2
        (7, 500), # user
    ],
)
def test_restore_acl(client, records, users, id, status_code):
    with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
        url = url_for(
            "weko_records_ui.restore", recid=1, _external=True
        )
        with patch("flask.templating._render", return_value=""):
            res = client.post(url)
            assert res.status_code == status_code

# def init_permission(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_init_permission_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_init_permission_acl_guest(client, records):
    url = url_for(
        "weko_records_ui.init_permission", recid=1, _external=True
    )
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_init_permission_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
# Error
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 400),
        # (1, 302),
        # (2, 302),
        # (3, 302),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_init_permission_acl(client, records,users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    _data = {
        'file_name': 'helloworld.pdf',
        'activity_id': 'A-00000000-00000',
    }
    url = url_for(
        "weko_records_ui.init_permission", recid=1, _external=True
    )
    res = client.post(url, data=_data,headers = {"Content-Type" : "application/json"})
    assert res.status_code == status_code


# def escape_str(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_escape_str -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_escape_str():
    assert escape_str("\n")==""


# def escape_newline(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_escape_newline -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_escape_newline():
    assert escape_newline("\r") == '<br/>'
    assert escape_newline("\r\n") == '<br/>'
    assert escape_newline("\n") == '<br/>'
    assert escape_newline("\r\r\n\n") == '<br/><br/><br/>'

# def json_string_escape(s):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_json_string_escape -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

def test_json_string_escape():
    assert json_string_escape("\x5c") == "\\\\"
    assert json_string_escape("\x08") == "\\b"
    assert json_string_escape("\x0a") == "\\n"
    assert json_string_escape("\x0d") == "\\r"
    assert json_string_escape("\x09") == "\\t"
    assert json_string_escape("\x0c") == "\\f"
    assert json_string_escape("\x0c") == "\\f"
    assert json_string_escape('"\x0c"') == '\\"\\f\\"'


# def xml_string_escape(s):
def test_xml_string_escape():
    assert xml_string_escape("&<>") == "&amp;&lt;&gt;"


# def preview_able(file_json):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_preview_able -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_preview_able(app):
    mimetype = "image/jpeg"
    size = 200000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == True

    mimetype = "application/msword"
    size = 2000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == True
    

    size = 20000000000000
    file_json = {'url': {'url': 'https://weko3.example.org/record/11/files/001.jpg'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-27'}], 'format': mimetype, 'filename': '001.jpg', 'filesize': [{'value': '2.7 MB'}], 'accessrole': 'open_access', 'version_id': 'd73bd9cb-aa9e-4cd0-bf07-c5976d40bdde', 'displaytype': 'preview', 'is_thumbnail': False, 'future_date_message': '', 'download_preview_message': '', 'size': size, 'mimetype': mimetype, 'file_order': 0}
    with app.test_request_context():
        ret = preview_able(file_json)
        assert isinstance(ret,bool)
        assert ret == False

# def get_uri():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_get_uri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_uri(app,client,db_sessionlifetime,records):
    url = url_for("weko_records_ui.get_uri",  _external=True)
    res = client.post(url,data=json.dumps({"uri":"https://localhost/record/1/files/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

    res = client.post(url,data=json.dumps({"uri":"https://localhost/001.jpg","pid_value":"1","accessrole":"1"}), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data)=={'status': True}

# def charge():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_charge -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_charge(app,db,users,client,mocker):
    _data = {}
    url = url_for("weko_records_ui.charge",_external=True)
    _data['item_id'] = '1'
    _data['file_name'] = 'file_name'
    _data['title'] = 'title'
    _data['price'] = '110'

    redis = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv=True)
    redis_key = 'charge_{}'.format(users[0]['obj'].get_id())

    with patch.object(db.session, "remove", lambda: None):
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            # redis_key is exists
            redis.put(redis_key, _data['item_id'].encode('utf-8'))
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}
            redis.delete(redis_key)

            # 49
            with patch('weko_records_ui.views.check_charge', return_value='already'):
                res = client.get(url, data=_data)
                assert json.loads(res.data) == {'status': 'already'}
            with patch('weko_records_ui.views.check_charge', side_effect=Exception):
                with patch("weko_records_ui.views.abort", return_value=make_response()) as mock_abort:
                    with patch("weko_records_ui.views.create_charge", return_value=make_response()) as mock_create_charge:
                        res = client.get(url, data=_data)
                        mock_abort.assert_called_with(500)
                        mock_create_charge.assert_not_called()
            
            with patch('weko_records_ui.views.check_charge', return_value='not_billed'):
                # 50
                with patch('weko_records_ui.views.create_charge', return_value='connection_error'):
                    res = client.get(url, data=_data)
                    assert json.loads(res.data) == {'status': 'error'}
                # 51
                with patch('weko_records_ui.views.create_charge', return_value='credit_error'):
                    res = client.get(url, data=_data)
                    assert json.loads(res.data) == {'status': 'credit_error'}
                # 52
                with patch('weko_records_ui.views.create_charge', return_value='already'):
                    res = client.get(url, data=_data)
                    assert json.loads(res.data) == {'status': 'already'}
                
                with patch('weko_records_ui.views.create_charge', side_effect=Exception):
                    with patch("weko_records_ui.views.abort", return_value=make_response()) as mock_abort:
                        with patch("weko_records_ui.views.close_charge", return_value=make_response()) as mock_close_charge:
                            res = client.get(url, data=_data)
                            mock_abort.assert_called_with(500)
                            mock_close_charge.assert_not_called()

                with patch('weko_records_ui.views.create_charge', return_value='https://pt01.mul-pay.jp'):
                    # charge is success
                    redirect = mocker.patch('weko_records_ui.views.redirect', return_value=make_response())
                    client.get(url, data=_data)
                    redirect.asert_called_with('https://pt01.mul-pay.jp')
                    redis_value = redis.get(redis_key)
                    assert redis_value.decode('utf-8') == _data['item_id']
                    redis.delete(redis_key)
                
                with patch('weko_records_ui.views.create_charge', return_value=None):
                    # charge is fail
                    res = client.get(url, data=_data)
                    assert json.loads(res.data) == {'status': 'error'}
                    assert redis.redis.exists(redis_key) == 0

# def charge_secure():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_charge_secure -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_charge_secure(app, db, users, client, mocker):
    _data = {}
    url = url_for('weko_records_ui.charge_secure', _external=True)
    _data['MD'] = 'access_id'

    redis = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv=True)
    redis_key = 'charge_{}'.format(users[0]['obj'].get_id())
    redis.delete(redis_key)

    with patch.object(db.session, "remove", lambda: None):
        with patch('flask_login.utils._get_user', return_value=users[0]['obj']):
            mocker_redirect = mocker.patch('weko_records_ui.views.redirect', return_value=make_response())
            # redis_key is not exists
            client.post(url, data=_data)
            mocker_redirect.assert_called_with('/')
            assert redis.redis.exists(redis_key) == 0

            with patch('weko_records_ui.views.secure_charge', side_effect=Exception):
                with patch('weko_records_ui.views.abort', return_value=make_response()) as mocker_abort:
                    # secure_charge is fail
                    redis.put(redis_key, '1'.encode('utf-8'))
                    client.post(url, data=_data)
                    mocker_abort.assert_called_with(500)
                    assert redis.redis.exists(redis_key) == 0

            with patch('weko_records_ui.views.secure_charge', return_value='connection_error'):
                # secure_charge's return value is connection_error
                redis.put(redis_key, '1'.encode('utf-8'))
                client.post(url, data=_data)
                mocker_redirect.assert_called_with('/records/1')
                assert redis.redis.exists(redis_key) == 0
            
            with patch('weko_records_ui.views.secure_charge', return_value='api_error'):
                # secure_charge's return value is api_error
                redis.put(redis_key, '1'.encode('utf-8'))
                client.post(url, data=_data)
                mocker_redirect.assert_called_with('/records/1')
                assert redis.redis.exists(redis_key) == 0

            with patch('weko_records_ui.views.secure_charge', return_value=1):
                with patch('weko_records_ui.views.close_charge', side_effect=Exception):
                    with patch('weko_records_ui.views.abort', return_value=make_response()) as mocker_abort:
                        # close_charge is fail
                        redis.put(redis_key, '1'.encode('utf-8'))
                        client.post(url, data=_data)
                        mocker_abort.assert_called_with(500)
                        assert redis.redis.exists(redis_key) == 0

                with patch('weko_records_ui.views.close_charge'):
                    # close_charge is success
                    redis.put(redis_key, '1'.encode('utf-8'))
                    client.post(url, data=_data)
                    mocker_redirect.assert_called_with('/records/1')
                    assert redis.redis.exists(redis_key) == 0

# def charge_show():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_charge_show -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_charge_show(db, users, client, mocker):
    _data = {}
    url = url_for('weko_records_ui.charge_show', _external=True)
    _data['item_id'] = '1'

    with patch.object(db.session, 'remove', lambda: None):
        with patch('flask_login.utils._get_user', return_value=users[0]['obj']):
            mocker_check_charge = mocker.patch('weko_records_ui.views.check_charge')
            # check_charge returns 'already'
            mocker_check_charge.return_value = 'already'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'success'}

            # check_charge returns 'api_error'
            mocker_check_charge.return_value = 'api_error'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}

            # check_charge returns 'unknown_user'
            mocker_check_charge.return_value = 'unknown_user'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}

            # check_charge returns 'shared'
            mocker_check_charge.return_value = 'shared'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}

            # check_charge returns 'credit_error'
            mocker_check_charge.return_value = 'credit_error'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}

            # check_charge returns 'not_billed'
            mocker_check_charge.return_value = 'not_billed'
            res = client.get(url, data=_data)
            assert json.loads(res.data) == {'status': 'error'}

            # check_charge occurs an exception
            mocker_check_charge.side_effect = Exception
            with patch('weko_records_ui.views.abort', return_value=make_response()) as mocker_abort:
                res = client.get(url, data=_data)
                mocker_abort.assert_called_with(500)

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_views.py::test_default_view_method_fix35133 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_default_view_method_fix35133(app, records, itemtypes, indexstyle,mocker):
    indexer, results = records
    record = results[0]["record"]
    recid = results[0]["recid"]
    etree_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-10-07T06:11:40Z</responseDate><request identifier="oai:repository.dl.itc.u-tokyo.ac.jp:02005680" verb="getrecord" metadataPrefix="jpcoar_1.0">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><getrecord><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:02005680</identifier><datestamp>2022-09-27T06:40:27Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表</dc:title><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/123" nameIdentifierScheme="ORCID">123</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="en">creator name</jpcoar:creatorName><jpcoar:familyName xml:lang="en">creator family name</jpcoar:familyName><jpcoar:givenName xml:lang="en">creator given name</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="en">creator alternative name</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="test uri" nameIdentifierScheme="ISNI">affi name id</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">affi name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><dc:rights>CC BY</dc:rights><datacite:description xml:lang="ja" descriptionType="Other">『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。</datacite:description><dc:publisher xml:lang="ja">東京大学史料編纂所附属画像史料解析センター</dc:publisher><dc:publisher xml:lang="en">Center for the Study of Visual Sources, Historiographical Institute, The University of Tokyo</dc:publisher><datacite:date dateType="Issued">2022-09-30</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_ddb1">dataset</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/0002005680</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/2005680</jpcoar:identifier><jpcoar:relation relationType="references"><jpcoar:relatedIdentifier identifierType="URI">https://clioimg.hi.u-tokyo.ac.jp/viewer/list/idata/850/8500/20/%28a%29/?m=limit</jpcoar:relatedIdentifier></jpcoar:relation><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>point longitude test</datacite:pointLongitude><datacite:pointLatitude>point latitude test</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>1</datacite:westBoundLongitude><datacite:eastBoundLongitude>2</datacite:eastBoundLongitude><datacite:southBoundLatitude>3</datacite:southBoundLatitude><datacite:northBoundLatitude>4</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>geo location place test</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:file><jpcoar:URI objectType="dataset">https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx</jpcoar:URI><jpcoar:mimeType>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</jpcoar:mimeType><jpcoar:extent>121.7KB</jpcoar:extent><datacite:date dateType="Available">2022-09-27</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></getrecord></OAI-PMH>'
    et = etree.fromstring(etree_str)
    mock_render_template = mocker.patch("weko_records_ui.views.render_template")
    with app.test_request_context():
        with patch('weko_records_ui.views.check_original_pdf_download_permission', return_value=True):
            with patch("weko_records_ui.views.getrecord",return_value=et):
                default_view_method(recid, record)
                args, kwargs = mock_render_template.call_args
                assert kwargs["google_scholar_meta"] == [
                        {'name': "citation_title","data": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表"},
                        {"name": "citation_publisher", "data": "東京大学史料編纂所附属画像史料解析センター"},
                        {'name': 'citation_publication_date', 'data': "2022-09-30"},
                        {"name": "citation_author","data": "creator name"},
                        {"name":"citation_pdf_url","data":"https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx"},
                        {'name': 'citation_dissertation_institution','data':""},
                        {'name': 'citation_abstract_html_url','data': 'http://TEST_SERVER/records/1'},
                    ]
                assert kwargs["google_dataset_meta"] == '{"@context": "https://schema.org/", "@type": "Dataset", "citation": ["http://hdl.handle.net/2261/0002005680", "https://repository.dl.itc.u-tokyo.ac.jp/records/2005680"], "creator": [{"@type": "Person", "alternateName": "creator alternative name", "familyName": "creator family name", "givenName": "creator given name", "identifier": "123", "name": "creator name"}], "description": "『史料編纂掛備用寫眞畫像圖畫類目録』（1905年）の「画像」（肖像画模本）の部に著録する資料の架番号の新旧対照表。史料編纂所所蔵肖像画模本データベースおよび『目録』版面画像へのリンク付き。『画像史料解析センター通信』98（2022年10月）に解説記事あり。", "distribution": [{"@type": "DataDownload", "contentUrl": "https://repository.dl.itc.u-tokyo.ac.jp/record/2005680/files/comparison_table_of_preparation_image_catalog.xlsx", "encodingFormat": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/apt.txt", "encodingFormat": "text/plain"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/environment.yml", "encodingFormat": "application/x-yaml"}, {"@type": "DataDownload", "contentUrl": "https://raw.githubusercontent.com/RCOSDP/JDCat-base/main/postBuild", "encodingFormat": "text/x-shellscript"}], "includedInDataCatalog": {"@type": "DataCatalog", "name": "https://localhost"}, "license": ["CC BY"], "name": "『史料編纂掛備用写真画像図画類目録』画像の部：新旧架番号対照表", "spatialCoverage": [{"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": "point latitude test", "longitude": "point longitude test"}}, {"@type": "Place", "geo": {"@type": "GeoShape", "box": "1 3 2 4"}}, "geo location place test"]}'

