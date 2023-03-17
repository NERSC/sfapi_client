from sfapi_client import Client


def test_get_group(client_id, client_secret, test_group):
    with Client(client_id, client_secret) as client:
        group = client.group(test_group)
        assert group is not None
        assert group.name == test_group
