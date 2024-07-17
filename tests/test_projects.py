def test_projects(authenticated_client):
    with authenticated_client as client:
        user = client.user()
        projects = user.projects()
        assert projects


def test_roles(authenticated_client):
    with authenticated_client as client:
        user = client.user()
        roles = user.roles()
        assert roles
