import pytest
from pathlib import Path

from sfapi_client import AsyncClient


@pytest.mark.skip(
    reason="not sure how we can test this, there doesn't seem to be a way to remove groups?"
)
@pytest.mark.asyncio
async def test_create_group(
    client_id, client_secret, test_username, test_project, test_group_create
):
    async with AsyncClient(client_id, client_secret) as client:
        user = await client.user(test_username)
        projects = await user.projects()

        project = None
        for p in projects:
            if p.repo_name == test_project:
                project = p
                break

        assert project

        group = await project.create_group(test_group_create)

        assert group.name == test_create_group
