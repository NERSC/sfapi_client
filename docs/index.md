# Welcome to sfapi_client

sfapi_client is a Python 3 client for NERSC's [Superfacility API](https://docs.nersc.gov/services/sfapi/).

---

Install sfapi_client using pip:

```shell
$ pip install sfapi_client
```

Let's get started by checking the status of perlmutter:

```pycon
>>> from sfapi_client import Client
>>> from sfapi_client.compute import Machine
>>> with Client() as client:
...     status = client.compute(Machine.perlmutter)
...
>>> status
Compute(name='perlmutter', full_name='Perlmutter', description='System Degraded', system_type='compute', notes=['2023-04-26 18:16 -- 2023-04-28 09:30 PDT, System Degraded, Rolling reboots are complete, a final reboot is scheduled for 0930 PDT'], status=<StatusValue.degraded: 'degraded'>, updated_at=datetime.datetime(2023, 4, 26, 18, 16, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))), client=<sfapi_client._sync.client.Client object at 0x102c871c0>)
```

## Features

* `async` interface and standard synchronous interface.
* Fully type annotated.

## Documentation

For the basics, head over to the [QuickStart](quickstart). We also have Jupyter Notebook [examples](examples).

More in depth developer documentation can be found in the [API reference](reference).

## Dependencies

The sfapi_client project relies on these libraries:

* `httpx` - HTTP support.
* `authlib` - OAuth 2.0 authentication.
* `pydantic` - Data models.
* `tenacity` - Retry.
* `datamodel-code-generator` - Generating data models from the Open API specification.
* `unasync` - Generating synchronous interface from the async implementation.


## Installation

Install with pip:

```shell
$ pip install sfapi_client
```
