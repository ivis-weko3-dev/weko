import pytest

from flask import Flask

from weko_admin.logger import WEKO_ADMIN_MESSAGE, weko_logger


# .tox/c1/bin/pytest --cov=weko_admin tests/test_logger.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_admin tests/test_logger.py::test_message_resource -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_message_resource():
    assert all([isinstance(v, dict) for v in WEKO_ADMIN_MESSAGE.values()])
    assert all(set(v.keys()) == {"msgid", "msgstr", "loglevel"} for v in WEKO_ADMIN_MESSAGE.values())


# .tox/c1/bin/pytest --cov=weko_admin tests/test_logger.py::test_weko_logger_key_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_weko_logger_key_exists(base_logger):
    app, mock_logger = base_logger
    param = WEKO_ADMIN_MESSAGE.get(key:='WEKO_ADMIN_FAILED_FEEDBACK_ADDRESS_SET')

    weko_logger(key=key)

    mock_logger.assert_called_once_with(app=app, param=param, ex=None)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_logger.py::test_weko_logger_with_kwargs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_weko_logger_with_kwargs(base_logger):
    app, mock_logger = base_logger
    param = WEKO_ADMIN_MESSAGE.get(key:='WEKO_ADMIN_EXCLUDED_USERID')

    weko_logger(key=key, user_id="test_user")

    mock_logger.assert_called_once_with(app=app, param=param, ex=None, user_id="test_user")

# .tox/c1/bin/pytest --cov=weko_admin tests/test_logger.py::test_weko_logger_key_not_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_weko_logger_key_not_exists(base_logger):
    app, mock_logger = base_logger

    weko_logger(key=(key:='WEKO_COMMON_MESSAGE'))

    mock_logger.assert_called_once_with(app=app, key=key, ex=None)


@pytest.fixture
def base_logger(mocker):
    app = Flask(__name__)
    mock_logger = mocker.patch("weko_admin.logger.weko_logger_base")

    with app.app_context():
        yield app, mock_logger
