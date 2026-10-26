# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging admin view."""

from celery import states
from flask import current_app, jsonify, abort
from flask.helpers import url_for
from flask_admin import BaseView, expose
from flask_babel import gettext as _

from invenio_files_rest.models import FileInstance
from weko_logging.utils import UserActivityLogUtils
from weko_logging.tasks import export_all_user_activity_logs
from weko_search_ui.tasks import check_celery_is_run
from weko_redis.redis import RedisConnection

class ExportLogAdminView(BaseView):
    """Export user activity log view."""

    @expose('/', methods=['GET'])
    def index(self):
        """Log export admin view.

        Returns:
            str: Log export admin view template.
        """
        return self.render(
            current_app.config['WEKO_LOGGING_LOG_EXPORT_TEMPLATE']
        )

    @expose('/export', methods=['POST'])
    def export_user_activity_log(self):
        """Start export user activity log task.

        Returns:
            str: Response (export task id).
        """
        # get current task running
        task_status = UserActivityLogUtils.get_export_task_status()
        if task_status and task_status.get('task_id'):
            is_deleted = self.is_celery_task_meta_missing(task_status.get('task_id'))
            if not is_deleted:
                task = export_all_user_activity_logs.AsyncResult(
                    task_status.get('task_id')
                )

                if task.state == states.PENDING or task.state == states.STARTED:
                    return jsonify({
                        'code': 409,
                        'data': {'message': _('Export task is running.')}
                    })

        UserActivityLogUtils.clear_export_status()
        task = export_all_user_activity_logs.delay()
        UserActivityLogUtils.set_export_status(task_id=task.id)
        return jsonify({
            'code': 200,
            'data': {'task_id': task.id}
        })

    @expose('/check_export_status', methods=['GET'])
    def check_export_status(self):
        """API check export status.

        Returns:
            str: Response (export status).
        """
        status = UserActivityLogUtils.get_export_task_status()
        check = check_celery_is_run()
        status['celery_is_run'] = check
        if status and status.get('task_id'):
            task = export_all_user_activity_logs.AsyncResult(
                status.get('task_id')
            )
            status['status'] = task.status

            if task.successful():
                url_info = UserActivityLogUtils.get_export_url()
                status.update(url_info)
            elif task.failed():
                status['error'] = 'export failed'

        # set download_link
        status['download_link'] = ""
        if status.get('file_uri'):
            status['download_link'] = url_for(
                'logs/export.download_user_activity_log', _external=True)

        if 'file_uri' in status:
            del status['file_uri']

        return jsonify({
            'code': 200,
            'data': status
        })

    @expose("/cancel_export", methods=["GET"])
    def cancel_export(self):
        """Check export status.

        Returns:
            str: Response (export cancel status).
        """
        result = UserActivityLogUtils.cancel_export_log()
        task_status = UserActivityLogUtils.get_export_task_status()
        status = task_status.get("status", "")
        can_export = status not in ["PENDING", "STARTED"]
        return jsonify(data={
            "cancel_status": result,
            "export_status": can_export,
            "status": status
        })

    @expose("/download", methods=['GET'])
    def download_user_activity_log(self):
        """Download log as zip (includes tsv).

        Returns:
            byte: Log zip file.
        """
        url_info = UserActivityLogUtils.get_export_url()
        if url_info.get('file_uri'):
            file_instance = FileInstance.get_by_uri(url_info.get('file_uri'))
            file_name = "export_log.zip"
            return file_instance.send_file(
                file_name,
                mimetype='application/octet-stream',
                as_attachment=True
            )
        else:
            abort(404)

    def is_celery_task_meta_missing(self, task_id):
        """
        Checks if the Celery task meta information for the given task_id is missing.

        Args:
            task_id (str): Celery task ID.

        Returns:
            bool: True if deleted, otherwise False.
        """
        is_deleted = False
        meta_task_id = "celery-task-meta-{}".format(task_id)
        redis_connection_celery = RedisConnection()
        datastore_celery = redis_connection_celery.connection(db=current_app.config['CELERY_RESULT_BACKEND_DB_NO'], kv = True)
        if not datastore_celery.redis.exists(meta_task_id):
            is_deleted = True
        return is_deleted

log_export_admin_view = {
    "view_class": ExportLogAdminView,
    "kwargs": {
        "category": _("Logs"),
        "name": _("Export"),
        "endpoint": "logs/export",
    }
}
"""Log export admin view."""

__all__ = (
    'log_export_admin_view',
)
