# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test celery task."""

import uuid
from unittest.mock import patch

from invenio_indexer.tasks import delete_record, index_record, process_bulk_queue


# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_tasks.py::test_process_bulk_queue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-indexer/.tox/c1/tmp
def test_process_bulk_queue(app):
    """Test index records."""
    with patch("invenio_indexer.api.RecordIndexer.process_bulk_queue") as fun:
        process_bulk_queue()
        assert fun.called


# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_tasks.py::test_index_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-indexer/.tox/c1/tmp
def test_index_record(app):
    """Test index records."""
    with patch("invenio_indexer.api.RecordIndexer.index_by_id") as fun:
        recid = str(uuid.uuid4())
        index_record(recid)
        fun.assert_called_with(recid)


# .tox/c1/bin/pytest --cov=invenio_indexer tests/test_tasks.py::test_delete_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-indexer/.tox/c1/tmp
def test_delete_record(app):
    """Test index records."""
    with patch("invenio_indexer.api.RecordIndexer.delete_by_id") as fun:
        recid = str(uuid.uuid4())
        delete_record(recid)
        fun.assert_called_with(recid)
