import pytest

from sfapi_client import AsyncClient


@pytest.mark.public
@pytest.mark.asyncio
async def test_changelog():
    async with AsyncClient() as client:
        changelog = await client.api.changelog()
        assert len(changelog) > 0


@pytest.mark.public
@pytest.mark.asyncio
async def test_config():
    async with AsyncClient() as client:
        config = await client.api.config()
        assert "compute.targets" in config
