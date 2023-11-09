# cellPack

[![Build Status](https://github.com/mesoscope/cellpack/workflows/Build%20Main/badge.svg)](https://github.com/mesoscope/cellpack/actions)
[![Documentation](https://github.com/mesoscope/cellpack/workflows/Documentation/badge.svg)](https://mesoscope.github.io/cellpack/)
[![Code Coverage](https://codecov.io/gh/mesoscope/cellpack/branch/main/graph/badge.svg)](https://codecov.io/gh/mesoscope/cellpack)

algorithm to pack molecular recipes

### Prerequisite 
1. Install Conda: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

### Setup 
1. create a virtual env: `conda create -n autopack python=3.9`
2. `conda activate autopack`
3. `pip install -e .[dev]`

### Run pack code
1. example pack v1 recipe : `pack -r examples/recipes/v1/NM_Analysis_FigureB1.0.json -c examples/packing-configs/run.json`
2. example pack v2 recipe :  `pack -r examples/recipes/v2/one_sphere.json -c examples/packing-configs/run.json`
3. example pack from remote : `pack -r  github:recipes/NM_Analysis_FigureB1.0.json  -c examples/packing-configs/run.json`

### Run conversion code 
* To convert to simularium and view at https://staging.simularium.allencell.org/viewer
`convert -r [FULL_PATH_TO_INPUT_RECIPE_FILE] -p [FULL_PATH_TO_PACKING_RESULT] -o [OUTPUT_PATH]`
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

## Introduction to Remote Databases 
### AWS S3
1. Pre-requisites
   * Obtain an AWS account for AICS. Please contact the IT team or the code owner. 
   * Generate an `aws_access_key_id` and `aws_secret_access_key` in your AWS account.

2. Step-by-step Guide
   * Download and install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   * Configure AWS CLI by running `aws configure`, then enter your credentials as prompted.
   * Ensure that Boto3, the AWS SDK for Python is installed and included in the requirements section of `setup.py`. 

### Firebase Firestore
1. Step-by-step Guide
   * Create a Firebase project in test mode with your google account, select `firebase_admin` as the SDK. [Firebase Firestore tutorial](https://firebase.google.com/docs/firestore)
   * Generate a new private key by navigating to "Project settings">"Service account" in the project's dashboard.

**MIT license**

