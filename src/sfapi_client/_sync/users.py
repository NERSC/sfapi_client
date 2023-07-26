from typing import List, Optional, Callable
from functools import wraps

from pydantic import ConfigDict

from .._models import (
    UserInfo as UserBase,
    GroupList as GroupsResponse,
)
from .projects import Project, Role
from ..exceptions import SfApiError


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client_id is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."
            )
        return method(self, *args, **kwargs)

    return wrapper


class User(UserBase):
    client: Optional["Client"]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    @check_auth
    def _fetch_user(client: "Client", username: Optional[str] = None):
        url = "account/"
        if username is not None:
            url = f"{url}?username={username}"

        response = client.get(url)
        json_response = response.json()

        user = User.model_validate(dict(json_response, client=client))

        return user

    def groups(self) -> List["Group"]:
        """
        The groups that the user is a member of.

        :return: the groups
        """
        # Avoid circular import
        from .groups import Group

        if self.name != (self.client._user()).name:
            raise SfApiError(f"Can only fetch groups for authenticated user.")

        r = self.client.get("account/groups")

        json_response = r.json()
        groups_reponse = GroupsResponse.model_validate(json_response)

        groups = [
            Group.model_validate(dict(g, client=self.client))
            for g in groups_reponse.groups
        ]

        return groups

    def projects(self) -> List[Project]:
        """
        The projects the user is associate with.

        :return: the projects
        """
        if self.name != (self.client._user()).name:
            raise SfApiError(f"Can only fetch projects for authenticated user.")

        r = self.client.get("account/projects")

        project_values = r.json()

        projects = [
            Project.model_validate(dict(p, client=self.client))
            for p in project_values
        ]

        return projects

    def roles(self) -> List[Role]:
        """
        The roles the user is associate with.

        :return: the roles
        """
        if self.name != (self.client._user()).name:
            raise SfApiError(f"Can only fetch roles for authenticated user.")

        r = self.client.get("account/roles")

        json_response = r.json()

        roles = [
            Role.model_validate(dict(p, client=self.client)) for p in json_response
        ]

        return roles
