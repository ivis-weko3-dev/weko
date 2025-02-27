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

"""WEKO3 module docstring."""

# import math
# from typing import List
# import urllib.parse
# import uuid
# import traceback
# from datetime import date,datetime, timedelta

# from flask import abort, current_app, request, session, url_for
# from flask_login import current_user
# from invenio_accounts.models import Role, User, userrole
# from invenio_db import db
# from invenio_pidstore.models import PersistentIdentifier, PIDStatus
# from sqlalchemy import and_, asc, desc, func, or_
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.orm.exc import NoResultFound
# from weko_deposit.api import WekoDeposit
# from weko_records.serializers.utils import get_item_type_name
# from weko_schema_ui.models import PublishStatus
# from weko_index_tree.api import Indexes

from .config import WEKO_WORKFLOW_REQUEST_TIMEOUT, WEKO_WORKFLOW_SYS_HTTP_PROXY, \
    WEKO_WORKFLOW_SYS_HTTPS_PROXY, WEKO_WORKSPACE_CiNii_API_URL, \
    WEKO_WORKSPACE_JALC_API_URL, WEKO_WORKSPACE_DATACITE_API_URL
import requests
# from .models import Action as _Action
# from .models import ActionCommentPolicy, ActionFeedbackMail, \
#     ActionIdentifier, ActionJournal, ActionStatusPolicy
# from .models import Activity as _Activity
# from .models import ActivityAction, ActivityHistory, ActivityStatusPolicy
# from .models import FlowAction as _FlowAction
# from .models import FlowActionRole as _FlowActionRole
# from .models import FlowDefine as _Flow
# from .models import FlowStatusPolicy
# from .models import WorkFlow as _WorkFlow
# from .models import WorkflowRole
# from .models import ActivityCount


class CiNiiURL:
    """The Class retrieves the metadata from CiNii."""

    ENDPOINT = 'doi='
    POST_FIX = '&format=json'
    # Set default value
    _timeout = WEKO_WORKFLOW_REQUEST_TIMEOUT
    _proxy = {
        'http': WEKO_WORKFLOW_SYS_HTTP_PROXY,
        'https': WEKO_WORKFLOW_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init CiNiiURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """Create endpoint.

        :return: endpoint string.
        """
        endpoint_url = self.ENDPOINT + self._doi + self.POST_FIX
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  WEKO_WORKSPACE_CiNii_API_URL + '?' + endpoint
        return url

    @property
    def url(self):
        """URL property.

        :return: Request URL
        """
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """This method retrieves the metadata from CrossRef."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.json()
        except Exception as e:
            response['error'] = str(e)
        return response


class JALCURL:
    """The Class retrieves the metadata from JALC."""

    # ENDPOINT = 'doi='
    # POST_FIX = '&format=json'
    # Set default value
    _timeout = WEKO_WORKFLOW_REQUEST_TIMEOUT
    _proxy = {
        'http': WEKO_WORKFLOW_SYS_HTTP_PROXY,
        'https': WEKO_WORKFLOW_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init JALCURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """Create endpoint.

        :return: endpoint string.
        """
        endpoint_url = self._doi
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  WEKO_WORKSPACE_JALC_API_URL + endpoint
        return url

    @property
    def url(self):
        """URL property.

        :return: Request URL
        """
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """This method retrieves the metadata from CrossRef."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.json()
        except Exception as e:
            response['error'] = str(e)
        return response

class DATACITEURL:
    """The Class retrieves the metadata from JALC."""

    # ENDPOINT = 'doi='
    # POST_FIX = '&format=json'
    # Set default value
    _timeout = WEKO_WORKFLOW_REQUEST_TIMEOUT
    _proxy = {
        'http': WEKO_WORKFLOW_SYS_HTTP_PROXY,
        'https': WEKO_WORKFLOW_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init JALCURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """Create endpoint.

        :return: endpoint string.
        """
        endpoint_url = self._doi
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  WEKO_WORKSPACE_DATACITE_API_URL + endpoint
        return url

    @property
    def url(self):
        """URL property.

        :return: Request URL
        """
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """This method retrieves the metadata from CrossRef."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.json()
        except Exception as e:
            response['error'] = str(e)
        return response
