from typing import Optional, Union, List, Any
from pydantic import ValidationError, Field, BaseModel, validator
from .._models import BatchGroupAction as GroupAction, UserStats as GroupMemberBase
from ..common import SfApiError
from .user import User


class GroupMember(GroupMemberBase):
    client: Optional["AsyncClient"]

    async def user(self) -> "User":
        return await User._fetch_user(self.client, self.name)


# Note: We can't use our generated model as we want user => members ( to avoid confusion with User model )
class Group(BaseModel):
    client: Optional["AsyncClient"]
    gid: Optional[int]
    name: Optional[str]
    users_: Optional[List[GroupMemberBase]] = Field(..., alias="users")

    async def _group_action(
        self, users: Union[str, "User", List[str], List["User"]], action: GroupAction
    ):
        # coerse to list
        if not isinstance(users, list):
            users = [users]

        users = map(lambda u: u if not hasattr(u, "name") else u.name, users)
        params = {
            "group": self.name,
            "action": action.value,
            "usernames": ",".join(users),
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
                raise SfApiError(r.text)
            else:
                raise RuntimeError(r.text)

    async def add(self, users: Union[List[str], List["User"]]):
        await self._group_action(users, GroupAction.batch_add)

    async def remove(self, users: Union[List[str], List["User"]]):
        await self._group_action(users, GroupAction.batch_remove)

    @property
    def members(self):
        members = [GroupMember.parse_obj(user_info) for user_info in self.users_]

        def _set_client(m):
            m.client = self.client

            return m

        members = map(_set_client, members)

        return list(members)

    @staticmethod
    async def _fetch_group(client: "Client", name):
        response = await client.get(f"account/groups/{name}")
        json_response = response.json()

        group = Group.parse_obj(json_response)
        group.client = client

        return group

    async def update(self):
        """
        Update the state of the group by fetching the state from the server.
        """
        group_state = await self._fetch_group(self.client, self.name)
        self._update(group_state)

    def _update(self, new_group_state: Any) -> "Group":
        for k in new_group_state.__fields_set__:
            v = getattr(new_group_state, k)
            setattr(self, k, v)

        return self