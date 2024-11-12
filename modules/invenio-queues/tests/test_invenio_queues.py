# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import sys
import os
import invenio_queues
from unittest.mock import patch
# テストディレクトリをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import pytest
from conftest import MOCK_MQ_EXCHANGE, mock_iter_entry_points_factory
from flask import Flask
from pkg_resources import EntryPoint
from invenio_queues.proxies import current_queues
from invenio_queues import InvenioQueues, current_queues
from invenio_queues.errors import DuplicateQueueError
from invenio_queues.queue import Queue
from conftest import MOCK_MQ_EXCHANGE, mock_iter_entry_points_factory
from invenio_queues.proxies import current_queues
from kombu import Connection, Exchange, Queue, exceptions

MOCK_MQ_EXCHANGE = Exchange(
    "test_events",
    type="direct",
    delivery_mode="transient",  # in-memory queue
    durable=True,
)

def ensure_connection(conn, retries=5, delay=2):
    """Ensure connection with retries."""
    for _ in range(retries):
        try:
            conn.connect()
            return
        except exceptions.OperationalError:
            time.sleep(delay)
    raise exceptions.OperationalError("Failed to connect after retries")

def test_version():
    """Test version import."""
    from invenio_queues import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioQueues(app)
    assert "invenio-queues" in app.extensions

    app = Flask("testapp")
    ext = InvenioQueues()
    assert "invenio-queues" not in app.extensions
    ext.init_app(app)
    assert "invenio-queues" in app.extensions


def test_duplicate_queue(app):
    """Check that duplicate queues raise an exception."""
    with app.app_context():
        data = []
        for idx in range(2):
            queue_name = "myqueue"
            entrypoint = EntryPoint(queue_name, queue_name)
            conf = dict(name=queue_name, exchange=MOCK_MQ_EXCHANGE)
            entrypoint.load = lambda conf=conf: (lambda: [conf])
            data.append(entrypoint)

        entrypoints = mock_iter_entry_points_factory(data)

        with patch("pkg_resources.iter_entry_points", entrypoints):
            with pytest.raises(DuplicateQueueError):
                current_queues.queues()


with_different_brokers = pytest.mark.parametrize(
    "config",
    [
        # test with default connection pool
        {},
        # test with in memory broker as the exception is not the same
        {"QUEUES_BROKER_URL": "memory://"},
        {"QUEUES_BROKER_URL": "amqp://guest:guest@rabbitmq:5672//"},
        {"QUEUES_BROKER_URL": "redis://redis:6379//"},
    ],
)
"""Test with standard and in memory broker."""


@with_different_brokers
def test_publish_and_consume(app, test_queues, config):
    """Test queue.publish and queue.consume."""
    app.config.update(config)
    with app.app_context():
        broker_url = app.config.get("QUEUES_BROKER_URL")
        queue = current_queues.queues[test_queues[0]["name"]]
        queue.publish([1, 2, 3])
        queue.publish([4, 5])
        assert list(queue.consume()) == [1, 2, 3, 4, 5]


@with_different_brokers
def test_queue_exists(app, test_queues_entrypoints, config):
    """Test the "declare" CLI."""
    app.config.update(config)
    with app.app_context():
        broker_url = app.config.get("QUEUES_BROKER_URL")
        conn = Connection(broker_url)
        ensure_connection(conn)
        for queue in current_queues.queues.values():
            assert not queue.exists
        current_queues.declare()
        for queue in current_queues.queues.values():
            # NOTE: skip existence check for redis since is not supported
            if broker_url.startswith("redis"):
                continue
            assert queue.exists


@with_different_brokers
def test_routing(app, test_queues, config):
    """Test basic routing of messages."""
    app.config.update(config)
    with app.app_context():
        broker_url = app.config.get("QUEUES_BROKER_URL")
        q0 = current_queues.queues[test_queues[0]["name"]]
        q1 = current_queues.queues[test_queues[1]["name"]]
        q0.publish([{"event": "0"}])
        q1.publish([{"event": "1"}])

        assert list(q0.consume()) == [{"event": "0"}]
        assert list(q1.consume()) == [{"event": "1"}]
