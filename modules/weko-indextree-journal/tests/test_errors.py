import pytest

from weko_indextree_journal.errors import (
    WekoJournalError,
    WekoJournalSettingError,
    WekoJournalExportError,
    WekoJournalRegistrarionError
)

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_errors.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_weko_indextree_journal tests/test_errors.py::test_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoJournalError,
        WekoJournalSettingError,
        WekoJournalExportError,
        WekoJournalRegistrarionError
    ]
)
def test_error(error_class):
    e = error_class()
    assert e.msg is not None

    with pytest.raises(error_class):
        raise e

# .tox/c1/bin/pytest --cov=weko_weko_indextree_journal tests/test_errors.py::test_error_with_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoJournalError,
        WekoJournalSettingError,
        WekoJournalExportError,
        WekoJournalRegistrarionError
    ]
)
def test_error_with_message(error_class):
    e = error_class(msg=(message := "Custom error message."))
    assert e.msg == message

    with pytest.raises(error_class):
        raise e


# .tox/c1/bin/pytest --cov=weko_weko_indextree_journal tests/test_errors.py::test_error_with_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_error_with_exception():
    original_exception = ValueError("Original exception.")
    e = WekoJournalError(ex=original_exception)
    assert e.exception == original_exception

    with pytest.raises(WekoJournalError):
        raise e
