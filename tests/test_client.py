import pytest
import httpx

from sfapi_client import AsyncClient


@pytest.mark.public
@pytest.mark.asyncio
async def test_no_creds():
    async with AsyncClient() as client:
        assert client is not None


@pytest.mark.public
@pytest.mark.asyncio
async def test_no_creds_auth_required(test_machine):
    async with AsyncClient() as client:
        machine = await client.compute(test_machine)
        with pytest.raises(httpx.HTTPStatusError):
            await machine.jobs()
