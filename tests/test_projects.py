import pytest

from sfapi_client import Client


@pytest.mark.skip(
    reason="not sure how we can test this, there doesn't seem to be a way to remove groups?"
)
async def test_create_group(
    client_id, client_secret, test_username, test_project, test_group_create
):
    with Client(client_id, client_secret) as client:
        user = client.user(test_username)
        projects = user.projects()

        project = None
        for p in projects:
            if p.repo_name == test_project:
                project = p
                break

        assert project

        group = project.create_group(test_group_create)

        assert group.name == test_create_group
