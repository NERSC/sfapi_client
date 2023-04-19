"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

sync_path = Path("docs/reference/sync")
sync_path.mkdir(parents=True, exist_ok=True)
async_path = Path("docs/reference/async")

for path in async_path.rglob("*.md"):
    with path.open("r") as fp:
        content = fp.read().replace("Async", "")

    module_path = sync_path / path.relative_to(async_path)
    module_path.parent.mkdir(parents=True, exist_ok=True)
    with module_path.open("w") as fp:
        fp.write(content)
