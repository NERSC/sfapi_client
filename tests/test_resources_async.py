import pytest

from sfapi_client import StatusValue


@pytest.mark.public
@pytest.mark.asyncio
async def test_outages_by_resource(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        outages = await client.resources.outages(test_machine)

        assert len(outages) > 0
        assert outages[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_planned_outages_by_resource(
    async_unauthenticated_client, token_url, test_machine
):
    async with async_unauthenticated_client as client:
        outages = await client.resources.planned_outages(test_machine)

        if len(outages) > 0:
            assert outages[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_notes_by_resource(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        notes = await client.resources.notes(test_machine)

        assert len(notes) > 0
        assert notes[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_status_by_resource(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        status = await client.resources.status(test_machine)

        assert status.name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_outages(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        outages = await client.resources.outages()

        assert test_machine.value in outages
        test_machine_outages = outages[test_machine.value]
        assert len(test_machine_outages) > 0
        assert test_machine_outages[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_planned_outages(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        outages = await client.resources.planned_outages()

        if test_machine.value in outages:
            test_machine_outages = outages[test_machine.value]
            assert len(test_machine_outages) > 0
            assert test_machine_outages[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_notes(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        notes = await client.resources.notes()

        assert test_machine.value in notes
        test_machine_notes = notes[test_machine.value]
        assert len(test_machine_notes) > 0
        assert test_machine_notes[0].name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_status(async_unauthenticated_client, test_machine):
    async with async_unauthenticated_client as client:
        status = await client.resources.status()

        assert test_machine.value in status
        test_machine_status = status[test_machine.value]
        assert test_machine_status.name == test_machine


@pytest.mark.public
@pytest.mark.asyncio
async def test_resouce_status(async_unauthenticated_client, test_resource):
    async with async_unauthenticated_client as client:
        status = await client.resources.status(test_resource)

        assert test_resource.value in status.name
        assert status.status in StatusValue
