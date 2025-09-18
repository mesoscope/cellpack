# cleans the local cache directory
import fire
import os
import shutil
from cellpack.autopack import CACHE_DIR


def clean(cache_dir=CACHE_DIR):
    """
    Cleans the local cache directory
    :param cache_dir: dict, the cache directory
    :return: void
    """
    for _, folder in cache_dir.items():
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Exception: {e}")
    print("Cache cleaned")


def main():
    fire.Fire(clean)


# Run directly from command line
if __name__ == "__main__":
    main()
