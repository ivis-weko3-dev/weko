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

import sys
import re
import uuid
import json

from flask_wtf import FlaskForm
from flask import abort, current_app, jsonify, flash, request, url_for
from flask_admin import BaseView, expose
from flask_login import current_user
from flask_babelex import gettext as _
from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_records.api import ItemTypes
from weko_admin.models import AdminSettings

from weko_workflow.api import WorkFlow


class WorkSpaceWorkFlowSettingView(BaseView):
    """WorkSpace WorkFlow setting view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        default_workspace_workflowselect_api = { "item_type_id": "30002",
                            "work_flow_id": "1", "workFlow_select_flg":"1"}  # Default

        current_settings = AdminSettings.get(
                name='workspace_workflow_settings',
                dict_to_object=False)
        if not current_settings:  
            AdminSettings.update('workspace_workflow_settings', default_workspace_workflowselect_api)
            current_settings = AdminSettings.get(
                name='workspace_workflow_settings',
                dict_to_object=False)
        current_settings_json = json.dumps(current_settings)
        try:
            form = FlaskForm(request.form)
            item_type_list = ItemTypes.get_latest_with_item_type(True)
            # item_type_list = ItemTypes.get_latest(harvesting_type=False)
            item_type_list = [item for item in item_type_list if item[3] != True]
            workflow = WorkFlow()
            workflows = workflow.get_workflow_list()
            if request.method == 'POST' and form.validate():
                # Process forms
                form = request.form.get('submit', None)
                if form == 'set_workspace_workflow_setting_form':
                    # settings = AdminSettings.get('workspace_workflow_settings')
                    workFlow_select_flg = request.form.get('registrationRadio', '')
                    if workFlow_select_flg == '1':
                        current_settings_json.workFlow_select_flg = '1'
                        current_settings_json.item_type_id = request.form.get('itemType', '')
                    else:
                        current_settings_json.workFlow_select_flg = '0'
                        current_settings_json.work_flow_id = request.form.get('workFlow', '')

                    AdminSettings.update('workspace_workflow_settings',
                                         current_settings_json.__dict__)
                    flash(_('WorkSpace WorkFlow Setting was updated.'), category='success')

            return self.render('weko_workflow/admin/workspace_workflow_setting.html',
                               item_type_list=item_type_list,
                               work_flow_list=workflows,
                               form=form)
        except BaseException:
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
        return abort(400)


workspace_workflow_adminview = {
    'view_class': WorkSpaceWorkFlowSettingView,
    'kwargs': {
        'category': _('WorkFlow'),
        'name': _('WorkSpaceWorkFlow Setting'),
        'endpoint': 'workspaceworkflowsetting'
    }
}


__all__ = (
    'workspace_workflow_adminview',
)
