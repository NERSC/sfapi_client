import pytest

from sfapi_client import Client


def test_projects(client_id, client_secret):
    with Client(client_id, client_secret) as client:
        user = client.user()
        projects = user.projects()
        assert projects


def test_roles(client_id, client_secret):
    with Client(client_id, client_secret) as client:
        user = client.user()
        roles = user.roles()
        assert roles
