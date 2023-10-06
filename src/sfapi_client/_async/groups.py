from typing import Optional, Union, List, Any, Callable
from functools import wraps
from pydantic import ValidationError, Field, BaseModel, ConfigDict
from .._models import BatchGroupAction as GroupAction, UserStats as GroupMemberBase
from ..exceptions import SfApiError
from .users import AsyncUser


def check_auth(method: Callable):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._client_id is None:
            raise SfApiError(
                f"Cannot call {self.__class__.__name__}.{method.__name__}() with an unauthenticated client."  # noqa: E501
            )
        return method(self, *args, **kwargs)

    return wrapper


class AsyncGroupMember(GroupMemberBase):
    client: Optional["AsyncClient"]  # noqa: F821

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def user(self) -> "AsyncUser":
        """
        Get the user associated with the membership.
        """
        return await AsyncUser._fetch_user(self.client, self.name)


# Note: We can't use our generated model as we want user => members ( to avoid
# confusion with User model )
class AsyncGroup(BaseModel):
    """
    A user group.
    """

    client: Optional["AsyncClient"]  # noqa: F821
    gid: Optional[int]
    name: Optional[str]
    users_: Optional[List[GroupMemberBase]] = Field(..., alias="users")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def _group_action(
        self,
        users: Union[str, "AsyncUser", List[str], List["AsyncUser"]],
        action: GroupAction,
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
            new_group = AsyncGroup.model_validate(
                dict(json_response, client=self.client)
            )
            self._update(new_group)
        except ValidationError:
            # See if we have validation error raise it
            if "details" in json_response:
                raise SfApiError(r.text)
            else:
                raise RuntimeError(r.text)

    async def add(self, users: Union[List[str], List["AsyncUser"]]):
        """
        Add users to the group.

        :param users: The usernames to add
        """
        await self._group_action(users, GroupAction.batch_add)

    async def remove(self, users: Union[List[str], List["AsyncUser"]]):
        """
        Remove users from the group.

        :param users: The usernames to remove
        """
        await self._group_action(users, GroupAction.batch_remove)

    @property
    def members(self):
        """
        The users in this group.
        """
        members = [
            AsyncGroupMember.model_validate(
                dict(user_info.model_dump(), client=self.client)
            )
            for user_info in self.users_
        ]

        def _set_client(m):
            m.client = self.client

            return m

        members = map(_set_client, members)

        return list(members)

    @staticmethod
    @check_auth
    async def _fetch_group(client: "AsyncClient", name):  # noqa: F821
        response = await client.get(f"account/groups/{name}")

        json_response = response.json()
        group = AsyncGroup.model_validate(dict(json_response, client=client))

        return group

    async def update(self):
        """
        Update the state of the group by fetching the state from the server.
        """
        group_state = await self._fetch_group(self.client, self.name)
        self._update(group_state)

    def _update(self, new_group_state: Any) -> "AsyncGroup":
        for k in new_group_state.model_fields_set:
            v = getattr(new_group_state, k)
            setattr(self, k, v)

        return self
