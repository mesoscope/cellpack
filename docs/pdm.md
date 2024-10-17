# Using PDM
These instructions are intended to get you started managing dependencies with PDM. Consult the [PDM documentation](https://pdm.fming.dev/latest/usage/dependency/) for more detailed help.

## Workflow for adding/updating/removing a package
1. To add/update/remove a package, use a Linux machine. The `pdm.lock` file is _usually_ compatible across operating systems, but in some cases `pdm` can generate a lock file that is only compatible with the operating system family used to generate it. Ours should always be compatible with Linux.

2. Start a new branch from `main` (`git checkout main && git checkout -b {branch-name}`), or if you are already on a branch, get the latest changes from the `main` to avoid merge conflicts with `pdm.lock` (`git merge main`).

3. Synchronize the current installed dependencies with the lock file.
```bash
pdm sync
```

4. Update `pyproject.toml` and `pdm.lock`. This will install/update/uninstall the package from your current virtual environment.
```bash
# Add package(s) to pyproject.toml and install them
pdm add {package-name}
# Remove packages from pyproject.toml
pdm remove {package-name}
# Update all packages according to pyproject.toml
pdm update
# Update one package
pdm update {package-name}
```

5. Test and commit your changes to `pyproject.toml` and `pdm.lock`.

6. Make a pull request on Github with your changes and (after approval) merge it.

7. A Github action will make a second pull request to update all three `requirements/{platform}/requirements.txt` files based on your changes. This second PR must be merged before any further changes are made to `pdm.lock`.