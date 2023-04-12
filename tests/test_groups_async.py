import pytest

from sfapi_client import AsyncClient


@pytest.mark.asyncio
async def test_group(client_id, client_secret, test_group, dev_api_url):
    async with AsyncClient(
        client_id, client_secret, api_base_url=dev_api_url
    ) as client:
        group = await client.group(test_group)
        assert group is not None
        assert group.name == test_group


@pytest.mark.asyncio
async def test_create_group(
    client_id,
    client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
):
    async with AsyncClient(
        client_id, client_secret, api_base_url=dev_api_url
    ) as client:
        user = await client.user(test_username)
        projects = await user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = await project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group


@pytest.mark.asyncio
async def test_add_user(
    client_id,
    client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
):
    async with AsyncClient(
        client_id, client_secret, api_base_url=dev_api_url
    ) as client:
        user = await client.user(test_username)
        projects = await user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = await project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = await client.user(test_username)

        assert user is not None
        assert user.name == test_username

        await group.add(user)

        assert group.members

        is_member = (
            len(list(filter(lambda m: m.name == test_username, group.members))) == 1
        )
        assert is_member


@pytest.mark.asyncio
async def test_remove_user(
    client_id,
    client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
):
    async with AsyncClient(
        client_id, client_secret, api_base_url=dev_api_url
    ) as client:
        user = await client.user(test_username)
        projects = await user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = await project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = await client.user(test_username)

        assert user is not None
        assert user.name == test_username

        await group.add(user)

        assert group.members

        is_member = (
            len(list(filter(lambda m: m.name == test_username, group.members))) == 1
        )
        assert is_member

        # Now remove the user
        await group.remove(user)

        assert group.members == []


@pytest.mark.asyncio
async def test_groupmember_to_user(
    client_id,
    client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
):
    async with AsyncClient(
        client_id, client_secret, api_base_url=dev_api_url
    ) as client:
        user = await client.user(test_username)
        projects = await user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = await project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = await client.user(test_username)

        assert user is not None
        assert user.name == test_username

        await group.add(user)

        assert group.members

        from_member = await group.members[0].user()

        assert from_member == user
