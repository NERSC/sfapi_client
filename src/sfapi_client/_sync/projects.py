from typing import Optional
from pydantic import ValidationError, Field, ConfigDict

from .._models import ProjectStats as ProjectBase, RoleStats as RoleBase
from ..exceptions import SfApiError


class Role(RoleBase):
    client: Optional["Client"]

    model_config = ConfigDict(arbitrary_types_allowed=True)

class Project(ProjectBase):
    client: Optional["Client"]
    name: str = Field(alias="repo_name")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def create_group(self, name: str) -> "Group":
        """
        Create a new project.
        :param name: The project name
        """
        from .groups import Group

        params = {"name": name, "repo_name": self.repo_name}

        r = self.client.post("account/groups", data=params)
        values = r.json()
        values["client"] = self.client
        try:
            group = Group.model_validate(values)
        except ValidationError:
            # See if we have validation error raise it
            if "details" in values:
                raise SfApiError(r.text())
            else:
                raise RuntimeError(r.text())

        group.client = self.client

        return group
