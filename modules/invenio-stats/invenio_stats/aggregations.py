# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Aggregation classes."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta
import json
from collections import OrderedDict
import pickle
from functools import wraps

import six
from celery.utils.log import get_task_logger
from dateutil import parser
from flask import current_app
from invenio_search import current_search_client
from invenio_search.engine import dsl, search
from invenio_search.utils import prefix_index
from invenio_db import db

from .models import StatsAggregation, StatsBookmark

SUPPORTED_INTERVALS = OrderedDict([
    ('hour', '%Y-%m-%dT%H'),
    ('day', '%Y-%m-%d'),
    ('month', '%Y-%m'),
    ('year', '%Y')
])


def filter_robots(query):
    """Modify an search query so that robot events are filtered out."""
    return query.filter('term', is_robot=False)


def filter_restricted(query):
    """Add term filter to query for checking restricted users."""
    return query.filter('term', is_restricted=False)


def format_range_dt(dt, interval):
    """Format range filter datetime to the closest aggregation interval."""
    dt_rounding_map = {
        'hour': 'h', 'day': 'd', 'month': 'M', 'year': 'y'}

    if not isinstance(dt, six.string_types):
        dt = dt.replace(microsecond=0).isoformat()
    return '{0}||/{1}'.format(dt, dt_rounding_map[interval])


