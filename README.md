# cellPack

[![Build Status](https://github.com/mesoscope/cellpack/workflows/Build%20Main/badge.svg)](https://github.com/mesoscope/cellpack/actions)
[![Documentation](https://github.com/mesoscope/cellpack/workflows/Documentation/badge.svg)](https://mesoscope.github.io/cellpack/)
[![Code Coverage](https://codecov.io/gh/mesoscope/cellpack/branch/main/graph/badge.svg)](https://codecov.io/gh/mesoscope/cellpack)

algorithm to pack molecular recipes

---

## Features

-   Store values and retain the prior value in memory
-   ... some other functionality

## Quick Start

```python
from cellpack import Example

a = Example()
a.get_value()  # 10

```

in terminal:

### Setup 
1. create a virtual env: `conda create -n autopack`
2. `activate autopack`
3. `pip install -e .[dev]`

### Run analysis code
By default analyze will run all packing methods on `cellpack/test-recipes/NM_Analysis_FigureB1.0.json
Examples:
* `analyze -o [PATH/TO/OUTPUT/FOLDER]` will create subfolders for each packing method at your output folder
* To run just one packing method: `analyze -o [PATH/TO/OUTPUT/FOLDER] -p jitter`
* To change the dimension of the packing: `analyze -r cellpack/test-recipes/NM_Analysis_FigureC1.json  -o /Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_C_1 -d 3`
* Turn off plotly plot: `analyze -o [PATH/TO/OUTPUT/FOLDER] -ng` or `analyze -o [PATH/TO/OUTPUT/FOLDER] --no-grid-plot`

### Run conversion code 
* To convert to simularium and view at https://staging.simularium.allencell.org/viewer
convert -r [FULL_PATH_TO_INPUT_RECIPE_FILE] -p [FULL_PATH_TO_PACKING_RESULT] -o [OUTPUT_PATH]
## Installation

**Stable Release:** `pip install cellpack`<br>
**Development Head:** `pip install git+https://github.com/mesoscope/cellpack.git`

## Documentation

For full package documentation please visit [mesoscope.github.io/cellpack](https://mesoscope.github.io/cellpack).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for information related to developing the code.

### Contributing cheat sheet

1. `pip install -e .[dev]`

    This will install your package in editable mode with all the required development
    dependencies (i.e. `tox`).

2. `make build`

    This will run `tox` which will run all your tests in both Python 3.7
    and Python 3.8 as well as linting your code.

3. `make clean`

    This will clean up various Python and build generated files so that you can ensure
    that you are working in a clean environment.

4. `make docs`

    This will generate and launch a web browser to view the most up-to-date
    documentation for your Python package.

#### Suggested Git Branch Strategy

1. `main` is for the most up-to-date development, very rarely should you directly
   commit to this branch. GitHub Actions will run on every push and on a CRON to this
   branch but still recommended to commit to your development branches and make pull
   requests to main. If you push a tagged commit with bumpversion, this will also release to PyPI.
2. Your day-to-day work should exist on branches separate from `main`. Even if it is
   just yourself working on the repository, make a PR from your working branch to `main`
   so that you can ensure your commits don't break the development head. GitHub Actions
   will run on every push to any branch or any pull request from any branch to any other
   branch.
3. It is recommended to use "Squash and Merge" commits when committing PR's. It makes
   each set of changes to `main` atomic and as a side effect naturally encourages small
   well defined PR's.


**MIT license**

