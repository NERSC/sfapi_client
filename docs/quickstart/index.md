# QuickStart

Import the client

=== "sync"

    ```pycon
    >>> from sfapi_client import Client
    ```
=== "async"

    ```pycon
    >>> from sfapi_client import AsyncClient
    ```

Lets get the status for permutter.

=== "sync"

    ```pycon
    >>> from sfapi_client.compute import Machines
    >>> with Client() as client:
    ...     status = client.compute(Machines.perlmutter)
    ...
    >>> status
    Compute(name='perlmutter', full_name='Perlmutter', description='System Degraded', system_type='compute', notes=['2023-04-26 18:16 -- 2023-04-28 09:30 PDT, System Degraded, Rolling reboots are complete, a final reboot is scheduled for 0930 PDT'], status=<StatusValue.degraded: 'degraded'>, updated_at=datetime.datetime(2023, 4, 26, 18, 16, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x102c871c0>)
    ```
=== "async"
    ```pycon
    >>> from sfapi_client.compute import Machines
    >>> async with AsyncClient() as client:
    ...     status = await client.compute(Machines.perlmutter)
    ...
    >>> status
    AsyncCompute(name='perlmutter', full_name='Perlmutter', description='System Degraded', system_type='compute', notes=['2023-04-26 18:16 -- 2023-04-28 09:30 PDT, System Degraded, Rolling reboots are complete, a final reboot is scheduled for 0930 PDT'], status=<StatusValue.degraded: 'degraded'>, updated_at=datetime.datetime(2023, 4, 26, 18, 16, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x102c871c0>)
    ```

## Setting up credentials

## Submitting a job

## Monitoring a job

## Cancelling a job

## Download a file

## Upload a file