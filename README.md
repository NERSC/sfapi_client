# SF API Python Client

This a first pass at a basic async client for the SF API. It sketches out some of the basic interfaces that could be provided. We are using pydantic models and Python typing to make the JSON responses from the API more discoverable during development. Using the various asyncio constructs such as `await` and `gather` it is possible to build up job based workflow pretty easily. This is very much a prototype, there are plenty of things that would need to be done before any of it could be used in production, its a first step. 

## Usage

### Accessing a compute resource

```python
    from sfapi_client import Client
    from sfapi_client import Machines
    
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)

```

### Submitting a job


```python
    from sfapi_client import Client
    from sfapi_client import Machines
    
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)
        job = await cori.submit_job(job_path)
        
        # Now wait for the job to complete
        await job.complete()
```

### Cancelling a job


```python
    from sfapi_client import Client
    from sfapi_client import Machines
    
    async with Client(client_id, client_secret) as client:
        cori = await client.compute(Machines.CORI)
        job = await cori.submit_job(job_path)

        await job.cancel()
```
