import sys
import fire

from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.DBRecipeHandler import DBUploader, DBMaintenance

from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader


def get_recipe_metadata(loader):
    """
    Extracts and returns essential metadata from a recipe for uploading
    """
    try:
        recipe_meta_data = {
            "format_version": loader.recipe_data["format_version"],
            "version": loader.recipe_data["version"],
            "name": loader.recipe_data["name"],
            "bounding_box": loader.recipe_data["bounding_box"],
            "composition": {},
        }
        if "grid_file_path" in loader.recipe_data:
            recipe_meta_data["grid_file_path"] = loader.recipe_data["grid_file_path"]
        if "randomness_seed" in loader.recipe_data:
            recipe_meta_data["randomness_seed"] = loader.recipe_data["randomness_seed"]
        return recipe_meta_data
    except KeyError as e:
        sys.exit(f"Recipe metadata is missing. {e}")


def upload(
    recipe_path=None,
    config_path=None,
    db_id=DATABASE_IDS.FIREBASE,
):
    """
    Uploads a recipe to the database

    :return: void
    """
    if db_id == DATABASE_IDS.FIREBASE:
        # fetch the service key json file
        db_handler = FirebaseHandler()
        if FirebaseHandler._initialized:
            db_handler = DBUploader(db_handler)
            if recipe_path:
                recipe_loader = RecipeLoader(recipe_path)
                recipe_full_data = recipe_loader._read(resolve_inheritance=False)
                recipe_meta_data = get_recipe_metadata(recipe_loader)
                db_handler.upload_recipe(recipe_meta_data, recipe_full_data)
            if config_path:
                config_data = ConfigLoader(config_path).config
                db_handler.upload_config(config_data, config_path)

        else:
            db_maintainer = DBMaintenance(db_handler)
            sys.exit(
                f"The selected database is not initialized. Please set up Firebase credentials to upload recipes. Refer to the instructions at {db_maintainer.readme_url()} "
            )


def main():
    fire.Fire(upload)


if __name__ == "__main__":
    main()
