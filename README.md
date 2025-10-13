# cellPACK

[![Continuous Integration](https://github.com/mesoscope/cellpack/actions/workflows/ci.yml/badge.svg)](https://github.com/mesoscope/cellpack/actions/workflows/ci.yml)
[![Documentation](https://github.com/mesoscope/cellpack/workflows/Documentation/badge.svg)](https://mesoscope.github.io/cellpack/)
[![Code Coverage](https://codecov.io/gh/mesoscope/cellpack/branch/main/graph/badge.svg)](https://codecov.io/gh/mesoscope/cellpack)

An algorithm to pack molecular recipes

**Try cellPACK online:** [cellpack.allencell.org](https://cellpack.allencell.org)

## Installation

> [!NOTE]
> These are the basic installation steps. However, our recommendation for developers is to install using `uv`. See advanced installation instructions [here](./docs/INSTALLATION.md).

1. Install Python 3.11 and `git`.  Update pip at least to `24.0.0`.
2. Clone this git repository.
```bash
git clone git@github.com:mesoscope/cellpack.git
cd cellpack
```
1. Create a new virtual environment and activate it.
```bash
python -m venv .venv
source .venv/bin/activate
```
1. Install the required packages for your operating system. Replace `linux` with `macos` or `windows` as appropriate.
```bash
pip install --upgrade pip
pip install -r requirements/linux/requirements.txt
pip install -e .
```

## Pack example recipes
1. v1: `pack -r examples/recipes/v1/NM_Analysis_FigureB1.0.json`
2. v2:  `pack -r examples/recipes/v2/one_sphere.json`
3. Pack from remote server: `pack -r  github:recipes/NM_Analysis_FigureB1.0.json`

### Config Files
Config files control the packing behavior and simulation parameters such as place methods, output formats, grid settings, and debugging options. If you need different config settings than the default, you can use the provided example config files in `examples/packing-configs/` or customize your own config options. Use `-c` flag to specify a config file: `pack -r recipe.json -c config.json`

**Stable Release:** `pip install cellpack`<br>
**Development Head:** `pip install git+https://github.com/mesoscope/cellpack.git`

## Documentation

For full package documentation please visit [mesoscope.github.io/cellpack](https://mesoscope.github.io/cellpack).

## Development

See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for information related to developing the code.

## Remote databases
cellPACK uses AWS and Firebase Firestore as remote databases to store packing results and recipes. Follow [ setup instructions](./docs/REMOTE_DATABASES.md) for access.

## Docker
cellPACK can be run in Docker containers for both AWS ECS and AWS Batch. Follow the [instructions](./docs/DOCKER.md) to set up the Docker environment.

**MIT license**