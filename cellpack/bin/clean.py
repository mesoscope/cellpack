# cleans the local cache directory
import shutil
from cellpack.autopack import CACHE_DIR
import fire
import os


def clean():
    """
    Cleans the local cache directory
    :return: void
    """
    for _, folder in CACHE_DIR.items():
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


# Run directly from command line
def main():
    fire.Fire(clean)


if __name__ == "__main__":
    main()
