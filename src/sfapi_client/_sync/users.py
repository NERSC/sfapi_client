from typing import List, Optional, Callable
from functools import wraps

from .._models import (
    UserInfo as UserBase,
    GroupList as GroupsResponse,
)
from .projects import Project
from ..exceptions import SfApiError


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client_id is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client.")
        return method(self, *args, **kwargs)
    return wrapper


class User(UserBase):
    client: Optional["Client"]

    @staticmethod
    @check_auth
    def _fetch_user(client: "Client", username: Optional[str] = None):
        url = "account/"
        if username is not None:
            url = f"{url}?username={username}"

        response = client.get(url)
        json_response = response.json()

        user = User.parse_obj(json_response)
        user.client = client

        return user

    def groups(self) -> List["Group"]:
        """
        The groups that the user is a member of.
        """
        # Avoid circular import
        from .groups import Group

        if self.name != (self.client._user()).name:
            raise SfApiError(f"Can only fetch groups for authenticated user.")

        r = self.client.get("account/groups")

        json_response = r.json()
        groups_reponse = GroupsResponse.parse_obj(json_response)

        groups = [Group.parse_obj(g) for g in groups_reponse.groups]

        def _set_client(g):
            g.client = self.client
            return g

        groups = map(_set_client, groups)

        return list(groups)

    def projects(self) -> List[Project]:
        """
        The projects the user is associate with.
        """
        if self.name != (self.client._user()).name:
            raise SfApiError(f"Can only fetch projects for authenticated user.")

        r = self.client.get("account/roles")

        json_response = r.json()

        projects = [Project.parse_obj(p) for p in json_response]

        def _set_client(p):
            p.client = self.client
            return p

        projects = map(_set_client, projects)

        return list(projects)
