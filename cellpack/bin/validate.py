import logging
import logging.config
import fire
import json
from pathlib import Path
from pydantic import ValidationError

from cellpack.autopack.validation.recipe_validator import RecipeValidator

###############################################################################
log_file_path = Path(__file__).parent.parent / "logging.conf"
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


def validate(recipe_path):
    try:
        with open(recipe_path, "r") as f:
            raw_recipe_data = json.load(f)

        RecipeValidator.validate_recipe(raw_recipe_data)

        log.info(f"Recipe {raw_recipe_data['name']} is valid!")
    except ValidationError as e:
        formatted_error = RecipeValidator.format_validation_error(e)
        log.error(formatted_error)
        return


def main():
    fire.Fire(validate)


if __name__ == "__main__":
    main()
