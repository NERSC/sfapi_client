from typing import List, Optional
from .._models import (
    UserInfo as UserBase,
    ProjectStats as Project,
    GroupList as GroupsResponse,
)
from .group import Group
from .project import Project
from .common import SfApiError


class User(UserBase):
    client: Optional["Client"]

    async def groups(self) -> List[Group]:
        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch groups for authenticated user.")

        r = await self.client.get("account/groups")

        json_response = r.json()
        groups_reponse = GroupsResponse.parse_obj(json_response)

        groups = [Group.parse_obj(g) for g in groups_reponse.groups]

        def _set_client(g):
            g.client = self.client
            return g

        groups = map(_set_client, groups)

        return list(groups)

    async def projects(self) -> List[Project]:
        if self.name != (await self.client._user()).name:
            raise SfApiError(f"Can only fetch projects for authenticated user.")

        r = await self.client.get("account/roles")

        json_response = r.json()

        projects = [Project.parse_obj(p) for p in json_response]

        def _set_client(p):
            p.client = self.client
            return p

        projects = map(_set_client, projects)

        return list(projects)
