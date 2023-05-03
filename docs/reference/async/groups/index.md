## `AsyncGroup`

::: sfapi_client.groups.AsyncGroup
    options:
        show_if_no_docstring: yes
        filters:
            - "!client"
            - "!^_[^_]"
            - "!^users_"

## `AsyncGroupMember`

A group member.

<!-- mkdocsstring doesn't display inherited pydantic members, so we fake
by include the parent explicitly. -->
::: sfapi_client._models.UserStats
    options:
        show_bases: false
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"

::: sfapi_client.groups.AsyncGroupMember
    options:
        show_bases: false
        show_if_no_docstring: yes
        filters:
            - "!client"
            - "!^_[^_]"
            - "!^users_"
