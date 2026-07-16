# .tox/c1/bin/pytest --cov=invenio_communities tests/test_permissions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
from datetime import datetime, timedelta
from invenio_communities.permissions import can_user_create_community

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_permissions.py::test_can_user_create_community_not_confirmed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_can_user_create_community_not_confirmed(app, mocker):
    app.config['COMMUNITIES_USER_CONFIRMED_SINCE'] = timedelta(days=7)

    with app.app_context():
        mock_user = mocker.MagicMock()
        mock_user.confirmed_at = None
        result, message = can_user_create_community(
            mock_user
        )

        assert result is False
        assert message == 'You have not yet confirmed your account.'

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_permissions.py::test_can_user_create_community_not_old_enough -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_can_user_create_community_not_old_enough(app, mocker):
    app.config['COMMUNITIES_USER_CONFIRMED_SINCE'] = timedelta(days=7)

    with app.app_context():
        mock_user = mocker.MagicMock()
        mock_user.confirmed_at = datetime.now() - timedelta(days=3)

        result, message = can_user_create_community(mock_user)

        assert result is False
        assert 'must be verified' in message

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_permissions.py::test_can_user_create_community_allowed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_can_user_create_community_allowed(app, mocker):
    app.config['COMMUNITIES_USER_CONFIRMED_SINCE'] = timedelta(days=7)

    with app.app_context():
        mock_user = mocker.MagicMock()
        mock_user.confirmed_at = datetime.now() - timedelta(days=10)

        result, message = can_user_create_community(mock_user)

        assert result is True
        assert message == ''