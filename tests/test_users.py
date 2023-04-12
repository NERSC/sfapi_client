import pytest
from sfapi_client import Client
from sfapi_client import SfApiError


def test_get_user(client_id, client_secret, test_username):
    with Client(client_id, client_secret) as client:
        user = client.user(test_username)
        assert user is not None
        assert user.name == test_username

        user = client.user()
        assert user is not None
        assert user.name == test_username


def test_get_another_user(client_id, client_secret, test_another_username):
    with Client(client_id, client_secret) as client:
        user = client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username


def test_get_user_groups(client_id, client_secret, test_username):
    with Client(client_id, client_secret) as client:
        user = client.user(test_username)
        assert user is not None
        assert user.name == test_username

        groups = user.groups()

        assert groups


def test_get_user_groups_different_user(
    client_id, client_secret, test_another_username
):
    with Client(client_id, client_secret) as client:
        user = client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username

        with pytest.raises(SfApiError):
            user.groups()


def test_get_user_projects(client_id, client_secret, test_username):
    with Client(client_id, client_secret) as client:
        user = client.user(test_username)
        assert user is not None
        assert user.name == test_username

        projects = user.projects()

        assert projects


def test_get_user_projects_different_user(
    client_id, client_secret, test_another_username
):
    with Client(client_id, client_secret) as client:
        user = client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username

        with pytest.raises(SfApiError):
            user.projects()
