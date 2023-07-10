import pytest
from pathlib import Path

from sfapi_client import AsyncClient


@pytest.mark.asyncio
async def test_projects(client_id, client_secret):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user()
        projects = await user.projects()
        assert projects


@pytest.mark.asyncio
async def test_roles(client_id, client_secret):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user()
        roles = await user.roles()
        assert roles
