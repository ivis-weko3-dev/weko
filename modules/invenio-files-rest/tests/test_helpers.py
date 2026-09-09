# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Storage module tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_files_rest.helpers import make_path, to_s3_uri


@pytest.mark.parametrize(
    'fileurl, expected',
    [
        (
            'https://s3.us-east-1.amazonaws.com/bucket_name/file_name',
            's3://bucket_name/file_name',
        ),
        (
            'https://s3.us-east-1.amazonaws.com/'
            'bucket_name/folder/sub/file_name',
            's3://bucket_name/folder/sub/file_name',
        ),
        (
            'https://bucket_name.s3.us-east-1.amazonaws.com/file_name',
            's3://bucket_name/file_name',
        ),
        (
            'https://bucket_name.s3.us-east-1.amazonaws.com/'
            'folder/sub/file_name',
            's3://bucket_name/folder/sub/file_name',
        ),
        (
            # Legacy AWS region-encoded host:
            # <bucket>.s3-<region>.amazonaws.com
            'https://bucket_name.s3-us-west-2.amazonaws.com/file_name',
            's3://bucket_name/file_name',
        ),
    ],
    ids=[
        'path-style AWS standard',
        'path-style nested key',
        'virtual-hosted standard',
        'virtual-hosted nested key',
        'legacy AWS region-encoded host',
    ],
)
def test_to_s3_uri(fileurl, expected):
    """Test https:// -> s3:// conversion for S3 Virtual Host locations.

    Only covers URLs that ``LocationModelView.validate_uri``
    (``modules/invenio-files-rest/invenio_files_rest/admin.py``) actually
    allows to be saved for a ``FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE``
    Location -- see ``test_to_s3_uri_known_limitations`` below for the
    inputs that are rejected precisely because this function cannot
    handle them correctly.
    """
    assert to_s3_uri(fileurl) == expected


@pytest.mark.parametrize(
    'fileurl, misinterpreted_as',
    [
        (
            # Bucket name starting with "s3" (virtual-hosted): the whole
            # URL starts with "https://s3", so this is misread as a
            # bucket-less path-style URL and the bucket name is lost.
            'https://s3-assets.s3.us-east-1.amazonaws.com/file_name',
            's3://file_name',
        ),
        (
            # Bucket name containing dots (virtual-hosted): only the
            # first dot-separated label is taken as the bucket.
            'https://my.bucket.name.s3.amazonaws.com/file_name',
            's3://my/file_name',
        ),
    ],
    ids=[
        'bucket name starting with s3 (virtual-hosted)',
        'bucket name containing dots',
    ],
)
def test_to_s3_uri_known_limitations(fileurl, misinterpreted_as):
    """Document the known cases this function gets wrong.

    ``LocationModelView.validate_uri`` rejects Location URIs that would
    hit these cases at save time, so a saved Location never triggers
    this in practice.
    """
    assert to_s3_uri(fileurl) == misinterpreted_as


def test_make_path():
    """Test path for files."""
    myid = 'deadbeef-dead-dead-dead-deaddeafbeef'
    base = '/base'
    f = 'data'

    assert make_path(base, myid, f, 1, 1) == \
        '/base/d/eadbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 3, 1) == \
        '/base/d/e/a/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 1, 3) == \
        '/base/dea/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 2, 2) == \
        '/base/de/ad/beef-dead-dead-dead-deaddeafbeef/data'

    pytest.raises(AssertionError, make_path, base, myid, f, 1, 50)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 1)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 50)
