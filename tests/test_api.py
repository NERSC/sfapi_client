import pytest
from sfapi_client import Client


@pytest.mark.public
def test_changelog():
    with Client() as client:
        changelog = client.api.changelog()
        assert len(changelog) > 0


@pytest.mark.public
def test_config():
    with Client() as client:
        config = client.api.config()
        assert "compute.targets" in config
