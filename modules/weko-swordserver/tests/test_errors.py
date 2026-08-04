from weko_swordserver.errors import WekoSwordserverException, ErrorType

# .tox/c1/bin/pytest --cov=modules/weko-swordserver/weko_swordserver tests/test_errors.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=modules/weko-swordserver/weko_swordserver tests/test_errors.py::test_weko_swordserver_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_weko_swordserver_exception():
    message = "Test error message"
    exception = WekoSwordserverException(message, ErrorType.BadRequest, ValueError("Test exception"))
    assert str(exception) == message
    assert exception.errorType == ErrorType.BadRequest

# .tox/c1/bin/pytest --cov=modules/weko-swordserver/weko_swordserver tests/test_errors.py::test_weko_swordserver_exception_no_params -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_weko_swordserver_exception_no_params():
    exception = WekoSwordserverException()
    assert str(exception) == "Some error has occurred in weko_swordserver."
