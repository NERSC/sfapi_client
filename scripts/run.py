import os
from pathlib import Path

import typer
import unasync
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from typing import List, Optional, Any
import ast
from ast import unparse
from pathlib import Path

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
        "AsyncApi": "Api",
        "AsyncResources": "Resources",
        "AsyncCompute": "Compute",
        "AsyncGroup": "Group",
        "AsyncGroupMember": "GroupMember",
        "AsyncRemotePath": "RemotePath",
        "AsyncProject": "Project",
        "AsyncUser": "User",
        "AsyncJob": "Job",
        "AsyncJobSacct": "JobSacct",
        "AsyncJobSqueue": "JobSqueue",
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
def lookup_docstring(base_path: Path, class_name: str):
    path = Path(base_path / f"{class_name}.docstring")
    if path.exists():
        with path.open() as fp:
            return fp.read()

    return None


class DocstringInserter(ast.NodeTransformer):
    def __init__(self, base_path: Path) -> None:
        super().__init__()

        self._base_path = base_path

    def visit_ClassDef(self, node) -> Any:
        docstring = lookup_docstring(self._base_path, node.name)

        if docstring:
            new_docstring_node = make_docstring_node(docstring)
            node.body[0] = new_docstring_node

        return node


def make_docstring_node(content):
    s = ast.Str(content)
    return ast.Expr(value=s)


def add_docstrings(base_path: Path, code: str):
    tree = ast.parse(code)
    inserter = DocstringInserter(base_path)
    new_tree = inserter.visit(tree)
    ast.fix_missing_locations(new_tree)

    return unparse(new_tree)


@cli.command(name="codegen")
def openapimodel_codegen(
    output: Path = typer.Option(
        Path(__file__).parent.parent
        / "src"
        / "sfapi_client"
        / "_models"
        / "__init__.py",
        dir_okay=False,
        writable=True,
    ),
):
    with output.open("w") as fp:
        code = _from_open_api()
        code = add_docstrings(output.parent, code)
        fp.write(code)


@cli.command(name="datacodegen")
def datamodel_codegen(
    json_models: Optional[List[Path]] = typer.Option(
        None, dir_okay=True, writable=True
    ),
):
    base_dir = Path(__file__).parent.parent / "src" / "sfapi_client" / "_models"
    for model in json_models:
        model = model.resolve(strict=False)
        output = Path(f"{base_dir}/{model.stem}.py")

        with output.open("w") as fp:
            name_split = model.stem.split("_")
            name_split = [name.capitalize() for name in name_split]
            job_model = _from_json(model, f"{''.join(name_split)}")
            job_model = add_docstrings(output.parent, job_model)
            fp.write(job_model)


if __name__ == "__main__":
    cli()
