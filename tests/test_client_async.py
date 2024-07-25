import pytest

from sfapi_client import SfApiError, AsyncClient


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


@pytest.mark.asyncio
async def test_access_token(api_base_url, access_token, test_machine, test_username):
    async with AsyncClient(
        api_base_url=api_base_url, access_token=access_token
    ) as client:
        machine = await client.compute(test_machine)
        await machine.jobs(user=test_username)
