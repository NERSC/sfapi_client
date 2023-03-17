from typing import Optional, Union, List
from pydantic import ValidationError
from .._models import GroupStats as GroupBase, BatchGroupAction as GroupAction
from ..common import SfApiError


class Group(GroupBase):
    client: Optional["AsyncClient"]

    async def _group_action(
        self, users: Union[List[str], List["User"]], action: GroupAction
    ):
        users = map(lambda u: u if not hasattr(u.name) else u.name)
        params = {
            "group": self.name,
            "action": GroupAction.batch_add,
            "users": ",".join(users),
        }

        r = await self.client.put(f"account/groups/{self.name}", data=params)
        json_response = r.json()

        # if successful will return group object
        try:
            new_group = Group.parse_obj(json_response)
            self._update(new_group)
        except ValidationError:
            # See if we have validation error raise it
            if "details" in json_response:
                raise SfApiError(r.text())
            else:
                raise RuntimeError(r.text())

    async def add(self, users: Union[List[str], List["User"]]):
        self._group_action(users, GroupAction.batch_add)

    async def remove(self, users: Union[List[str], List["User"]]):
        self._group_action(users, GroupAction.batch_remove)