class BookmarkAPI:
    """Bookmark API class.

    It provides an interface that lets us interact with a bookmark.
    """

    def __init__(self, agg_type, agg_interval):
        """Construct bookmark instance.

        :param agg_type: aggregation type for the bookmark
        """
        # NOTE: doc_type is going to be deprecated with ES_7
        self.bookmark_index = prefix_index('stats-bookmarks')
        self.agg_type = agg_type
        self.agg_interval = agg_interval

    def set_bookmark(self, value):
        """Set bookmark for starting next aggregation."""
        _id = self.agg_type
        _source = {'date': value, 'aggregation_type': self.agg_type}

        # Save stats bookmark into Database.
        StatsBookmark.save(dict(
            _id=_id,
            _index=self.bookmark_index,
            # stats_bookmark.type is NOT NULL
            _type='aggregation-bookmark',
            _source=_source,
        ), delete=True)
        self.new_timestamp = None

    def get_bookmark(self, refresh_time=60):
        """Get last aggregation date."""
        # retrieve the oldest bookmark
        db_bookmark = (
            StatsBookmark.query.filter_by(source_id=self.agg_type)
            .order_by(StatsBookmark.date.desc()).first()
        )

        if db_bookmark:
            source = db_bookmark.source
            if isinstance(source, str):
                source = json.loads(source)
            source_date = source['date']
            try:
                my_date = datetime.fromisoformat(source_date)
            except ValueError:
                # This one is for backwards compatibility, when the bookmark did not have the time
                my_date = datetime.strptime(
                    source_date, "%Y-%m-%dT%H:%M:%S"
                )
            # By default, the bookmark returns a slightly sooner date, to make sure that documents
            # that had arrived before the previous run and where not indexed by the engine are caught in this run
            # This means that some events might be processed twice
            if refresh_time:
                my_date -= timedelta(seconds=refresh_time)
            return my_date

    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List bookmarks."""
        query = StatsBookmark.get_by_source_id(self.agg_type, start_date, end_date)

        if query:
            query = sorted(query, key=lambda x: x.date, reverse=True)

            if limit:
                query = query[:limit]

        return query


class StatAggregator(object):
    """Generic aggregation class.

    This aggregation class queries search events and creates a new
    search document for each aggregated day/month/year... This enables
    to "compress" the events and keep only relevant information.

    The expected events shoud have at least those two fields:

    .. code-block:: json

        {
            "timestamp": "<ISO DATE TIME>",
            "field_on_which_we_aggregate": "<A VALUE>"
        }

    The resulting aggregation documents will be of the form:

    .. code-block:: json

        {
            "timestamp": "<ISO DATE TIME>",
            "field_on_which_we_aggregate": "<A VALUE>",
            "count": "<NUMBER OF OCCURENCE OF THIS EVENT>",
            "field_metric": "<METRIC CALCULATION ON A FIELD>"
        }

    This aggregator saves a bookmark document after each run. This bookmark
    is used to aggregate new events without having to redo the old ones.
    """

    def __init__(self, name, event, client=None,
                 aggregation_field=None,
                 metric_aggregation_fields=None,
                 copy_fields=None,
                 query_modifiers=None,
                 aggregation_interval='month',
                 index_interval='month', batch_size=7):
        """Construct aggregator instance.

        :param event: aggregated event.
        :param client: search client.
        :param aggregation_field: field on which the aggregation will be done.
        :param metric_aggregation_fields: dictionary of fields on which a
            metric aggregation will be computed. The format of the dictionary
            is "destination field" ->
            tuple("metric type", "source field", "metric_options").
        :param copy_fields: list of fields which are copied from the raw events
            into the aggregation.
        :param query_modifiers: list of functions modifying the raw events
            query. By default the query_modifiers are [filter_robots].
        :param aggregation_interval: aggregation time window. default: month.
        :param index_interval: time window of the search indices which
            will contain the resulting aggregations.
        :param batch_size: max number of days for which raw events are being
            fetched in one query. This number has to be coherent with the
            aggregation_interval.
        """
        self.name = name
        self.client = client or current_search_client
        self.event = event
        self.search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX']. \
            strip('-')
        self.aggregation_alias = prefix_index('stats-index')
        self.bookmark_alias = '{0}-stats-{1}-bookmark'.format(
            self.search_index_prefix, self.event)
        self.aggregation_field = aggregation_field
        self.metric_aggregation_fields = metric_aggregation_fields or {}
        self.allowed_metrics = {
            'cardinality', 'min', 'max', 'avg', 'sum', 'extended_stats',
            'geo_centroid', 'percentiles', 'stats'}
        if any(v not in self.allowed_metrics
               for k, (v, _, _) in (metric_aggregation_fields or {}).items()):
            raise(ValueError('Metric aggregation type should be one of [{}]'
                             .format(', '.join(self.allowed_metrics))))

        self.copy_fields = copy_fields or {}
        self.aggregation_interval = aggregation_interval
        self.index_interval = index_interval
        self.query_modifiers = (query_modifiers if query_modifiers is not None
                                else [filter_robots])
        self.supported_intervals = SUPPORTED_INTERVALS
        self.dt_rounding_map = {
            'hour': 'h', 'day': 'd', 'month': 'M', 'year': 'y'}
        if list(self.supported_intervals.keys()).index(aggregation_interval) \
                > \
                list(self.supported_intervals.keys()).index(index_interval):
            raise(ValueError('Aggregation interval should be'
                             ' shorter than index interval'))
        self.index_name_suffix = self.supported_intervals[index_interval]
        self.doc_id_suffix = self.supported_intervals[aggregation_interval]
        self.batch_size = batch_size
        self.event_index = prefix_index('events-stats-index')
        self.indices = set()
        self.bookmark_api = BookmarkAPI(self.name, self.aggregation_interval)

    @property
    def aggregation_doc_type(self):
        """Get document type for the aggregation."""
        return '{0}-{1}-aggregation'.format(
            self.event, self.aggregation_interval)

    def _get_oldest_event_timestamp(self):
        """Search for the oldest event timestamp."""
        # Retrieve the oldest event in order to start aggregation
        # from there
        query_events = dsl.Search(
            using=self.client,
            index=self.event_index
        ).filter('term', event_type=self.event)[0:1].sort(
            {'timestamp': {'order': 'asc'}}
        )
        result = query_events.execute()

        # There might not be any events yet if the first event have been
        # indexed but the indices have not been refreshed yet.
        if len(result) == 0:
            return None
        return parser.parse(result[0]['timestamp'])

    def agg_iter(self, lower_limit=None, upper_limit=None, manual=False):
        """Aggregate and return dictionary to be indexed in the search engine."""
        logger = get_task_logger(__name__)

        lower_limit = (
            lower_limit
            or self.bookmark_api.get_bookmark()
            or self._get_oldest_event_timestamp()
        )
        upper_limit = upper_limit or (
            datetime.utcnow().replace(microsecond=0).isoformat())
        aggregation_data = {}

        self.agg_query = dsl.Search(using=self.client,
                                index=self.event_index).\
            filter('term', event_type=self.event).\
            filter('range', timestamp={
                'gte': format_range_dt(lower_limit, self.aggregation_interval),
                'lte': format_range_dt(upper_limit, self.aggregation_interval)})

        # apply query modifiers
        for modifier in self.query_modifiers:
            self.agg_query = modifier(self.agg_query)

        hist = self.agg_query.aggs.bucket(
            'histogram',
            'date_histogram',
            field='timestamp',
            interval=self.aggregation_interval
        )
        terms = hist.bucket(
            'terms', 'terms', field=self.aggregation_field,
            size=current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        )
        # FIXME: Paginate?
        top = terms.metric(
            'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
        )
        for dst, (metric, src, opts) in self.metric_aggregation_fields.items():
            terms.metric(dst, metric, field=src, **opts)
        logger.debug("agg_query query: {}".format(self.agg_query))
        results = self.agg_query.execute()
        logger.debug("agg_query result: {}".format(len(results)))
        for interval in results.aggregations['histogram'].buckets:
            interval_date = datetime.strptime(
                interval['key_as_string'], '%Y-%m-%dT%H:%M:%S')
            for aggregation in interval['terms'].buckets:
                aggregation_data['timestamp'] = interval_date.isoformat()
                aggregation_data[self.aggregation_field] = aggregation['key']
                aggregation_data['count'] = aggregation['doc_count']
                aggregation_data['event_type'] = self.event

                if self.metric_aggregation_fields:
                    for f in self.metric_aggregation_fields:
                        aggregation_data[f] = aggregation[f]['value']

                # opensearch-dsl AttrDict has no .get(); use a plain dict.
                doc = aggregation.top_hit.hits.hits[0]['_source'].to_dict()
                for destination, source in self.copy_fields.items():
                    if isinstance(source, six.string_types):
                        if source == 'root_file_id' and source not in doc:
                            if 'file_id' in doc:
                                aggregation_data[destination] = doc['file_id']
                        else:
                            aggregation_data[destination] = doc.get(source, '')
                    else:
                        aggregation_data[destination] = source(
                            doc,
                            aggregation_data
                        )

                index_name = self.aggregation_alias
                logger.debug("index_name: {}".format(index_name))

                if manual:
                    res = dsl.Search(using=self.client,
                                 index=index_name).\
                        filter('term', unique_id=aggregation['key']).\
                        filter('term', event_type=self.event).\
                        execute()
                    
                    if res.hits.total.value > 0:
                        index_name = res.hits.hits[0]['_index']

                rtn_data = dict(
                    _id='{0}'.format(aggregation['key']),
                    _index=index_name,
                    _source=aggregation_data
                )
                self.indices.add(index_name)
                if current_app.config['STATS_WEKO_DB_BACKUP_AGGREGATION']:
                    # Save stats aggregation into Database.
                    StatsAggregation.save(
                        dict(rtn_data, _type=self.aggregation_doc_type),
                        delete=True)

                yield rtn_data

    def run(self, start_date=None, end_date=None, update_bookmark=True, manual=False):
        """Calculate statistics aggregations."""
        # If no events have been indexed there is nothing to aggregate
        if not dsl.Index(self.event_index, using=self.client).exists():
            return
        logger = get_task_logger(__name__)
        lower_limit = (
            start_date
            or self.bookmark_api.get_bookmark()
            or self._get_oldest_event_timestamp()
        )
        logger.debug("lower_limit: {}".format(lower_limit))
        # Stop here if no bookmark could be estimated.
        if lower_limit is None:
            return
        upper_limit = min(
            end_date or datetime.max,  # ignore if `None`
            datetime.utcnow().replace(microsecond=0),
            datetime.combine(
                lower_limit + timedelta(self.batch_size),
                datetime.min.time())
        )
        logger.debug("upper_limit: {}".format(upper_limit))
        while upper_limit <= datetime.utcnow():
            self.indices = set()
            search.helpers.bulk(self.client,
                 self.agg_iter(lower_limit, upper_limit, manual),
                 stats_only=True,
                 chunk_size=50)
            # Flush all indices which have been modified
            current_search_client.indices.flush(
                index=','.join(self.indices),
                wait_if_ongoing=True
            )
            if update_bookmark:
                self.bookmark_api.set_bookmark(
                    upper_limit.strftime(self.doc_id_suffix)
                    or datetime.utcnow().strftime(self.doc_id_suffix)
                )
            self.indices = set()
            lower_limit = lower_limit + timedelta(self.batch_size)
            upper_limit = min(
                end_date or datetime.max,  # ignore if `None``
                datetime.utcnow().replace(microsecond=0),
                lower_limit + timedelta(self.batch_size)
            )
            if lower_limit > upper_limit:
                break

    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List the aggregation's bookmarks."""
        return self.bookmark_api.list_bookmarks(start_date, end_date, limit)

    def delete(self, start_date=None, end_date=None):
        """Delete aggregation documents."""
        aggs_query = dsl.Search(
            using=self.client,
            index=self.aggregation_alias
        ).filter('term', event_type=self.event).extra(_source=False)

        range_args = {}
        if start_date:
            range_args['gte'] = format_range_dt(
                start_date.replace(microsecond=0), self.aggregation_interval)
        if end_date:
            range_args['lte'] = format_range_dt(
                end_date.replace(microsecond=0), self.aggregation_interval)
        if range_args:
            aggs_query = aggs_query.filter('range', timestamp=range_args)

        def _delete_actions():
            affected_indices = set()
            for doc in aggs_query.scan():
                affected_indices.add(doc.meta.index)
                yield dict(_index=doc.meta.index,
                           _op_type='delete',
                           _id=doc.meta.id)
            current_search_client.indices.flush(
                index=','.join(affected_indices), wait_if_ongoing=True)

        # Bookmarks are stored in the database (stats_bookmark).
        bookmark_query = StatsBookmark.query.filter_by(source_id=self.name)
        if start_date:
            bookmark_query = bookmark_query.filter(
                StatsBookmark.date >= start_date)
        if end_date:
            bookmark_query = bookmark_query.filter(
                StatsBookmark.date <= end_date)
        bookmark_query.delete(synchronize_session=False)

        search.helpers.bulk(self.client, _delete_actions(), refresh=True)
        db.session.commit()
