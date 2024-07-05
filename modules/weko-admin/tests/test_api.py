
import pytest
from mock import patch
from redis import RedisError
from requests.models import Response
from flask import make_response, request, current_app
from flask_wtf.csrf import CSRFError
from wtforms import ValidationError
from weko_admin.api import (
    is_restricted_user,
    _is_crawler,
    send_site_license_mail,
    TempDirInfo,
    validate_csrf_header
)
from weko_admin.models import SiteInfo


# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

#def is_restricted_user(user_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::test_is_restricted_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_restricted_user(client,restricted_ip_addr,mocker):
    mocker.patch("weko_admin.api._is_crawler",return_value=False)
    result = is_restricted_user({"ip_address":"123.456.789.012"})
    assert result == True
    
    result = is_restricted_user({"ip_address":"987.654.321.098"})
    assert result == False
    
    with patch("weko_admin.api._is_crawler",side_effect=Exception("test_error")):
        result = is_restricted_user({"ip_address":"123.456.789.012"})
        assert result == False
    
class MockRedisSet:
    def __init__(self):
        self.data = dict()
    
    def smembers(self,name):
        return {bytes(x,"utf-8") for x in self.data[name]} if name in self.data else set()
    
    def get(self,name):
        ret = ''
        if name in self.data:
            ret =  self.data[name]
        return ret

    def set(self,name,value):
        if name not in self.data:
            self.data[name] = ''
        self.data[name]=value
    
    def sadd(self,name,value):
        if name not in self.data:
            self.data[name] = set()
        self.data[name].add(value)

    def srem(self,name,value):
        self.data[name].remove(value)

    def srem_all(self,name):
        self.data[name] = set()

    def expire(self,name,ttl):
        pass

#def _is_crawler(user_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::test_is_crawler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_crawler(client,log_crawler_list,restricted_ip_addr,mocker):
    mock_redis = MockRedisSet()
    mocker.patch("weko_admin.api.RedisConnection.connection",return_value=mock_redis)
    mock_res=Response()
    mock_res._content = b"122.1.91.145\n122.1.91.146"
    with patch("weko_admin.api.requests.get",return_value=mock_res):
        user_info={"user_agent":"","ip_address":""}
        result = _is_crawler(user_info)
        assert result == False

        user_info = {"user_agent":"","ip_address":"122.1.91.145"}
        result = _is_crawler(user_info)
        assert result == True

        mock_redis.srem_all(log_crawler_list[0].list_url)
        with patch("weko_admin.api.RedisConnection.connection.smembers",side_effect=RedisError):
            result = _is_crawler(user_info)
            assert result == True
    
    mock_res=Response()
    mock_res._content = b""
    with patch("weko_admin.api.requests.get", return_value=mock_res):
        with patch("weko_admin.api.RedisConnection", side_effect=RedisError):
            result = _is_crawler(user_info)
            assert result == False


# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::test_is_crawler2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_is_crawler2(client,log_crawler_list,restricted_ip_addr,mocker):
    current_app.config.update(WEKO_ADMIN_USE_REGEX_IN_CRAWLER_LIST=True)
    mock_redis = MockRedisSet()
    mocker.patch("weko_admin.api.RedisConnection.connection",return_value=mock_redis)
    mock_res=Response()
    mock_res._content = b"API[\+\s]scraper\n^java\/\d{1,2}.\d"
    with patch("weko_admin.api.requests.get",return_value=mock_res):
        user_info={"user_agent":"API scraper","ip_address":""}
        result = _is_crawler(user_info)
        assert result == True

        user_info = {"user_agent":"API+scraper","ip_address":"122.1.91.145"}
        result = _is_crawler(user_info)
        assert result == True
        
        user_info = {"user_agent":"APIscraper","ip_address":"122.1.91.145"}
        result = _is_crawler(user_info)
        assert result == False
        
        user_info = {"user_agent":"java/1.1","ip_address":"122.1.91.145"}
        result = _is_crawler(user_info)
        assert result == True
        
        user_info = {"user_agent":"java/8","ip_address":"122.1.91.145"}
        result = _is_crawler(user_info)
        assert result == False
        

        mock_redis.srem_all(log_crawler_list[0].list_url)
        with patch("weko_admin.api.RedisConnection.connection.get",side_effect=RedisError):
            result = _is_crawler(user_info)
            assert result == False
    
    mock_res=Response()
    mock_res._content = b""
    with patch("weko_admin.api.requests.get", return_value=mock_res):
        with patch("weko_admin.api.RedisConnection", side_effect=RedisError):
            result = _is_crawler(user_info)
            assert result == False
            

