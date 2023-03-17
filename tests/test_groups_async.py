import pytest
from pathlib import Path

from sfapi_client import AsyncClient


@pytest.mark.asyncio
async def test_get_group(client_id, client_secret, test_group):
    async with AsyncClient(client_id, client_secret) as client:
        group = await client.group(test_group)
        assert group is not None
        assert group.name == test_group


@pytest.mark.skip(reason="not sure how we can test this, we need a test group?")
@pytest.mark.asyncio
async def test_add_user(client_id, client_secret, test_group, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        group = await client.group(test_group)
        assert group is not None
        assert group.name == test_group

        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        await group.add(user)


@pytest.mark.skip(reason="not sure how we can test this, we need a test group?")
@pytest.mark.asyncio
async def test_remove_user(client_id, client_secret, test_group, test_username):
    async with AsyncClient(client_id, client_secret) as client:
        group = await client.group(test_group)
        assert group is not None
        assert group.name == test_group

        user = await client.user(test_username)
        assert user is not None
        assert user.name == test_username

        await group.add(user)

        await group.remove(user)
