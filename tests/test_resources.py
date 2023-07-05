import pytest
from sfapi_client import Client, StatusValue


@pytest.mark.public
def test_outages_by_resource(test_machine):
    with Client() as client:
        outages = client.resources.outages(test_machine)

        assert len(outages) > 0
        assert outages[0].name == test_machine


@pytest.mark.public
def test_planned_outages_by_resource(test_machine):
    with Client() as client:
        outages = client.resources.planned_outages(test_machine)

        if len(outages) > 0:
            assert outages[0].name == test_machine


@pytest.mark.public
def test_notes_by_resource(test_machine):
    with Client() as client:
        notes = client.resources.notes(test_machine)

        assert len(notes) > 0
        assert notes[0].name == test_machine


@pytest.mark.public
def test_status_by_resource(test_machine):
    with Client() as client:
        status = client.resources.status(test_machine)

        assert status.name == test_machine


@pytest.mark.public
def test_outages(test_machine):
    with Client() as client:
        outages = client.resources.outages()

        assert test_machine.value in outages
        test_machine_outages = outages[test_machine.value]
        assert len(test_machine_outages) > 0
        assert test_machine_outages[0].name == test_machine


@pytest.mark.public
def test_planned_outages(test_machine):
    with Client() as client:
        outages = client.resources.planned_outages()

        if test_machine.value in outages:
            test_machine_outages = outages[test_machine.value]
            assert len(test_machine_outages) > 0
            assert test_machine_outages[0].name == test_machine


@pytest.mark.public
def test_notes(test_machine):
    with Client() as client:
        notes = client.resources.notes()

        assert test_machine.value in notes
        test_machine_notes = notes[test_machine.value]
        assert len(test_machine_notes) > 0
        assert test_machine_notes[0].name == test_machine


@pytest.mark.public
def test_status(test_machine):
    with Client() as client:
        status = client.resources.status()

        assert test_machine.value in status
        test_machine_status = status[test_machine.value]
        assert test_machine_status.name == test_machine


@pytest.mark.public
def test_resouce_status(test_resource):
    with Client() as client:
        status = client.resources.status(test_resource)

        assert test_resource.value in status.name
        assert status.status in StatusValue
