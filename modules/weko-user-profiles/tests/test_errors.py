import pytest

from weko_user_profiles.errors import (
    WekoUserProfilesError, WekoUserProfilesEditError
)

# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_errors.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_errors.py::test_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoUserProfilesError,
        WekoUserProfilesEditError,
    ]
)
def test_error(error_class):
    e = error_class()
    assert e.msg is not None

    with pytest.raises(error_class):
        raise e

# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_errors.py::test_error_with_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
@pytest.mark.parametrize(
    "error_class",
    [
        WekoUserProfilesError,
        WekoUserProfilesEditError,
    ]
)
def test_error_with_message(error_class):
    e = error_class(msg=(message := "Custom error message."))
    assert e.msg == message

    with pytest.raises(error_class):
        raise e


# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_errors.py::test_error_with_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_error_with_exception():
    original_exception = ValueError("Original exception.")
    e = WekoUserProfilesError(ex=original_exception)
    assert e.exception == original_exception

    with pytest.raises(WekoUserProfilesError):
        raise e
