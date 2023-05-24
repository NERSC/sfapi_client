## `JobState`
::: sfapi_client.jobs.JobState
    options:
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"

## `AsyncJob`
::: sfapi_client.jobs.AsyncJob
    :docstring:
    options:
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"
            - "!^__"

## `AsyncJobSacct`

Models a job running on a compute resource, the information is fetched using `sacct`.

<!-- mkdocsstring doesn't display inherited pydantic members, so we fake
by include the parent explicitly. -->
::: sfapi_client._models.job_status_response_squeue.OutputItem
    options:
        show_bases: false
        inherited_members: true
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"

::: sfapi_client.jobs.AsyncJobSacct
    options:
        show_bases: false
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"
            - "!^__"

## `AsyncJobSqueue`

Models a job running on a compute resource, the information is fetched using `squeue`.

<!-- mkdocsstring doesn't display inherited pydantic members, so we fake
by include the parent explicitly. -->
::: sfapi_client._models.job_status_response_sacct.OutputItem
    options:
        show_bases: false
        inherited_members: true
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"

::: sfapi_client.jobs.AsyncJobSqueue
    options:
        show_bases: false
        inherited_members: true
        show_if_no_docstring: yes
        filters:
            - "!^_[^_]"
            - "!^__"
