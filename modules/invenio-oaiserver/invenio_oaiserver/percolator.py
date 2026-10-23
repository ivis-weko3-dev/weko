# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

from __future__ import absolute_import, print_function

from invenio_indexer.api import RecordIndexer
from invenio_search import current_search, current_search_client
from invenio_search.utils import build_alias_name
from weko_search_ui.config import INDEXER_DEFAULT_INDEX

from flask import current_app

from .models import OAISet
from .proxies import current_oaiserver
from .query import query_string_parser


def _create_percolator_mapping(index):
    """Update mappings with the percolator field.

    .. note::

        Percolators are a special type of field inside mappings.
    """
    current_search_client.indices.put_mapping(
        index=index, body=PERCOLATOR_MAPPING, ignore=[400, 404])


def _percolate_query(index, document):
    """Get results for a percolate query."""
    results = current_search_client.search(
        index=index, allow_no_indices=True,
        ignore_unavailable=True, body={
            'query': {
                'percolate': {
                    'field': 'query',
                    'document': document,
                }
            }
        }
    )
    return results['hits']['hits']


PERCOLATOR_MAPPING = {
    'properties': {'query': {'type': 'percolator'}}
}


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()
        for index in current_search.mappings.keys():
            # TODO: Consider doing this only once in app initialization
            if index == INDEXER_DEFAULT_INDEX:
                index = build_alias_name(index)
                _create_percolator_mapping(index)
                current_search_client.index(
                    index=index,
                    id='oaiset-{}'.format(spec),
                    body={'query': query}
                )


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the new oaiset."""
    if spec:
        for index in current_search.mappings.keys():
            if index == INDEXER_DEFAULT_INDEX:
                index = build_alias_name(index)
                _create_percolator_mapping(index)
                current_search_client.delete(
                    index=index,
                    id='oaiset-{}'.format(spec), ignore=[404]
                )


def _build_cache():
    """Build sets cache."""
    sets = current_oaiserver.sets
    if sets is None:
        # build sets cache
        sets = current_oaiserver.sets = [
            oaiset.spec for oaiset in OAISet.query.filter(
                OAISet.search_pattern.is_(None)).all()]
    return sets


def get_record_sets(record):
    """Find matching sets."""
    # get lists of sets with search_pattern equals to None but already in the
    # set list inside the record
    record_sets = set(record.get('_oai', {}).get('sets', []))
    for spec in _build_cache():
        if spec in record_sets:
            yield spec

    # get list of sets that match using percolator
    index = RecordIndexer().record_to_index(record)
    document = record.dumps()

    _create_percolator_mapping(index)
    results = _percolate_query(index, document)
    prefix = 'oaiset-'
    prefix_len = len(prefix)
    for match in results:
        set_name = match['_id']
        if set_name.startswith(prefix):
            name = set_name[prefix_len:]
            yield name.split(':')[-1]