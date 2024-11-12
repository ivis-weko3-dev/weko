# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from unittest.mock import patch
import invenio_queues
import time
import pytest
from flask import Flask
from kombu import Exchange, Queue, Connection, exceptions
from invenio_queues import InvenioQueues

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

def remove_queues(app):
    """Delete all queues declared on the current app."""
    with app.app_context():
        ext = app.extensions["invenio-queues"]
        for name, queue in ext.queues.items():
            if queue.exists:
                queue.queue.delete()


def mock_iter_entry_points_factory(data):
    """Create a mock iter_entry_points function."""
    from pkg_resources import iter_entry_points

    def entrypoints(group, name=None):
        if group == "invenio_queues.queues":
            for entrypoint in data:
                yield entrypoint
        else:
            for x in iter_entry_points(group=group, name=name):
                yield x

    return entrypoints


@pytest.yield_fixture()
def test_queues_entrypoints(app):
    """Declare some queues by mocking the invenio_queues.queues entrypoint.

    It yields a list like [{name: queue_name, exchange: conf}, ...].
    """
    from pkg_resources import EntryPoint

    data = []
    result = []
    for idx in range(5):
        queue_name = "queue{}".format(idx)
        entrypoint = EntryPoint(queue_name, queue_name)
        conf = dict(name=queue_name, exchange=MOCK_MQ_EXCHANGE)
        entrypoint.load = lambda conf=conf: (lambda: [conf])
        data.append(entrypoint)
        result.append(conf)

    entrypoints = mock_iter_entry_points_factory(data)

    with patch("pkg_resources.iter_entry_points", entrypoints):
        try:
            yield result
        finally:
            remove_queues(app)


@pytest.yield_fixture()
def test_queues(app, test_queues_entrypoints):
    """Declare test queues."""
    with app.app_context():
        ext = app.extensions["invenio-queues"]
        for conf in test_queues_entrypoints:
            queue = ext.queues[conf["name"]]
            queue.queue.declare()
            assert queue.exists
    yield test_queues_entrypoints


@pytest.fixture()
def app():
    """Flask application fixture."""
    from invenio_queues import InvenioQueues
    app_ = Flask("testapp")
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        BROKER_URL="amqp://guest:guest@rabbitmq:5672//",  
        CELERY_BROKER_URL="amqp://guest:guest@rabbitmq:5672//",  
        QUEUES_BROKER_URL="amqp://guest:guest@rabbitmq:5672//" 
    )
    InvenioQueues(app_)
    
    # Ensure connection with retries
    conn = Connection(app_.config['BROKER_URL'])
    ensure_connection(conn)
    
    return app_

@pytest.fixture(autouse=True)
def set_redis_host():
    """Set Redis host to 'redis' instead of 'localhost'."""
    import os
    os.environ['REDIS_HOST'] = 'redis'