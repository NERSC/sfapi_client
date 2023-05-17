# QuickStart

This will be a basic guide to using the `sfapi_client`. Documentation on all the features can be found under the API Reference,
and example jupyter notebooks can be found in [Examples](../examples).

## Installation

The library is available on [PyPi](https://pypi.org/project/sfapi_client/) and installable with `pip`.

```bash
pip install sfapi_client
```

## Importing the Client

The client can be imported into your existing python codes by importing the client you want to use.

=== "async"

    ```pycon
    >>> from sfapi_client import AsyncClient
    ```
=== "sync"

    ```pycon
    >>> from sfapi_client import Client
    ```

## Getting system status

The status of the compute machines as well as other resources available at NERSC can be fetched without authentication.
Here's an example of getting the status of Perlmutter.

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>> async with AsyncClient() as client:
    ...     status = await client.compute(Machine.perlmutter)
    ...
    >>> status
    AsyncCompute(name='perlmutter', full_name='Perlmutter', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 11, 13, 50, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._async.client.AsyncClient object at 0x1070b0790>)
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>> with Client() as client:
    ...     status = client.compute(Machine.perlmutter)
    ...
    >>> status
    Compute(name='perlmutter', full_name='Perlmutter', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 11, 13, 50, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x10679afe0>)
    ```

And an example of getting the most recent outages for a resource such as Spin.

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client import Resource
    >>> async with AsyncClient() as client:
    ...     outages = await client.resources.outages(Resource.spin)
    ...
    >>> outages[0]
    Outage(name='spin', start_at=datetime.datetime(2023, 5, 5, 13, 50, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), end_at=datetime.datetime(2023, 5, 5, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), description='System Degraded', notes='The Rancher 2 development cluster was unavailable from 13:50-14:10 due to a control plane node RAM shortage combined with reaching a ceiling on total cluster pod count. Staff increased RAM and unanimously agreed to raise the pod count ceiling; workloads will be briefly unavailable (1-2 min) for rolling node reboots.', status='Completed', swo='degr', update_at=None)
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client import Resource
    >>> with Client() as client:
    ...     outages = client.resources.outages(Resource.spin)
    ...
    >>> outages[0]
    Outage(name='spin', start_at=datetime.datetime(2023, 5, 5, 13, 50, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), end_at=datetime.datetime(2023, 5, 5, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), description='System Degraded', notes='The Rancher 2 development cluster was unavailable from 13:50-14:10 due to a control plane node RAM shortage combined with reaching a ceiling on total cluster pod count. Staff increased RAM and unanimously agreed to raise the pod count ceiling; workloads will be briefly unavailable (1-2 min) for rolling node reboots.', status='Completed', swo='degr', update_at=None)
    ```


## Setting up credentials

To get more detailed information from NERSC systems like your projects allocations or the current jobs in the queue you will need to provide credentials. 
The [NERSC Documentation](https://docs.nersc.gov/services/sfapi/authentication/#client) has more information about getting the `client_id` and `client_secret` from iris.
Once you retrieve the keys there are a few ways to use them to activate the client.

### Storing as environment variables

The simplest way to get started is to export them into your environment, and then retrieve them in your python script from the `os` module.

```bash
export SFAPI_CLIENT_ID='randmstrgz'
export SFAPI_SECRET='{"kty": "RSA", "n": ...}'
```

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>> from authlib.jose import JsonWebKey
    >>> import json
    >>> import os
    >>>
    >>> client_id = os.getenv("SFAPI_CLIENT_ID")
    >>> sfapi_secret = os.getenv("SFAPI_SECRET")
    >>> client_secret = JsonWebKey.import_key(json.loads(sfapi_secret))
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>> from authlib.jose import JsonWebKey
    >>> import json
    >>> import os
    >>>
    >>> client_id = os.getenv("SFAPI_CLIENT_ID")
    >>> sfapi_secret = os.getenv("SFAPI_SECRET")
    >>> client_secret = JsonWebKey.import_key(json.loads(sfapi_secret))
    >>>
    >>> with Client(client_id, client_secret) as client:
    ...     perlmutter = client.compute(Machine.perlmutter)
    ```

### Storing keys in files

Keys can also be stored in a file. By default the client will look for files saved to the `~/.superfacility` directory in the pem format with the `client_id` in the first line.
Files should be saved as read/write only by the user with `chmod 600 ~/.superfacility/key.pem`.

```pem
randmstrgz
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

If the key is stored in a different location, possibly as a secret file storage in Spin, the `key_path` can be given explicitly to the client.

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>> from pathlib import Path
    >>>
    >>> key_path = Path("/path/to/secret/key.pem")
    >>>
    >>> async with AsyncClient(key=key_path) as client:
    ...     perlmutter = await client.compute(Machine.perlmutter)

    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>> from pathlib import Path
    >>>
    >>> key_path = Path("/path/to/secret/key.pem")
    >>>
    >>> with Client(key=key_path) as client:
    ...     perlmutter = client.compute(Machine.perlmutter)
    ```


## Submitting a job

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ...     job = await perlmutter.submit_job(job_path)
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
    ...     perlmutter = client.compute(Machine.perlmutter)
    ...     job = perlmutter.submit_job(job_path)
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
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ...     job = await perlmutter.submit_job(job_path)
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
    ...     perlmutter = client.compute(Machine.perlmutter)
    ...     job = perlmutter.submit_job(job_path)
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

## Canceling a job

=== "async"
    ```pycon
    >>> from sfapi_client import AsyncClient
    >>> from sfapi_client.compute import Machine
    >>>
    >>> async with AsyncClient(client_id, client_secret) as client:
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ...     job = await perlmutter.submit_job(job_path)
    ...
    ...     await job.cancel()
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, client_secret) as client:
    ...     perlmutter = client.compute(Machine.perlmutter)
    ...     job = perlmutter.submit_job(job_path)
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
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ...     [file] = await perlmutter.ls(path)
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
    ...     perlmutter = client.compute(Machine.perlmutter)
    ...     [file] = perlmutter.ls(path)
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
    ...     perlmutter = await client.compute(Machine.perlmutter)
    ...     [path] = await perlmutter.ls(target, directory=True)
    ...     await path.upload(file)
    ...
    AsyncRemotePath(perms=None, hardlinks=0, user=None, group=None, size=0, date=None, name='hello.txt', compute=AsyncCompute(name='perlmutter', full_name='perlmutter', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 9, 22, 5, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._async.client.AsyncClient object at 0x107f85840>))
    ```
=== "sync"
    ```pycon
    >>> from sfapi_client import Client
    >>> from sfapi_client.compute import Machine
    >>>
    >>> with Client(client_id, key) as client:
    ...     perlmutter = client.compute(Machine.perlmutter)
    ...     [path] = perlmutter.ls(target, directory=True)
    ...     path.upload(file)
    ...
    RemotePath(perms=None, hardlinks=0, user=None, group=None, size=0, date=None, name='hello.txt', compute=Compute(name='perlmutter', full_name='perlmutter', description='System is active', system_type='compute', notes=[], status=<StatusValue.active: 'active'>, updated_at=datetime.datetime(2023, 5, 9, 22, 5, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x107f84e20>))
    ```