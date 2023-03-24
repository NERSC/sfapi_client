from sfapi_client import Client

DEV_API_URL = "https://api-dev.nersc.gov/api/v1.2"


def test_group(client_id, client_secret, test_group):
    with Client(client_id, client_secret, api_base_url=DEV_API_URL) as client:
        group = client.group(test_group)
        assert group is not None
        assert group.name == test_group


def test_create_group(
    client_id, client_secret, test_project, test_random_group, test_username
):
    with Client(client_id, client_secret, api_base_url=DEV_API_URL) as client:
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


def test_add_user(
    client_id, client_secret, test_project, test_random_group, test_username
):
    with Client(client_id, client_secret, api_base_url=DEV_API_URL) as client:
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


def test_remove_user(
    client_id, client_secret, test_project, test_random_group, test_username
):
    with Client(client_id, client_secret, api_base_url=DEV_API_URL) as client:
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


def test_groupmember_to_user(
    client_id, client_secret, test_project, test_random_group, test_username
):
    with Client(client_id, client_secret, api_base_url=DEV_API_URL) as client:
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
