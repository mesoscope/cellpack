import logging
import logging.config
import fire
import json
from pathlib import Path
from pydantic import ValidationError

from cellpack.autopack.validation.recipe_validator import RecipeValidator
from cellpack.autopack.loaders.recipe_loader import RecipeLoader

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def validate(recipe_path):
    try:
        if recipe_path.startswith("firebase:"):
            loader = RecipeLoader(recipe_path, use_docker=True)
            recipe_data = loader.recipe_data
            log.info(f"Firebase recipe {recipe_data['name']} is valid!")
        else:
            with open(recipe_path, "r") as f:
                raw_recipe_data = json.load(f)

            RecipeValidator.validate_recipe(raw_recipe_data)
            log.info(f"Local recipe {raw_recipe_data['name']} is valid!")
            
    except ValidationError as e:
        formatted_error = RecipeValidator.format_validation_error(e)
        log.error(formatted_error)
        return
    except ValueError as e:
        log.error(str(e))
        return
    except Exception as e:
        if "firebase" in str(e).lower() and "not initialized" in str(e).lower():
            log.error("Firebase database not initialized. Please set up firebase credentials.")
            log.error("See: https://github.com/mesoscope/cellpack?tab=readme-ov-file#introduction-to-remote-databases")
        else:
            log.error(f"Error loading recipe: {e}")
        return


def main():
    fire.Fire(validate)


if __name__ == "__main__":
    main()
