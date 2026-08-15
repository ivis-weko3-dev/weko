import pytest

from weko_schema_ui.errors import (
    WekoSchemaError, WekoSchemaSettingError, WekoSchemaConversionError, WekoOAISchemaError,
    WekoItemtypeSchemaError, WekoSchemaTreeError,
)

# .tox/c1/bin/pytest --cov=weko_admin tests/test_errors.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_admin tests/test_errors.py::test_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoSchemaError,
        WekoSchemaSettingError,
        WekoSchemaConversionError,
        WekoOAISchemaError,
        WekoItemtypeSchemaError,
        WekoSchemaTreeError,
    ]
)
def test_error(error_class):
    e = error_class()
    assert e.msg is not None

    with pytest.raises(error_class):
        raise e

# .tox/c1/bin/pytest --cov=weko_admin tests/test_errors.py::test_error_with_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoSchemaError,
        WekoSchemaSettingError,
        WekoSchemaConversionError,
        WekoOAISchemaError,
        WekoItemtypeSchemaError,
        WekoSchemaTreeError,
    ]
)
def test_error_with_message(error_class):
    e = error_class(msg=(message := "Custom error message."))
    assert e.msg == message

    with pytest.raises(error_class):
        raise e


# .tox/c1/bin/pytest --cov=weko_admin tests/test_errors.py::test_error_with_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_error_with_exception():
    original_exception = ValueError("Original exception.")
    e = WekoSchemaError(ex=original_exception)
    assert e.exception == original_exception

    with pytest.raises(WekoSchemaError):
        raise e
