import pytest


@pytest.mark.public
@pytest.mark.asyncio
async def test_changelog(async_unauthenticated_client):
    async with async_unauthenticated_client as client:
        changelog = await client.api.changelog()
        assert len(changelog) > 0


@pytest.mark.public
@pytest.mark.asyncio
async def test_config(async_unauthenticated_client):
    async with async_unauthenticated_client as client:
        config = await client.api.config()
        assert "compute.targets" in config
