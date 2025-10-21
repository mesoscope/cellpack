import logging
import logging.config
from pathlib import Path

import fire

from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def validate(recipe_path):
    try:
        use_remote_db = any(
            recipe_path.startswith(db) for db in DATABASE_IDS.with_colon()
        )
        loader = RecipeLoader(recipe_path, use_docker=use_remote_db)
        recipe_data = loader.recipe_data
        log.debug(f"Recipe {recipe_data['name']} is valid!")

    except ValueError as e:
        log.error(str(e))
        return
    except Exception as e:
        error_msg = str(e).lower()
        if (
            any(db.lower() in error_msg for db in DATABASE_IDS.values())
            and "not initialized" in error_msg
        ):
            log.error(
                "Remote database not initialized. Please set up credentials for the database."
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
