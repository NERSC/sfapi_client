from pathlib import Path
import json

replace = Path("examples_dev") / "replacement.json"

if replace.exists():
    with replace.open("r"):
        replacements = json.loads(replace.read_text())
else:
    replacements = {}

# Replace personal details in notebook
for notebook in Path("examples_dev").glob("*.ipynb"):
    # Read in notebook
    with notebook.open("r") as nb:
        full_nb = nb.read()
    # replace all key with value
    for k, v in replacements.items():
        full_nb = full_nb.replace(k, v)

    new_path = Path("examples") / notebook.name
    # Open to write back to notebook
    with new_path.open("w") as nb:
        nb.write(full_nb)


# Get our index page
index_path = Path("docs/examples/index.md")

# Ensure the directory exists
index_path.parent.mkdir(exist_ok=True)

# Open it up and write heading
with index_path.open("w") as index:
    index.write("# Examples \n\n")

    for notebook in Path("examples").glob("*.ipynb"):
        notebook_name = " ".join(notebook.stem.title().split("_"))
        index.write(f"* [{notebook_name}]({notebook.name})\n")
