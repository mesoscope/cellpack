# cleans the local cache directory
import logging
import shutil
from pathlib import Path

import fire

from cellpack.autopack import appdata

log = logging.getLogger(__name__)


def clean(cache_dir_path: Path | str = appdata):
    """
    Cleans the local cache directories.

    Parameters
    ----------
    cache_dir_path
        The path to the cache directory. Defaults to the appdata directory.
    """
    cache_dir_path = Path(cache_dir_path)
    if not cache_dir_path.exists():
        log.error(f"Cache directory {cache_dir_path} does not exist.")
        return
    elif not cache_dir_path.is_dir():
        log.error(f"Cache directory {cache_dir_path} is not a directory.")
    else:
        log.info("Cleaning cache located at %s", cache_dir_path)

    for folder in cache_dir_path.iterdir():
        for file_path in folder.iterdir():
            try:
                if file_path.is_file() or file_path.is_symlink():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                log.warning(f"Failed to delete {file_path}. Exception: {e}")
    log.info("Cache cleaned successfully.")


# Run directly from command line
def main():
    fire.Fire(clean)


if __name__ == "__main__":
    main()
