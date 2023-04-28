
from pathlib import Path
import os

replacements = {
    "tylern": "elvis",
    "/global/homes/t": "/global/homes/e",
    "/global/u1/t": "/global/homes/e",
    "nstaff": "ntrain",
    "dasrepo": "ntrain",
    "95745": "12345"
}

# Replace personal details in notebook
for notebook in Path('examples').glob('*.ipynb'):
    # Read in notebook
    with notebook.open('r') as nb:
        full_nb = nb.read()
    # replace all key with value
    for k, v in replacements.items():
        full_nb = full_nb.replace(k, v)
    # Open to write back to notebook
    with notebook.open('w') as nb:
        nb.write(full_nb)

# Get our index page
index_path = Path('docs/examples/index.md')

# Ensure the directory exists
index_path.parent.mkdir(exist_ok=True)

# Open it up and write heading
with index_path.open("w") as index:
    index.write("# Examples \n\n")

    for notebook in Path('examples').glob('*.ipynb'):
        # Hope to replace this with the python library
        os.system(f'jupyter nbconvert --to markdown {notebook} --output-dir="docs/examples"')

        notebook_name = " ".join(notebook.stem.title().split("_"))
        index.write(f"* [{notebook_name}]({notebook.stem})\n")
