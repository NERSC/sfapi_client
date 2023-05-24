from typing import List, Optional, Callable
from functools import wraps

from .._models import (
    UserInfo as UserBase,
    GroupList as GroupsResponse,
)
from .projects import AsyncProject
from ..exceptions import SfApiError


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client_id is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client.")
        return method(self, *args, **kwargs)
    return wrapper


class AsyncUser(UserBase):
    client: Optional["AsyncClient"]

    @staticmethod
    @check_auth
    async def _fetch_user(client: "AsyncClient", username: Optional[str] = None):
        url = "account/"
        if username is not None:
            url = f"{url}?username={username}"

        response = await client.get(url)
        json_response = response.json()

        user = AsyncUser.parse_obj(json_response)
        user.client = client

        return user

    async def groups(self) -> List["AsyncGroup"]:
        """
        The groups that the user is a member of.
        """
        # Avoid circular import
        from .groups import AsyncGroup

        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch groups for authenticated user.")

        r = await self.client.get("account/groups")

        json_response = r.json()
        groups_reponse = GroupsResponse.parse_obj(json_response)

        groups = [AsyncGroup.parse_obj(g) for g in groups_reponse.groups]

        def _set_client(g):
            g.client = self.client
            return g

        groups = map(_set_client, groups)

        return list(groups)

    async def projects(self) -> List[AsyncProject]:
        """
        The projects the user is associate with.
        """
        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch projects for authenticated user.")

        r = await self.client.get("account/roles")

        json_response = r.json()

        projects = [AsyncProject.parse_obj(p) for p in json_response]

        def _set_client(p):
            p.client = self.client
            return p

        projects = map(_set_client, projects)

        return list(projects)
