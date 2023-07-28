from typing import List, Optional, Callable
from functools import wraps

from pydantic import ConfigDict

from .._models import (
    UserInfo as UserBase,
    GroupList as GroupsResponse,
)
from .projects import AsyncProject, AsyncRole
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


class AsyncUser(UserBase):
    client: Optional["AsyncClient"]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    @check_auth
    async def _fetch_user(client: "AsyncClient", username: Optional[str] = None):
        url = "account/"
        if username is not None:
            url = f"{url}?username={username}"

        response = await client.get(url)
        json_response = response.json()

        user = AsyncUser.model_validate(dict(json_response, client=client))

        return user

    async def groups(self) -> List["AsyncGroup"]:
        """
        The groups that the user is a member of.

        :return: the groups
        """
        # Avoid circular import
        from .groups import AsyncGroup

        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch groups for authenticated user.")

        r = await self.client.get("account/groups")

        json_response = r.json()
        groups_reponse = GroupsResponse.model_validate(json_response)

        groups = [
            AsyncGroup.model_validate(dict(g, client=self.client))
            for g in groups_reponse.groups
        ]

        return groups

    async def projects(self) -> List[AsyncProject]:
        """
        The projects the user is associate with.

        :return: the projects
        """
        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch projects for authenticated user.")

        r = await self.client.get("account/projects")

        project_values = r.json()

        projects = [
            AsyncProject.model_validate(dict(p, client=self.client))
            for p in project_values
        ]

        return projects

    async def roles(self) -> List[AsyncRole]:
        """
        The roles the user is associate with.

        :return: the roles
        """
        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch roles for authenticated user.")

        r = await self.client.get("account/roles")

        json_response = r.json()

        roles = [
            AsyncRole.model_validate(dict(p, client=self.client)) for p in json_response
        ]

        return roles
