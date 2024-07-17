import pytest

from sfapi_client import AsyncClient


@pytest.mark.asyncio
async def test_group(async_authenticated_client, test_group):
    async with async_authenticated_client as client:
        group = await client.group(test_group)
        assert group is not None
        assert group.name == test_group


@pytest.mark.api_dev
@pytest.mark.asyncio
async def test_create_group(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    async with AsyncClient(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
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


@pytest.mark.api_dev
@pytest.mark.asyncio
async def test_add_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    async with AsyncClient(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
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


@pytest.mark.api_dev
@pytest.mark.asyncio
async def test_remove_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    async with AsyncClient(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
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


@pytest.mark.api_dev
@pytest.mark.asyncio
async def test_groupmember_to_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    async with AsyncClient(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
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
