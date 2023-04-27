
from pathlib import Path
import os

for notebook in Path('examples').glob('*.ipynb'):
    # Hope to replace this with the python library
    os.system(f'jupyter nbconvert --to markdown {notebook} --output-dir="docs/examples"')
