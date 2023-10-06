from typing import Optional
from pydantic import ValidationError, Field, ConfigDict

from .._models import ProjectStats as ProjectBase, RoleStats as RoleBase
from ..exceptions import SfApiError


class AsyncRole(RoleBase):
    client: Optional["AsyncClient"]  # noqa: F821

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AsyncProject(ProjectBase):
    client: Optional["AsyncClient"]  # noqa: F821
    name: str = Field(alias="repo_name")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def create_group(self, name: str) -> "AsyncGroup":  # noqa: F821
        """
        Create a new project.
        :param name: The project name
        """
        from .groups import AsyncGroup

        params = {"name": name, "repo_name": self.repo_name}

        r = await self.client.post("account/groups", data=params)
        json_response = r.json()
        try:
            group = AsyncGroup.model_validate(dict(json_response, client=self.client))
        except ValidationError:
            # See if we have validation error raise it
            if "details" in json_response:
                raise SfApiError(r.text())
            else:
                raise RuntimeError(r.text())

        group.client = self.client

        return group
