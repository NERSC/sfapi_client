from typing import Optional
from pydantic import ValidationError, Field

from .._models import (
    ProjectStats as ProjectBase,
)
from ..exceptions import SfApiError


class AsyncProject(ProjectBase):
    client: Optional["AsyncClient"]
    name: str = Field(alias="repo_name")

    async def create_group(self, name: str) -> "AsyncGroup":
        """
        Create a new project.
        :param name: The project name
        """
        from .groups import AsyncGroup

        params = {"name": name, "repo_name": self.repo_name}

        r = await self.client.post("account/groups", data=params)
        json_response = r.json()
        try:
            group = AsyncGroup.parse_obj(json_response)
        except ValidationError:
            # See if we have validation error raise it
            if "details" in json_response:
                raise SfApiError(r.text())
            else:
                raise RuntimeError(r.text())

        group.client = self.client

        return group
