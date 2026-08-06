import pytest

from flask import Flask

from weko_indextree_journal.logger import WEKO_INDEX_TREE_JOURNAL_MESSAGE, weko_logger


# .tox/c1/bin/pytest --cov=weko_indextree_jounaul tests/test_logger.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko-indextree-journal/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_indextree_jounaul tests/test_logger.py::test_message_resource -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko-indextree-journal/.tox/c1/tmp
def test_message_resource():
    assert all([isinstance(v, dict) for v in WEKO_INDEX_TREE_JOURNAL_MESSAGE.values()])
    assert all(set(v.keys()) == {"msgid", "msgstr", "loglevel"} for v in WEKO_INDEX_TREE_JOURNAL_MESSAGE.values())

# .tox/c1/bin/pytest --cov=weko_indextree_jounaul tests/test_logger.py::test_weko_logger_with_kwargs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko-indextree-journal/.tox/c1/tmp
def test_weko_logger_with_kwargs(base_logger):
    app, mock_logger = base_logger
    param = WEKO_INDEX_TREE_JOURNAL_MESSAGE.get(key:='WEKO_INDEX_TREE_JOURNAL_FAILED_DISPLAY_SETTINGS_JOURNAL_INFO')

    weko_logger(key=key, index_name="test",configuration_value="test")

    mock_logger.assert_called_once_with(app=app, param=param, ex=None, index_name="test",configuration_value="test")

# .tox/c1/bin/pytest --cov=weko_indextree_jounaul tests/test_logger.py::test_weko_logger_key_not_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko-indextree-journal/.tox/c1/tmp
def test_weko_logger_key_not_exists(base_logger):
    app, mock_logger = base_logger

    weko_logger(key=(key:='WEKO_COMMON_MESSAGE'))

    mock_logger.assert_called_once_with(app=app, key=key, ex=None)


@pytest.fixture
def base_logger(mocker):
    app = Flask(__name__)
    mock_logger = mocker.patch("weko_indextree_journal.logger.weko_logger_base")

    with app.app_context():
        yield app, mock_logger
