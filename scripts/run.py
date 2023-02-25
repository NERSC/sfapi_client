import os
from pathlib import Path

import typer
import unasync
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from typing import Optional

from datamodel_code_generator import InputFileType, generate
import typer


cli = typer.Typer()


#
# Generate sync client using unasync
#
@cli.command(name="unasync")
def run_unasync():
    additional_replacements = {
        "AsyncClient": "Client",
        "AsyncOAuth2Client": "OAuth2Client",
        "aclose": "close",
        "_ASYNC_SLEEP": "_SLEEP",
    }
    rules = [
        unasync.Rule(
            fromdir="/src/sfapi_client/_async/",
            todir="/src/sfapi_client/_sync/",
            additional_replacements=additional_replacements,
        ),
    ]

    filepaths = []
    exclude = ["common.py"]

    for p in (Path(__file__).parent.parent / "src" / "sfapi_client" / "_async").glob(
        "**/*.py"
    ):
        if p.name not in exclude:
            filepaths.append(str(p))

    unasync.unasync_files(filepaths, rules)


def _from_open_api() -> str:
    with TemporaryDirectory() as tempdir:
        output = Path(tempdir) / "model.py"
        generate(
            use_double_quotes=True,
            input_=urlparse("https://api.nersc.gov/api/v1.2/openapi.json"),
            input_file_type=InputFileType.OpenAPI,
            output=output,
        )

        return output.read_text()


def _from_json(json: Path, class_name: str) -> str:
    with TemporaryDirectory() as tempdir:
        output = Path(tempdir) / "model.py"
        generate(
            use_double_quotes=True,
            force_optional_for_required_fields=True,
            input_=json,
            input_file_type=InputFileType.Json,
            output=output,
            class_name=class_name,
            aliases={
                "OutputItem": "JobStatus",
            },
        )

        return output.read_text()


#
# Generate models using datamodel-codegen using OpenAPI spec and a sample JSON job status output.
# Eventually is would be nice to move the job status model into SF API, so cold then just rely
# only on the OpenAPI spec.
#
@cli.command(name="codegen")
def datamodel_codegen(
    output: Path = typer.Option(
        Path(__file__).parent.parent / "src" / "sfapi_client" / "_async" / "_models.py",
        dir_okay=False,
        writable=True,
    ),
    json_models: Optional[Path] = typer.Option(None, dir_okay=True, writable=True),
):
    with output.open("w") as fp:
        fp.write(_from_open_api())
        models = Path(json_models).glob("*.json")
        for model in models:
            fp.write("\n")

            job_model = _from_json(model, model.stem)
            # Strip out from __future__ import annotations
            job_model = job_model.replace("from __future__ import annotations\n", "")
            fp.write(job_model)


if __name__ == "__main__":
    cli()
