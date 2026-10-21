# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Registration of contrib events."""
from flask import current_app
from invenio_search import current_search_client

from invenio_stats.aggregations import StatAggregator, filter_restricted
from invenio_stats.contrib.event_builders import build_celery_task_unique_id, \
    build_file_unique_id, build_item_create_unique_id, \
    build_record_unique_id, build_search_detail_condition, \
    build_search_unique_id, build_top_unique_id, copy_record_index_list, \
    copy_search_keyword, copy_search_type, copy_user_group_list, copy_record_index
from invenio_stats.processors import EventsIndexer, anonymize_user, \
    flag_restricted, flag_robots
from invenio_stats.queries import DateHistogramQuery, TermsQuery, \
    WekoFileStatsQuery, WekoTermsQuery, WekoRankingQuery

from weko_schema_ui.models import PublishStatus

def register_events():
    """Register sample events."""
    return [
        dict(
            event_type='celery-task',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_celery_task_unique_id
                ],
                suffix="%Y",
            )),
        dict(
            event_type='file-download',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_file_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='file-preview',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_file_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='item-create',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_item_create_unique_id
                ],
                suffix="%Y",
            )),
        dict(
            event_type='record-view',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_record_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='top-view',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_top_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='search',
            templates='invenio_stats.contrib.events',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_search_detail_condition,
                    build_search_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            ))
    ]


def register_aggregations():
    """Register sample aggregations."""
    return [dict(
        aggregation_name='celery-task-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='celery-task',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                task_id='task_id',
                task_name='task_name',
                task_state='task_state',
                start_time='start_time',
                end_time='end_time',
                total_records='total_records',
                repository_name='repository_name',
                execution_time='execution_time',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )),
        dict(
            aggregation_name='search-agg',
            templates='invenio_stats.contrib.aggregations',
            aggregator_class=StatAggregator,
            aggregator_config=dict(
                client=current_search_client,
                event='search',
                aggregation_field='unique_id',
                aggregation_interval='day',
                index_interval='year',
                query_modifiers=[filter_restricted],
                copy_fields=dict(
                    country='country',
                    referrer='referrer',
                    search_key=copy_search_keyword,
                    search_type=copy_search_type,
                    site_license_name='site_license_name',
                    site_license_flag='site_license_flag'
                    # count='count',
                ),
                metric_aggregation_fields={
                    'unique_count': ('cardinality', 'unique_session_id',
                                     {'precision_threshold': 1000}),
                },
            )), dict(
        aggregation_name='file-download-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='file-download',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                item_id='item_id',
                item_title='item_title',
                file_key='file_key',
                bucket_id='bucket_id',
                file_id='file_id',
                root_file_id='root_file_id',
                accessrole='accessrole',
                userrole='userrole',
                index_list='index_list',
                index_id='index_id',
                is_billing_item='is_billing_item',
                billing_file_price='billing_file_price',
                user_group_names=copy_user_group_list,
                site_license_name='site_license_name',
                site_license_flag='site_license_flag',
                cur_user_id='cur_user_id',
                hostname='hostname',
                remote_addr='remote_addr',
                is_open_access='is_open_access',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )), dict(
        aggregation_name='file-preview-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='file-preview',
            aggregation_field='unique_id',
            query_modifiers=[filter_restricted],
            aggregation_interval='day',
            index_interval='year',
            copy_fields=dict(
                country='country',
                item_id='item_id',
                item_title='item_title',
                file_key='file_key',
                bucket_id='bucket_id',
                file_id='file_id',
                root_file_id='root_file_id',
                accessrole='accessrole',
                userrole='userrole',
                index_list='index_list',
                index_id='index_id',
                is_billing_item='is_billing_item',
                billing_file_price='billing_file_price',
                user_group_names=copy_user_group_list,
                site_license_name='site_license_name',
                site_license_flag='site_license_flag',
                cur_user_id='cur_user_id',
                hostname='hostname',
                remote_addr='remote_addr',
                is_open_access='is_open_access',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )), dict(
        aggregation_name='item-create-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='item-create',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                cur_user_id='cur_user_id',
                remote_addr='remote_addr',
                pid_type='pid_type',
                pid_value='pid_value',
                record_name='record_name',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        )), dict(
        aggregation_name='record-view-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='record-view',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                remote_addr='remote_addr',
                record_id='record_id',
                record_name='record_name',
                record_index_names=copy_record_index_list,
                record_index_id=copy_record_index,
                pid_type='pid_type',
                pid_value='pid_value',
                cur_user_id='cur_user_id',
                site_license_name='site_license_name',
                site_license_flag='site_license_flag'
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        )), dict(
        aggregation_name='top-view-agg',
        templates='invenio_stats.contrib.aggregations',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='top-view',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                remote_addr='remote_addr',
                site_license_name='site_license_name',
                site_license_flag='site_license_flag'
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        ))]


