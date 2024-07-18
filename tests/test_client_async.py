import pytest

from sfapi_client import SfApiError


@pytest.mark.public
@pytest.mark.asyncio
async def test_no_creds(async_unauthenticated_client):
    async with async_unauthenticated_client as client:
        assert client is not None


@pytest.mark.public
@pytest.mark.asyncio
async def test_no_creds_auth_required(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        machine = await client.compute(test_machine)
        with pytest.raises(SfApiError):
            await machine.jobs()
