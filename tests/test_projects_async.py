import pytest


@pytest.mark.asyncio
async def test_projects(async_authenticated_client):
    async with async_authenticated_client as client:
        user = await client.user()
        projects = await user.projects()
        assert projects


@pytest.mark.asyncio
async def test_roles(async_authenticated_client):
    async with async_authenticated_client as client:
        user = await client.user()
        roles = await user.roles()
        assert roles