#def send_site_license_mail(organization_name, mail_list, agg_date, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::test_send_site_license_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_send_site_license_mail(client,mocker,roles,site_info):
    SiteInfo.query.delete()
    data1 = {
        "site_name":[
            {"index":"new_index1","name":"new_name1","language":"en"},
            {"index":"new_index2","name":"new_name2","language":"ja"}
        ],
        "notify":[
            {"notify_name":"new_notify1","language":"en"},
            {"notify_name":"new_notify2","language":"ja"}
        ],
        "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
        "favicon_name":"test favicon","google_tracking_id_user":"test_tracking","addthis_user_id":"test_addthis_user",
        "ogp_image":""
    }
    data2 = {
        "site_name":[
            {"index":"new_index1","name":"new_name2","language":"ja"}
        ],
        "notify":[
            {"notify_name":"new_notify1","language":"en"},
            {"notify_name":"new_notify2","language":"ja"}
        ],
        "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
        "favicon_name":"test favicon","google_tracking_id_user":"test_tracking","addthis_user_id":"test_addthis_user",
        "ogp_image":""
    }
    data3 = {
        "site_name":[
            {"index":"new_index1","name":"new_name1","language":"en"}
        ],
        "notify":[
            {"notify_name":"new_notify1","language":"en"},
            {"notify_name":"new_notify2","language":"ja"}
        ],
        "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
        "favicon_name":"test favicon","google_tracking_id_user":"test_tracking","addthis_user_id":"test_addthis_user",
        "ogp_image":""
    }
    SiteInfo.update(data1)
    mocker.patch("weko_admin.api.get_system_default_language",return_value="en")
    organization_name="ORCID"
    mail_list=["test1@test.org","test2@test.org"]
    result = {"date":"2024-04-2024-05","datelist":["total","2024-04","2024-05"],"index_info":{"1616224532673":{"issn":12345,"name":"利用報告","name_en":"Data Report"},"1714029010533":{"issn":23456,"name":"New Index","name_en":"New Index"},"1714029010533:1715825846862":{"issn":678594,"name":"New New Index","name_en":"New New Index"}},"no_data":{"file_download":{"1616224532673":{"2024-04":0,"2024-05":0,"total":0},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":0,"2024-05":0,"total":0},"all_journals":{"2024-04":0,"2024-05":0}},"file_preview":{"1616224532673":{"2024-04":0,"2024-05":0,"total":0},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":0,"2024-05":0,"total":0},"all_journals":{"2024-04":0,"2024-05":0}},"search":{"2024-04":0,"2024-05":0,"total":0},"record_view":{"1616224532673":{"2024-04":0,"2024-05":0,"total":0,"file_download_count":{"2024-04":0,"2024-05":0,"total":0}},"1714029010533":{"2024-04":0,"2024-05":0,"total":0,"file_download_count":{"2024-04":0,"2024-05":0,"total":0}},"1714029010533:1715825846862":{"2024-04":0,"2024-05":0,"total":0,"file_download_count":{"2024-04":0,"2024-05":0,"total":0}}}},"result":{"ORCID":{"file_download":{"1616224532673":{"2024-04":1,"2024-05":22,"total":23},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":19,"2024-05":10,"total":29},"all_journals":{"2024-04":20,"2024-05":32}},"file_preview":{"1616224532673":{"2024-04":1,"2024-05":15,"total":16},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":19,"2024-05":27,"total":46},"all_journals":{"2024-04":20,"2024-05":42}},"search":{"2024-04":3,"2024-05":12,"total":15},"record_view":{"1616224532673":{"2024-04":27,"2024-05":15,"total":42,"file_download_count":{"2024-04":1,"2024-05":22,"total":23}},"1714029010533":{"2024-04":9,"2024-05":0,"total":9,"file_download_count":{"2024-04":0,"2024-05":0,"total":0}},"1714029010533:1715825846862":{"2024-04":0,"2024-05":23,"total":23,"file_download_count":{"2024-04":19,"2024-05":10,"total":29}}}}}}
    data={"file_download":{"1616224532673":{"2024-04":1,"2024-05":22,"total":23},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":19,"2024-05":10,"total":29},"all_journals":{"2024-04":20,"2024-05":32}},"file_preview":{"1616224532673":{"2024-04":1,"2024-05":15,"total":16},"1714029010533":{"2024-04":0,"2024-05":0,"total":0},"1714029010533:1715825846862":{"2024-04":19,"2024-05":27,"total":46},"all_journals":{"2024-04":20,"2024-05":42}},"search":{"2024-04":3,"2024-05":12,"total":15},"record_view":{"1616224532673":{"2024-04":27,"2024-05":15,"total":42,"file_download_count":{"2024-04":1,"2024-05":22,"total":23}},"1714029010533":{"2024-04":9,"2024-05":0,"total":9,"file_download_count":{"2024-04":0,"2024-05":0,"total":0}},"1714029010533:1715825846862":{"2024-04":0,"2024-05":23,"total":23,"file_download_count":{"2024-04":19,"2024-05":10,"total":29}}}}
    mock_send = mocker.patch("weko_admin.api.send_mail")
    mock_render = mocker.patch("weko_admin.api.render_template",return_value=make_response())
    send_site_license_mail(organization_name,mail_list,result,data)
    mock_send.assert_called_with("[new_name1]2024-04-2024-05 Site License Usage Statistics Report",mail_list,attachments=mocker.ANY,body="<<class 'pytest_flask.plugin.JSONResponse'> 0 bytes [200 OK]>")
    mock_render.assert_called_with(
        'weko_admin/email_templates/site_license_report.html',
        administrator=None,
        agg_date="2024-04-2024-05",
        organization_name='ORCID',
        site_name_en='new_name1', 
        site_name_ja='new_name2'
    )
    SiteInfo.update(data2)
    send_site_license_mail(organization_name,mail_list,result,data)
    mock_send.assert_called_with("[new_name2]2024-04-2024-05 Site License Usage Statistics Report",mail_list,attachments=mocker.ANY,body="<<class 'pytest_flask.plugin.JSONResponse'> 0 bytes [200 OK]>")
    mock_render.assert_called_with(
        'weko_admin/email_templates/site_license_report.html',
        administrator=None,
        agg_date="2024-04-2024-05",
        organization_name='ORCID',
        site_name_en='new_name2', 
        site_name_ja='new_name2'
    )
    SiteInfo.update(data3)
    send_site_license_mail(organization_name,mail_list,result,data)
    mock_send.assert_called_with("[new_name1]2024-04-2024-05 Site License Usage Statistics Report",mail_list,attachments=mocker.ANY,body="<<class 'pytest_flask.plugin.JSONResponse'> 0 bytes [200 OK]>")
    mock_render.assert_called_with(
        'weko_admin/email_templates/site_license_report.html',
        administrator=None,
        agg_date="2024-04-2024-05",
        organization_name='ORCID',
        site_name_en='new_name1', 
        site_name_ja='new_name1'
    )
    with patch("weko_admin.api.get_system_default_language",side_effect=Exception("test_error")):
        send_site_license_mail(organization_name,mail_list,result,data)

class MockRedisHash:
    def __init__(self):
        self.data = {}
    
    def hset(self,name,key,value):
        if name not in self.data:
            self.data[name] = {}
        self.data[name][key]=value
    
    def hdel(self,name,key):
        self.data[name].pop(key)
    
    def hget(self,name,key):
        return bytes(self.data[name][key],"utf-8")
    
    def hgetall(self,name):
        return {bytes(x,"utf-8"):bytes(y,"utf-8") for x,y in self.data[name].items()}

# class TempDirInfo(object):
class TestTempDirInfo:
#    def __init__(cls, key=None) -> None:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::TestTempDirInfo::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_init(self,client,redis_connect,mocker):
        mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
        temp = TempDirInfo()
        assert temp.key=="cache::temp_dir_info"
        
        temp = TempDirInfo("test_key")
        assert temp.key=="test_key"


#    def set(cls, temp_path, extra_info=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::TestTempDirInfo::test_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_set(self,client,mocker):
        mock_redis = MockRedisHash()
        mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=mock_redis)
        temp = TempDirInfo("test_key")
        temp.set("test_temp_path","test_extra_info")
        assert mock_redis.data["test_key"] == {"test_temp_path":"test_extra_info"}


#    def delete(cls, temp_path):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::TestTempDirInfo::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self,client,mocker):
        mock_redis = MockRedisHash()
        mock_redis.hset("test_key","test_path","test_value")
        mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=mock_redis)
        temp = TempDirInfo("test_key")
        temp.delete("test_path")
        assert "test_temp_path" not in mock_redis.data["test_key"]


