import pytest
from sfapi_client import Client


@pytest.mark.api_dev
def test_group(
    dev_client_id, dev_client_secret, test_group, dev_api_url, dev_token_url
):
    with Client(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        group = client.group(test_group)
        assert group is not None
        assert group.name == test_group


@pytest.mark.api_dev
def test_create_group(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    with Client(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        user = client.user(test_username)
        projects = user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group


@pytest.mark.api_dev
def test_add_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    with Client(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        user = client.user(test_username)
        projects = user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = client.user(test_username)

        assert user is not None
        assert user.name == test_username

        group.add(user)

        assert group.members

        is_member = (
            len(list(filter(lambda m: m.name == test_username, group.members))) == 1
        )
        assert is_member


@pytest.mark.api_dev
def test_remove_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    with Client(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        user = client.user(test_username)
        projects = user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = client.user(test_username)

        assert user is not None
        assert user.name == test_username

        group.add(user)

        assert group.members

        is_member = (
            len(list(filter(lambda m: m.name == test_username, group.members))) == 1
        )
        assert is_member

        # Now remove the user
        group.remove(user)

        assert group.members == []


@pytest.mark.api_dev
def test_groupmember_to_user(
    dev_client_id,
    dev_client_secret,
    test_project,
    test_random_group,
    test_username,
    dev_api_url,
    dev_token_url,
):
    with Client(
        client_id=dev_client_id,
        secret=dev_client_secret,
        api_base_url=dev_api_url,
        token_url=dev_token_url,
    ) as client:
        user = client.user(test_username)
        projects = user.projects()

        # Find the test project
        project = None
        for p in projects:
            if p.name == test_project:
                project = p
                break

        assert project

        # Create a test group
        group = project.create_group(test_random_group)

        assert group is not None
        assert group.name == test_random_group

        user = client.user(test_username)

        assert user is not None
        assert user.name == test_username

        group.add(user)

        assert group.members

        from_member = group.members[0].user()

        assert from_member == user
