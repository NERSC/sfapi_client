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
    >>> from sfapi_client.compute import Machine
    >>> with Client() as client:
    ...     status = client.compute(Machine.perlmutter)
    ...
    >>> status
    Compute(name='perlmutter', full_name='Perlmutter', description='System Degraded', system_type='compute', notes=['2023-04-26 18:16 -- 2023-04-28 09:30 PDT, System Degraded, Rolling reboots are complete, a final reboot is scheduled for 0930 PDT'], status=<StatusValue.degraded: 'degraded'>, updated_at=datetime.datetime(2023, 4, 26, 18, 16, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x102c871c0>)
    ```
=== "async"
    ```pycon
    >>> from sfapi_client.compute import Machine
    >>> async with AsyncClient() as client:
    ...     status = await client.compute(Machine.perlmutter)
    ...
    >>> status
    AsyncCompute(name='perlmutter', full_name='Perlmutter', description='System Degraded', system_type='compute', notes=['2023-04-26 18:16 -- 2023-04-28 09:30 PDT, System Degraded, Rolling reboots are complete, a final reboot is scheduled for 0930 PDT'], status=<StatusValue.degraded: 'degraded'>, updated_at=datetime.datetime(2023, 4, 26, 18, 16, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.AsyncClient object at 0x102c871c0>)
    ```

## Setting up credentials

## Submitting a job

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     cori = await client.compute(Machine.cori)
    ...     job = await cori.submit_job(job_path)
    ...
    ...     # Now wait for the job to complete
    ...     await job.complete()
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, client_secret) as client:
    ...     cori = client.compute(Machine.cori)
    ...     job = cori.submit_job(job_path)
    ...
    ...     # Now wait for the job to complete
    ...     job.complete()
    ```

## Monitoring a job

=== "async"
    ```pycon
    >>> import asyncio
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     cori = await client.compute(Machine.cori)
    ...     job = await cori.submit_job(job_path)
    ...
    ...     while True:
    ...         # Update the job state
    ...         await job.update()
    ...         print(job.state)
    ...         await asyncio.sleep(10)
    ...
    JobState.PENDING
    JobState.PENDING
    JobState.RUNNING
    ```
=== "sync"
    ```pycon
    >>> import time
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, client_secret) as client:
    ...     cori = client.compute(Machine.cori)
    ...     job = cori.submit_job(job_path)
    ...
    ...     while True:
    ...         # Update the job state
    ...         job.update()
    ...         print(job.state)
    ...         time.sleep(10)
    ...
    JobState.PENDING
    JobState.PENDING
    JobState.RUNNING
    ```


## Cancelling a job

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     cori = await client.compute(Machine.cori)
    ...     job = await cori.submit_job(job_path)
    ...
    ...     await job.cancel()
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, client_secret) as client:
    ...     cori = client.compute(Machine.cori)
    ...     job = cori.submit_job(job_path)
    ...
    ...     job.cancel()
    ```

## Download a file

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, key) as client:
    ...     cori = await client.compute(Machine.cori)
    ...     [file] = await cori.ls(path)
    ...     await file.download()
    ...
    <_io.StringIO object at 0x107f45120>
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, key) as client:
    ...     cori = client.compute(Machine.cori)
    ...     [file] = cori.ls(path)
    ...     file.download()
    ...
    <_io.StringIO object at 0x102aa5000>
    ```

## Upload a file

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, key) as client:
    ...     cori = await client.compute(Machine.cori)
    ...     [path] = await cori.ls(target, directory=True)
    ...     await path.upload(file)
    ...
    AsyncRemotePath(perms=None, hardlinks=0, user=None, group=None, size=0, date=None, name='hello.txt', compute=AsyncCompute(name='cori', full_name='Cori', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 9, 22, 5, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._async.client.AsyncClient object at 0x107f85840>))
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, key) as client:
    ...     cori = client.compute(Machine.cori)
    ...     [path] = cori.ls(target, directory=True)
    ...     path.upload(file)
    ...
    RemotePath(perms=None, hardlinks=0, user=None, group=None, size=0, date=None, name='hello.txt', compute=Compute(name='cori', full_name='Cori', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 9, 22, 5, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x107f84e20>))
    ```