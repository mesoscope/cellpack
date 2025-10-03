# cleans the local cache directory
import logging
import os
import shutil

import fire

from cellpack.autopack import CACHE_DIR

logger = logging.getLogger(__name__)


def clean(cache_type="all"):
    """
    Cleans the local cache directory
    :param cache_dir: dict, the cache directory
    :return: void
    """
    if cache_type == "all":
        cache_dir = CACHE_DIR
    elif cache_type in CACHE_DIR:
        cache_dir = {cache_type: CACHE_DIR[cache_type]}
    else:
        logger.error(f"Unknown cache type: {cache_type}")
        return

    for _, folder in cache_dir.items():
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Exception: {e}")
    logger.info("Cache cleaned for type: %s", cache_type)


def main():
    fire.Fire(clean)


# Run directly from command line
if __name__ == "__main__":
    main()
