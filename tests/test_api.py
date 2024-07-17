import pytest


@pytest.mark.public
def test_changelog(unauthenticated_client):
    with unauthenticated_client as client:
        changelog = client.api.changelog()
        assert len(changelog) > 0


@pytest.mark.public
def test_config(unauthenticated_client):
    with unauthenticated_client as client:
        config = client.api.config()
        assert "compute.targets" in config
