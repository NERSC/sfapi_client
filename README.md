# SF API Python Client

This a first pass at a basic async and generated sync client for the SF API. It sketches out some of the basic interfaces that could be provided. We are using pydantic models and Python typing to make the JSON responses from the API more discoverable during development. Using the various asyncio constructs such as `await` and `gather` it is possible to build up job based workflow pretty easily. This is very much a prototype, there are plenty of things that would need to be done before any of it could be used in production, its a first step.

## Usage

### Accessing a compute resource

#### async

```python
    from sfapi_client import AsyncClient
    from sfapi_client import Machines

    async with AsyncClient(client_id, client_secret) as client:
        cori = await client.compute(Machines.cori)

```

#### sync

```python
    from sfapi_client import Client
    from sfapi_client import Machines

    with Client(client_id, client_secret) as client:
        cori = client.compute(Machines.cori)
```


### Submitting a job

#### async

```python
    from sfapi_client import AsyncClient
    from sfapi_client import Machines

    async with AsyncClient(client_id, client_secret) as client:
        cori = await client.compute(Machines.cori)
        job = await cori.submit_job(job_path)

        # Now wait for the job to complete
        await job.complete()
```

#### sync

```python
    from sfapi_client import Client
    from sfapi_client import Machines

    with Client(client_id, client_secret) as client:
        cori = client.compute(Machines.cori)
        job = cori.submit_job(job_path)

        # Now wait for the job to complete
        job.complete()
```

### Cancelling a job

#### async

```python
    from sfapi_client import AsyncClient
    from sfapi_client import Machines

    async with AsyncClient(client_id, client_secret) as client:
        cori = await client.compute(Machines.cori)
        job = await cori.submit_job(job_path)

        await job.cancel()
```

#### sync

```python
    from sfapi_client import Client
    from sfapi_client import Machines

    with Client(client_id, client_secret) as client:
        cori = client.compute(Machines.cori)
        job = cori.submit_job(job_path)

        job.cancel()
```

## Synchronous client generation

The client is implemented using asyncio. However, we are using [unasync](https://github.com/python-trio/unasync)
to generate a synchronous version. The synchronous client can be updated by running the following command:

```bash
python scripts/run.py unasync
```

`unasync` doesn't currently have support for `asyncio.sleep` so any use of `asyncio.sleep` should be replaced with
`commmon._ASYNC_SLEEP` so we can apply the appropriate extract rule.

## pydantic model generation

The client uses pydantic models generated from the OpenAPI specification and optionally a sample job response. These
models are generated into `_models.py`. To refresh them run the following command:

```bash
python scripts/run.py codegen --job-json job.json
```

