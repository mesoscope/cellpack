# Installation using uv
This project requires Python 3.11. The installation is managed using [uv](https://docs.astral.sh/uv/).

Dependencies are listed in the `pyproject.toml` file and locked in the `uv.lock` file.

**1. Navigate to where you want to clone this repository**

```bash
cd /path/to/directory/
```

**2. Clone the repo from GitHub**

```bash
git clone git@github.com:mesoscope/cellpack-analysis.git
cd cellpack-analysis
```

**3. Install the dependencies using uv**

For basic installation with just the core dependencies:

```bash
uv sync --no-dev
```

If you plan to develop code, you should also install the development dependencies:

```bash
uv sync
```

To install extra dependencies:

```bash
uv sync --all-extras
```

**4. Activate the virtual environment**

Activate the virtual environment in the terminal:

For Windows:

```powershell
\path\to\venv\Scripts\activate
```

For Linux/Mac:

```bash
source /path/to/venv/bin/activate
```

You can deactivate the virtual environment using:

```
deactivate
```

### Run tests
To run the tests, use:

```bash
uv run pytest
```