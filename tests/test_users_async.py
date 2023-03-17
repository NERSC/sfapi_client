import pytest

from sfapi_client import AsyncClient


@pytest.mark.asyncio
async def test_get_user(client_id, client_secret, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        user = await client.user()
        assert user is not None
        assert user.name == test_username


@pytest.mark.asyncio
async def test_get_user_groups(client_id, client_secret, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        groups = await user.groups()

        assert groups


@pytest.mark.asyncio
async def test_get_user_projects(client_id, client_secret, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        projects = await user.projects()

        assert projects
