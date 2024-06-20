import sys
import fire

from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.DBRecipeHandler import DBUploader, DBMaintenance

from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.recipe_loader import RecipeLoader


def get_recipe_metadata(loader):
    """
    Fetches and returns the metadata of the recipe for uploading
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
        return recipe_meta_data
    except KeyError as e:
        sys.exit(f"Recipe metadata is missing. {e}")


def upload(
    recipe_path,
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
            recipe_loader = RecipeLoader(recipe_path)
            recipe_full_data = recipe_loader._read(resolve_inheritance=False)
            recipe_meta_data = get_recipe_metadata(recipe_loader)
            recipe_db_handler = DBUploader(db_handler)
            recipe_db_handler.upload_recipe(recipe_meta_data, recipe_full_data)
        else:
            db_maintainer = DBMaintenance(db_handler)
            sys.exit(
                f"The selected database is not initialized. Please set up Firebase credentials to upload recipes. Refer to the instructions at {db_maintainer.readme_url()} "
            )


def main():
    fire.Fire(upload)


if __name__ == "__main__":
    main()
