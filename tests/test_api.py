from sfapi_client import Client


def test_changelog():
    with Client() as client:
        changelog = client.api.changelog()
        assert len(changelog) > 0


def test_config():
    with Client() as client:
        config = client.api.config()
        assert "compute.targets" in config
