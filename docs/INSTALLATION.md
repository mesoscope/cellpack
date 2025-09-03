# Installation with `pyenv` and `pdm`
`pyenv` allows you to install multiple python versions side by side in your local user environment. This installation method is preferred over using `conda` to install `pdm`

### Install pyenv
1. Install pyenv: Follow the `pyenv` installation instructions [here](https://github.com/pyenv/pyenv#installation). There are just two steps.
1.  Download and install `pyenv`
2. Add `pyenv` functions to your shell configuration.

### Install python 3.9
Navigate to the `cellPACK` folder and install the required python version.
```bash
pyenv install $(cat .python-version)
```
The `.python-version` file in this repo tells `pyenv` to load Python 3.9 when you are inside the `cellPACK` directory.
Check that this is working with `which python && python --version`.

### Install `pdm`
Detailed installation instructions are available [here](https://pdm.fming.dev/latest/#installation).
For Linux or MacOS, install `pdm` for your user as follows.

1. Download the installer

```bash
curl -sSLO https://pdm.fming.dev/install-pdm.py
```

2. Validate that the installer has not been tampered with

```bash
curl -sSL https://pdm.fming.dev/install-pdm.py.sha256 | shasum -a 256 -c -
```

3. Using Python 3.9, run the installer.

```bash
python install-pdm.py
```
> [!WARNING]
> With this installation method `pdm` will be tied to the exact python version used to install it. If you installed with Python 3.9.13, for example, and you later transition to Python 3.9.17, do not uninstall Python 3.9.13.

`pdm` will be installed into `$HOME/.local/bin`. Check that your version is at least 2.10.
```bash
$ pdm --version
PDM, version 2.10.4
```

### Install the project dependencies
From the `cellPACK` directory, use `pdm` to install the dependencies.
```bash
pdm sync -d
```

This will create a virtual environment at `cellPACK/.venv`. You can activate it with `eval $(pdm venv activate)` or `source .venv/bin/activate`.

### Managing dependencies with `pdm`
To modify the project dependencies, see [our instructions for using pdm](./pdm.md).


## Testing
To run tests:
```bash
pdm run pytest
```