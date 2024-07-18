import pytest

from sfapi_client import SfApiError


@pytest.mark.asyncio
async def test_get_user(async_authenticated_client, test_username):
    async with async_authenticated_client as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        user = await client.user()
        assert user is not None
        assert user.name == test_username


@pytest.mark.asyncio
async def test_get_another_user(async_authenticated_client, test_another_username):
    async with async_authenticated_client as client:
        user = await client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username


@pytest.mark.asyncio
async def test_get_user_groups(async_authenticated_client, test_username):
    async with async_authenticated_client as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        groups = await user.groups()

        assert groups


@pytest.mark.asyncio
async def test_get_user_groups_different_user(
    async_authenticated_client, test_another_username
):
    async with async_authenticated_client as client:
        user = await client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username

        with pytest.raises(SfApiError):
            await user.groups()


@pytest.mark.asyncio
async def test_get_user_projects(async_authenticated_client, test_username):
    async with async_authenticated_client as client:
        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        projects = await user.projects()

        assert projects


@pytest.mark.asyncio
async def test_get_user_projects_different_user(
    async_authenticated_client, test_another_username
):
    async with async_authenticated_client as client:
        user = await client.user(test_another_username)
        assert user is not None
        assert user.name == test_another_username

        with pytest.raises(SfApiError):
            await user.projects()
