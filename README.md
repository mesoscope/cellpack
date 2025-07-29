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

## Pack example recipes
1. v1: `pack -r examples/recipes/v1/NM_Analysis_FigureB1.0.json -c examples/packing-configs/run.json`
2. v2:  `pack -r examples/recipes/v2/one_sphere.json -c examples/packing-configs/run.json`
3. Pack from remote server: `pack -r  github:recipes/NM_Analysis_FigureB1.0.json  -c examples/packing-configs/run.json`

**Stable Release:** `pip install cellpack`<br>
**Development Head:** `pip install git+https://github.com/mesoscope/cellpack.git`

## Documentation

For full package documentation please visit [mesoscope.github.io/cellpack](https://mesoscope.github.io/cellpack).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for information related to developing the code.

## Remote databases
cellPACK uses AWS and Firebase Firestore as remote databases to store packing results and recipes. Follow instructions [here](docs/REMOTE_DATABASES.md) to set up access.

## Docker
cellPACK can be run in Docker containers for both AWS ECS and AWS Batch. Follow the instructions [here](docs/DOCKER.md) to set up the Docker environment.

**MIT license**