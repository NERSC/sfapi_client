from typing import Optional
from pydantic import ValidationError, Field

from .._models import (
    ProjectStats as ProjectBase,
)
from ..exceptions import SfApiError


class Project(ProjectBase):
    client: Optional["Client"]
    name: str = Field(alias="repo_name")

    def create_group(self, name: str) -> "Group":
        """
        Create a new project.
        :param name: The project name
        """
        from .groups import Group

        params = {"name": name, "repo_name": self.repo_name}

        r = self.client.post("account/groups", data=params)
        json_response = r.json()
        try:
            group = Group.parse_obj(json_response)
        except ValidationError:
            # See if we have validation error raise it
            if "details" in json_response:
                raise SfApiError(r.text())
            else:
                raise RuntimeError(r.text())

        group.client = self.client

        return group
