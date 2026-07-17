# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test package API."""

from invenio_mail.api import TemplatedMessage, DomainConnection, send_mail
from unittest.mock import patch
from smtplib import SMTPServerDisconnected

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_invenio_mail_api.py::test_TempatedMessage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
def test_TempatedMessage(app,email_params, email_ctx):
    msg = TemplatedMessage(template_body='invenio_mail_test/base.txt',
                               template_html='invenio_mail_test/base.html',
                               ctx=email_ctx, **email_params)
    for key in email_params:
        assert email_params[key] == getattr(msg, key), key

    # let's check that the body and html are correctly formatted
    assert '<p>Dear {0},</p>'.format(email_ctx['user']) in msg.html
    assert 'Dear {0},'.format(email_ctx['user']) in msg.body
    assert '<p>{0}</p>'.format(email_ctx['content']) in msg.html
    assert '{0}'.format(email_ctx['content']) in msg.body
    assert email_ctx['sender'] in msg.html
    assert email_ctx['sender'] in msg.body

    # template_body is None, template_html is None
    msg = TemplatedMessage()
    assert msg.html == None
    assert msg.body == None

# .tox/c1/bin/pytest --cov=invenio_mail tests/test_api.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
def test_send_mail(app, mail_configs, mocker):
    # success mail sending
    mock_send = mocker.patch('flask_mail._Mail.send')
    result = send_mail("test_subject",['test@mail.nii.ac.jp'],"test_body","test_html")
    assert result == None
    args,kwargs=mock_send.call_args
    msg = args[0]
    assert msg.subject == "test_subject"
    assert msg.html == "test_html"

    # failed mail sending
    mock_send = mocker.patch('flask_mail._Mail.send', side_effect=SMTPServerDisconnected())
    result = send_mail("test_subject",['test@mail.nii.ac.jp'],"test_body","test_html")
    assert type(result) == SMTPServerDisconnected
    args,kwargs=mock_send.call_args
    msg = args[0]
    assert msg.subject == "test_subject"
    assert msg.html == "test_html"


class _FakeMail:
    """Connection.configure_host が参照する属性を持つダミーのMailオブジェクト。"""

    def __init__(self, server="mail.example.com", port=25, use_ssl=False,
                 use_tls=False, local_hostname=None, debug=0,
                 username=None, password=None):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl
        self.use_tls = use_tls
        self.local_hostname = local_hostname
        self.debug = debug
        self.username = username
        self.password = password


class TestDomainConnection:

    # .tox/c1/bin/pytest --cov=invenio_mail tests/test_api.py::TestDomainConnection::test_configure_host -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-mail/.tox/c1/tmp
    def test_configure_host(self, mocker):
        # use_ssl=True, local_hostname="myhost" -> SMTP_SSLにlocal_hostnameを渡す
        mock_host = mocker.Mock()
        mock_ssl = mocker.patch(
            "invenio_mail.api.smtplib.SMTP_SSL", return_value=mock_host)
        mail = _FakeMail(server="mail.example.com", port=465,
                          use_ssl=True, local_hostname="myhost")
        conn = DomainConnection(mail)
        host = conn.configure_host()
        mock_ssl.assert_called_once_with(
            "mail.example.com", 465, local_hostname="myhost")
        assert host is mock_host
        mock_host.set_debuglevel.assert_called_once_with(0)
        mock_host.starttls.assert_not_called()
        mock_host.login.assert_not_called()

        # use_ssl=True, local_hostname=None -> local_hostnameを渡さない
        mock_host = mocker.Mock()
        mock_ssl = mocker.patch(
            "invenio_mail.api.smtplib.SMTP_SSL", return_value=mock_host)
        mail = _FakeMail(use_ssl=True, local_hostname=None)
        conn = DomainConnection(mail)
        host = conn.configure_host()
        mock_ssl.assert_called_once_with(mail.server, mail.port)
        assert host is mock_host

        # use_ssl=False, local_hostname="test.example.com" -> SMTPにlocal_hostnameを渡す
        mock_host = mocker.Mock()
        mock_smtp = mocker.patch(
            "invenio_mail.api.smtplib.SMTP", return_value=mock_host)
        mail = _FakeMail(use_ssl=False, local_hostname="test.example.com")
        conn = DomainConnection(mail)
        host = conn.configure_host()
        mock_smtp.assert_called_once_with(
            mail.server, mail.port, local_hostname="test.example.com")
        assert host is mock_host

        # use_ssl=False, local_hostname=None -> local_hostnameを渡さない
        mock_host = mocker.Mock()
        mock_smtp = mocker.patch(
            "invenio_mail.api.smtplib.SMTP", return_value=mock_host)
        mail = _FakeMail(use_ssl=False, local_hostname=None)
        conn = DomainConnection(mail)
        host = conn.configure_host()
        mock_smtp.assert_called_once_with(mail.server, mail.port)
        assert host is mock_host

        # use_tls=True -> starttls()が呼ばれる
        mock_host = mocker.Mock()
        mocker.patch("invenio_mail.api.smtplib.SMTP", return_value=mock_host)
        mail = _FakeMail(use_tls=True)
        conn = DomainConnection(mail)
        conn.configure_host()
        mock_host.starttls.assert_called_once()

        # username/passwordが設定されている場合 -> login()が呼ばれる
        mock_host = mocker.Mock()
        mocker.patch("invenio_mail.api.smtplib.SMTP", return_value=mock_host)
        mail = _FakeMail(username="user", password="pass")
        conn = DomainConnection(mail)
        conn.configure_host()
        mock_host.login.assert_called_once_with("user", "pass")

        # debugの値がintに変換されset_debuglevelに渡る
        mock_host = mocker.Mock()
        mocker.patch("invenio_mail.api.smtplib.SMTP", return_value=mock_host)
        mail = _FakeMail(debug=True)
        conn = DomainConnection(mail)
        conn.configure_host()
        mock_host.set_debuglevel.assert_called_once_with(1)
