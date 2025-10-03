import logging
import logging.config
import fire
from pathlib import Path

from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def validate(recipe_path):
    try:
        use_docker = recipe_path.startswith("firebase:")
        loader = RecipeLoader(recipe_path, use_docker=use_docker)
        recipe_data = loader.recipe_data
        log.info(f"Recipe {recipe_data['name']} is valid!")

    except ValueError as e:
        log.error(str(e))
        return
    except Exception as e:
        if "firebase" in str(e).lower() and "not initialized" in str(e).lower():
            log.error(
                "Firebase database not initialized. Please set up firebase credentials."
            )
            log.error(
                "See: https://github.com/mesoscope/cellpack?tab=readme-ov-file#introduction-to-remote-databases"
            )
        else:
            log.error(f"Error loading recipe: {e}")
        return


def main():
    fire.Fire(validate)


if __name__ == "__main__":
    main()
