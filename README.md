# cellPACK

[![Continuous Integration](https://github.com/mesoscope/cellpack/actions/workflows/ci.yml/badge.svg)](https://github.com/mesoscope/cellpack/actions/workflows/ci.yml)
[![Documentation](https://github.com/mesoscope/cellpack/workflows/Documentation/badge.svg)](https://mesoscope.github.io/cellpack/)
[![Code Coverage](https://codecov.io/gh/mesoscope/cellpack/branch/main/graph/badge.svg)](https://codecov.io/gh/mesoscope/cellpack)

An algorithm to pack molecular recipes

## Installation

> [!NOTE]
> These are the basic installation steps. However, our recommendation for developers is to install with `pyenv` and `pdm`. See advanced installation instructions [here](docs/INSTALL.md).

1. Install Python 3.9 and `git`.  Update pip at least to `24.0.0`.
2. Clone this git repository.
```bash
git clone git@github.com:mesoscope/cellpack.git
cd cellpack
```
3. Create a new virtual environment and activate it.
```bash
python -m venv .venv
source .venv/bin/activate
```
4. Install the required packages for your operating system. Replace `linux` with `macos` or `windows` as appropriate.
```bash
pip install --upgrade pip
pip install -r requirements/linux/requirements.txt
pip install -e .
```

## Run pack code
1. example pack v1 recipe : `pack -r examples/recipes/v1/NM_Analysis_FigureB1.0.json -c examples/packing-configs/run.json`
2. example pack v2 recipe :  `pack -r examples/recipes/v2/one_sphere.json -c examples/packing-configs/run.json`
3. example pack from remote : `pack -r  github:recipes/NM_Analysis_FigureB1.0.json  -c examples/packing-configs/run.json`

## Run conversion code 
* To convert to simularium and view at https://staging.simularium.allencell.org/viewer
`convert -r [FULL_PATH_TO_INPUT_RECIPE_FILE] -p [FULL_PATH_TO_PACKING_RESULT] -o [OUTPUT_PATH]`

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

    This will run `tox` which will run all your tests and lint your code.

3. `make clean`

    This will clean up various Python and build generated files so that you can ensure
    that you are working in a clean environment.

4. `make docs`

    This will generate and launch a web browser to view the most up-to-date
    documentation for your Python package.

### Suggested Git Branch Strategy

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
   * For dev database:
     * Create a Firebase project in test mode with your google account, select `firebase_admin` as the SDK. [Firebase Firestore tutorial](https://firebase.google.com/docs/firestore)
     * Generate a new private key by navigating to "Project settings">"Service account" in the project's dashboard.
   * For staging database:
       * Obtain credentials:
          * Reach out to the code owner for the necessary credentials.
       * Configure the environment variables:
          * Create a `.env` file in the root directory.
          * Populate the `.env` file with the following variables:
           ```
               FIREBASE_TOKEN=KEY_JSON_FILE["private_key"]
               FIREBASE_EMAIL=KEY_JSON_FILE["client_email"]
           ```
          note: `KEY_JSON_FILE` is the content of the private key JSON file generated in the staging Firebase.

### Docker

* Install [docker](https://docs.docker.com/v17.09/engine/installation/)
* Clone the repository locally, if you haven't already: `git clone https://github.com/mesoscope/cellpack.git`
* Ensure that you have valid AWS access key and secret to access the `cellpack-results` S3 bucket, usually stored in a `~/.aws/credentials` file.
*  We have two Dockerfiles in /docker, one that builds the Docker image to be run in AWS ECS, and one to be run in AWS Batch. To build one of the images, run: `docker build -f [DOCKERFILE-NAME] -t [CONTAINER-NAME] .` Rebuild the container if new files are added or changes are made to the codebase.

#### Batch Docker Image
1. Build image, running `docker build -f docker/Dockerfile.batch -t [CONTAINER-NAME] .`
2. Run packings in the container, running: `docker run -v ~/.aws:/root/.aws -e recipe=examples/recipes/v2/one_sphere.json -e config=examples/packing-configs/run.json [CONTAINER-NAME]`
3. Verify that the packing results are saved in the `cellpack-results` S3 bucket. You should see a botocore logging message indicating that the credentials were successfully loaded.

#### ECS Docker Image
1. Build image, running `docker build -f docker/Dockerfile.ecs -t [CONTAINER-NAME] .`
2. Run packings in the container, running: `docker run -v ~/.aws:/root/.aws -p 8443:8443 [CONTAINER-NAME]`
3. Try hitting the test endpoint on the server, by navigating to `http://0.0.0.0:8443/hello` in your browser.
4. Try running a packing on the server, by hitting the `http://0.0.0.0:8443/pack?recipe=firebase:recipes/one_sphere_v_1.0.0` in your browser.
5. Verify that the packing result path was uploaded to the firebase results table, with the job id specified in the response from the request in step 4.The result simularium file can be found at the s3 path specified there.

**MIT license**

