import pytest

from flask import Flask

from weko_gridlayout.logger import WEKO_GRIDLAYOUT_MESSAGE, weko_logger


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_logger.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_logger.py::test_message_resource -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_message_resource():
    assert all([isinstance(v, dict) for v in WEKO_GRIDLAYOUT_MESSAGE.values()])
    assert all(set(v.keys()) == {"msgid", "msgstr", "loglevel"} for v in WEKO_GRIDLAYOUT_MESSAGE.values())


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_logger.py::test_weko_logger_key_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_weko_logger_key_exists(base_logger):
    app, mock_logger = base_logger
    param = WEKO_GRIDLAYOUT_MESSAGE.get(key:='WEKO_GRIDLAYOUT_FAILED_OUTPUT_RSS_DOCUMENT')

    weko_logger(key=key)

    mock_logger.assert_called_once_with(app=app, param=param, ex=None)

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_logger.py::test_weko_logger_with_kwargs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_weko_logger_with_kwargs(base_logger):
    app, mock_logger = base_logger
    param =WEKO_GRIDLAYOUT_MESSAGE.get(key:='WEKO_GRIDLAYOUT_FAILED_SAVE_WIDGET')

    weko_logger(key=key, id="test")

    mock_logger.assert_called_once_with(app=app, param=param, ex=None, id="test")

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_logger.py::test_weko_logger_key_not_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_weko_logger_key_not_exists(base_logger):
    app, mock_logger = base_logger

    weko_logger(key=(key:='WEKO_COMMON_MESSAGE'))

    mock_logger.assert_called_once_with(app=app, key=key, ex=None)


@pytest.fixture
def base_logger(mocker):
    app = Flask(__name__)
    mock_logger = mocker.patch("weko_gridlayout.logger.weko_logger_base")

    with app.app_context():
        yield app, mock_logger