def register_queries():
    """Register queries."""
    search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX'].strip('-')
    return [
        dict(
            query_name='get-celery-task-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='celery-task',
                aggregated_fields=['task_id', 'task_name', 'start_time',
                                   'end_time', 'total_records', 'task_state'],
                required_filters=dict(
                    task_name='task_name',
                ),
            )
        ),
        dict(
            query_name='get-search-report',
            query_class=WekoTermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='search',
                group_fields=['search_key', 'count'],
            )
        ),
        dict(
            query_name='get-file-download-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
            )
        ),
        dict(
            query_name='get-billing-file-download-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['file_key', 'index_list',
                              'userrole', 'site_license_flag',
                              'user_group_names', 'cur_user_id',
                              'count'],
                required_filters=dict(
                    is_billing_item='is_billing_item',
                ),
            )
        ),
        dict(
            query_name='get-file-download-open-access-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    is_open_access='is_open_access',
                ),
            )
        ),
        dict(
            query_name='get-billing-file-download-open-access-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['file_key', 'index_list',
                              'userrole', 'site_license_flag',
                              'user_group_names', 'cur_user_id',
                              'count'],
                required_filters=dict(
                    is_billing_item='is_billing_item',
                    is_open_access='is_open_access',
                ),
            )
        ),
        dict(
            query_name='get-file-preview-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
            )
        ),
        dict(
            query_name='get-billing-file-preview-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['file_key', 'index_list',
                              'userrole', 'site_license_flag',
                              'user_group_names', 'count'],
                required_filters=dict(
                    is_billing_item='is_billing_item',
                ),
            )
        ),
        dict(
            query_name='get-file-preview-open-access-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    is_open_access='is_open_access'
                    # is_billing_item='is_billing_item',
                ),
            )
        ),
        dict(
            query_name='bucket-file-download-histogram',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                copy_fields=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
                required_filters=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
            )
        ),
        dict(
            query_name='bucket-file-download-total',
            query_class=WekoFileStatsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                copy_fields=dict(),
                main_fields=['bucket_id', 'file_key', 'root_file_id'],
                main_query={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "bucket_id": {
                                                        "value": "@bucket_id",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "term": {
                                                    "file_key": {
                                                        "value": "@file_key",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "must_not": {
                                                        "exists": {
                                                            "field": "root_file_id"
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "root_file_id": {
                                                        "value": "@root_file_id",
                                                        "boost": 1
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            "adjust_pure_negative": True,
                            "boost": 1
                        }
                    }
                },
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='bucket-file-preview-histogram',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                copy_fields=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
                required_filters=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
            )
        ),
        dict(
            query_name='bucket-file-preview-total',
            query_class=WekoFileStatsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                copy_fields=dict(),
                main_fields=['bucket_id', 'file_key', 'root_file_id'],
                main_query={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "bucket_id": {
                                                        "value": "@bucket_id",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "term": {
                                                    "file_key": {
                                                        "value": "@file_key",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "must_not": {
                                                        "exists": {
                                                            "field": "root_file_id"
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "root_file_id": {
                                                        "value": "@root_file_id",
                                                        "boost": 1
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            "adjust_pure_negative": True,
                            "boost": 1
                        }
                    }
                },
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='get-file-download-per-user-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['cur_user_id', 'count'],
            )
        ),
        dict(
            query_name='get-file-preview-per-user-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['cur_user_id', 'count'],
            )
        ),
        dict(
            query_name='get-record-view-report',
            query_class=WekoTermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                group_fields=['record_id', 'record_index_names',
                               'cur_user_id', 'pid_value', 'record_name', 'count'],
            )
        ),
        dict(
            query_name='bucket-record-view-histogram',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                copy_fields=dict(
                    record_id='record_id',
                ),
                required_filters=dict(
                    record_id='record_id',
                ),
            )
        ),
        dict(
            query_name='bucket-record-view-total',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                copy_fields=dict(
                    record_id='record_id',
                ),
                required_filters=dict(
                    record_id='record_id',
                ),
                metric_fields=dict(
                    count=('sum', 'count', {}),
                    unique_count=('sum', 'unique_count', {}),
                ),
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='item-create-total',
            query_class=WekoTermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='item-create',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname', 'cur_user_id'],
            )
        ),
        dict(
            query_name='item-create-per-date',
            query_class=WekoTermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='item-create',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['timestamp', 'pid_value', 'record_name'],
            )
        ),
        dict(
            query_name='item-create-histogram',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='item-create',
                aggregated_fields=['timestamp'],
            )
        ),
        dict(
            query_name='item-detail-total',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname'],
            )
        ),
        dict(
            query_name='get-file-download-per-host-report',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname'],
            )
        ),
        # For query item details (id, name, count)
        dict(
            query_name='item-detail-item-total',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['pid_value', 'record_name'],
            )
        ),
        dict(
            query_name='get-file-download-per-item-report',
            query_class=WekoTermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['item_id', 'item_title'],
            )
        ),
        dict(
            query_name='bucket-item-detail-view-histogram',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                aggregated_fields=['timestamp'],
            )
        ),
        dict(
            query_name='get-file-download-per-time-report',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                aggregated_fields=['timestamp'],
            )
        ),
        dict(
            query_name='top-view-total-per-host',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='top-view',
                group_fields=['remote_addr', 'hostname', 'count']
            )
        ),
        dict(
            query_name='top-view-total',
            query_class=DateHistogramQuery,
            query_config=dict(
                index='stats-index',
                event_type='top-view',
                aggregated_fields=['remote_addr', 'hostname']
            )
        ),
        dict(
            query_name='top-view-total-for-access-counter',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='top-view',
            )
            
        ),
        dict(
            query_name='get-top-view-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='top-view',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-record-view-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-search-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='search',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-file-download-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-file-preview-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-feedback-mail-record-view-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='record-view',
                group_fields=['site_license_name', 'count', 'record_index_id'],
            )
        ),
        dict(
            query_name='get-feedback-mail-file-download-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-download',
                group_fields=['site_license_name', 'count', 'index_id'],
            )
        ),
        dict(
            query_name='get-feedback-mail-file-preview-per-site-license',
            query_class=TermsQuery,
            query_config=dict(
                index='stats-index',
                event_type='file-preview',
                group_fields=['site_license_name', 'count', 'index_id'],
            )
        ),
        dict(
            query_name='get-ranking-data',
            query_class=WekoRankingQuery,
            query_config=dict(
                index='stats-index',
                main_fields=['start_date', 'end_date', 'group_field', 'agg_size', 'count_field'],
                metric_fields=dict(),
                main_query={
                    "size": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "timestamp": {
                                            "gte": "@start_date",
                                            "lte": "@end_date",
                                            "time_zone": "@time_zone"
                                        }
                                    }
                                }
                            ],
                            "must_not": "@must_not"
                        }
                    },
                    "aggs": {
                        "my_buckets": {
                            "terms": {
                                "field": "@group_field",
                                "size": "@agg_size",
                                "order": {
                                    "my_sum": "desc" 
                                }
                            },
                            "aggs": {
                                "my_sum": {
                                    "sum": {
                                        "field": "@count_field" 
                                    }
                                }
                            }
                        }
                    }
                }
            )
        ),
        dict(
            query_name='get-new-items-data',
            query_class=WekoRankingQuery,
            query_config=dict(
                index='weko',
                main_fields=['start_date', 'end_date', 'agg_size'],
                metric_fields=dict(),
                main_query={
                    "size": "@agg_size",
                    "sort": [
                        {
                            "publish_date":{
                                "order": "desc"
                            }
                        }
                    ],
                    "query":{
                        "bool":{
                            "must":[
                                {
                                    "range": {
                                        "publish_date": {
                                            "gte": "@start_date",
                                            "lte": "@end_date"
                                        }
                                    }
                                },
                                {
                                    "term": {
                                        "relation_version_is_last": True
                                    }
                                },
                                {
                                    "terms": {
                                        "publish_status": [
                                            PublishStatus.PUBLIC.value,
                                            PublishStatus.PRIVATE.value
                                        ]
                                    }
                                }
                            ],
                            "must_not": "@must_not"
                        }
                    }
                }
            )
        )
    ]