#    def get(cls, temp_path):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::TestTempDirInfo::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get(self,client,mocker):
        mock_redis = MockRedisHash()
        mock_redis.hset("test_key","test_path",'{"key":"value"}')
        mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=mock_redis)
        temp = TempDirInfo("test_key")
        result = temp.get("test_path")
        assert result == {"key":"value"}


#    def get_all(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::TestTempDirInfo::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all(self,client,mocker):
        mock_redis = MockRedisHash()
        mock_redis.hset("test_key","test_path1",'{"key1":"value1"}')
        mock_redis.hset("test_key","test_path2",'{"key2":"value2"}')
        mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=mock_redis)
        temp = TempDirInfo("test_key")
        result = temp.get_all()
        assert result == {"test_path1":{"key1":"value1"},"test_path2":{"key2":"value2"}}

# def validate_csrf_header(request,csrf_header="X-CSRFToken"):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_api.py::test_validate_csrf_header -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_validate_csrf_header(app, mocker):
    import secrets
    mocker.patch("weko_admin.api.validate_csrf")
    currect_token = secrets.token_hex()
    failed_token = "not_currect_token"
    headers = [
        ("X-CSRFToken",currect_token),
        ("Referer","https://test_server/")
    ]
    with app.test_request_context(headers=headers,environ_overrides={
            'wsgi.url_scheme': 'https'
    }):
        req = request
        validate_csrf_header(request)
    
    # not exist referrer
    headers = [
        ("X-CSRFToken",currect_token),
    ]
    with app.test_request_context(headers=headers,environ_overrides={
            'wsgi.url_scheme': 'https'
    }):
        req = request
        with pytest.raises(CSRFError) as e:
            validate_csrf_header(request)
            assert str(e) == "The referrer header is missing."
    headers = [
        ("X-CSRFToken",currect_token),
        ("Referer","https://test_server_not_correct/")
    ]
    with app.test_request_context(headers=headers,environ_overrides={
            'wsgi.url_scheme': 'https'
    }):
        req = request
        with pytest.raises(CSRFError) as e:
            validate_csrf_header(request)
            assert str(e) == "The referrer does not match the host."

    headers = [
        ("X-CSRFToken",currect_token),
        ("Referer","https://test_server/")
    ]
    with app.test_request_context(headers=headers):
        req = request
        validate_csrf_header(req)

    # validation error in csrf
    mocker.patch("weko_admin.api.validate_csrf",side_effect=ValidationError("test_error"))
    headers = [
        ("X-CSRFToken",failed_token),
    ]
    with app.test_request_context(headers=headers,environ_overrides={
            'wsgi.url_scheme': 'https'
    }):
        req = request
        with pytest.raises(CSRFError) as e:
            validate_csrf_header(request)
            