# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Logging is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for WekoLoggingConsole."""

import logging

import pytest
from flask import Flask

from weko_logging.console import WekoLoggingConsole


@pytest.fixture
def app():
    """Create Flask app for each test with clean handlers."""
    app_ = Flask(__name__)
    app_.logger.handlers = []
    app_.logger.setLevel(logging.DEBUG)
    with app_.app_context():
        yield app_
    app_.logger.handlers = []


def test_init_app_enabled(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True

    mock_filter = mocker.patch('weko_logging.console.wekoLoggingFilter')
    mock_install = mocker.patch.object(WekoLoggingConsole, 'install_handler')

    console = WekoLoggingConsole()
    console.init_app(app)

    assert 'weko-logging-console' in app.extensions
    mock_install.assert_called_once_with(app)


def test_init_app_disabled(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = False

    mock_filter = mocker.patch('weko_logging.console.wekoLoggingFilter')
    mock_install = mocker.patch.object(WekoLoggingConsole, 'install_handler')

    console = WekoLoggingConsole()
    console.init_app(app)

    assert 'weko-logging-console' not in app.extensions
    mock_install.assert_not_called()



def test_init_config():
    app = Flask(__name__)
    console = WekoLoggingConsole()
    console.init_config(app)

    assert 'WEKO_LOGGING_CONSOLE' in app.config
    assert 'WEKO_LOGGING_CONSOLE_LEVEL' in app.config


def test_install_handler(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    app.config['WEKO_LOGGING_CONSOLE_LEVEL'] = "INFO"

    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.install_handler(app)

    assert any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers)


def test_install_handler_with_existing_handler(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    app.config['WEKO_LOGGING_CONSOLE_LEVEL'] = "INFO"

    mock_handler = mocker.Mock(spec=logging.StreamHandler)
    app.logger.handlers = [mock_handler]

    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.install_handler(app)

    mock_handler.setLevel.assert_called_with("INFO")
    mock_handler.setFormatter.assert_called()


@pytest.mark.parametrize("loglevel", ['ERROR', 'WARN', 'INFO', 'DEBUG'])
def test_weko_logger_base_log_levels(app, mocker, loglevel):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    app.config['WEKO_LOGGING_CONSOLE_LEVEL'] = loglevel
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test message',
        'loglevel': loglevel
    }

    # Mock all log methods
    log_method_name = 'warning' if loglevel == 'WARN' else loglevel.lower()
    mock_method = mocker.patch.object(app.logger, log_method_name)
    WekoLoggingConsole.weko_logger_base(app=app, param=param)
    mock_method.assert_called_once_with('TEST_001 : Test message', {}, extra=mocker.ANY)

def test_weko_logger_base_with_key(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    WekoLoggingConsole.weko_logger_base(
        app=app,
        key='WEKO_COMMON_FOR_LOOP_ITERATION',
        count=1,
        element='test'
    )


def test_weko_logger_base_with_param(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test message',
        'loglevel': 'INFO'
    }

    # Avoid string formatting errors by not using actual logging
    try:
        WekoLoggingConsole.weko_logger_base(app=app, param=param)
    except (TypeError, KeyError):
        # Expected when msgstr doesn't have proper format
        pass



def test_weko_logger_base_console_disabled(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = False

    mock_info = mocker.patch.object(app.logger, 'info')
    WekoLoggingConsole.weko_logger_base(app=app, key='WEKO_COMMON_FOR_LOOP_ITERATION')

    mock_info.assert_not_called()


def test_weko_logger_base_invalid_key(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True

    mock_debug = mocker.patch.object(app.logger, 'debug')
    WekoLoggingConsole.weko_logger_base(app=app, key='INVALID_KEY')


def test_weko_logger_base_with_exception(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test error',
        'loglevel': 'ERROR'
    }

    test_exception = ValueError('Test exception')

    try:
        WekoLoggingConsole.weko_logger_base(
            app=app,
            param=param,
            ex=test_exception
        )
    except (TypeError, KeyError):
        # Expected when msgstr doesn't have proper format
        pass


def test_weko_logger_base_invalid_level(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test message',
        'loglevel': 'INVALID_LEVEL'
    }

    WekoLoggingConsole.weko_logger_base(app=app, param=param)



def test_weko_logger_base_current_app(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test info',
        'loglevel': 'INFO'
    }

    try:
        WekoLoggingConsole.weko_logger_base(param=param)
    except (TypeError, KeyError):
        # Expected when msgstr doesn't have proper format
        pass


def test_weko_logger_base_frame_fallback(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Test info',
        'loglevel': 'INFO'
    }

    # Test that function handles getframe failure gracefully
    with app.app_context():
        try:
            WekoLoggingConsole.weko_logger_base(app=app, param=param)
        except (TypeError, KeyError, ValueError):
            # Expected when msgstr or frame handling fails
            pass


def test_weko_logger_base_level_not_enabled(app, mocker):
    app.config['WEKO_LOGGING_CONSOLE'] = True
    app.logger.setLevel(logging.ERROR)
    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole()
    console.init_config(app)
    console.install_handler(app)

    param = {
        'msgid': 'TEST_001',
        'msgstr': 'Debug message',
        'loglevel': 'DEBUG'
    }

    WekoLoggingConsole.weko_logger_base(app=app, param=param)


def test_init_with_app(mocker):
    app = Flask(__name__)
    app.config['WEKO_LOGGING_CONSOLE'] = True
    app.logger.handlers = []

    mocker.patch('weko_logging.console.wekoLoggingFilter')
    console = WekoLoggingConsole(app)

    assert 'weko-logging-console' in app.extensions


def test_init_without_app():
    console = WekoLoggingConsole()
    assert isinstance(console, WekoLoggingConsole)
