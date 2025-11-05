import sys
import fire
import json

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
        return recipe_meta_data
    except KeyError as e:
        sys.exit(f"Recipe metadata is missing. {e}")


def upload(
    recipe_path=None,
    config_path=None,
    db_id=DATABASE_IDS.FIREBASE,
    studio: bool = False,
    fields: str = None,
    name: str = None,
):
    """
    Uploads a recipe to the database

    :param recipe: string argument
    path to local recipe file to upload to firebase
    :param config: string argument
    path to local config file to upload to firebase
    :param db_id: string argument
    database ID to use for the upload
    :param studio: boolean argument
    upload for use in cellPACK studio if True
    :param fields: string argument
    path to local editable fields file to upload to firebase
    :param name: string argument
    display name for recipe in studio selection menu

    :return: void
    """
    recipe_id = ""
    config_id = ""
    editable_fields_ids = []
    if db_id == DATABASE_IDS.FIREBASE:
        # fetch the service key json file
        db_handler = FirebaseHandler()
        if FirebaseHandler._initialized:
            db_handler = DBUploader(db_handler)
            if recipe_path:
                recipe_loader = RecipeLoader(recipe_path)
                recipe_full_data = recipe_loader._read(resolve_inheritance=False)
                recipe_meta_data = get_recipe_metadata(recipe_loader)
                recipe_id = db_handler.upload_recipe(recipe_meta_data, recipe_full_data)
            if config_path:
                config_data = ConfigLoader(config_path).config
                config_id = db_handler.upload_config(config_data, config_path)
            if fields:
                editable_fields_data = json.load(open(fields, "r"))
                for field in editable_fields_data.get("editable_fields", []):
                    id, _ = db_handler.upload_data("editable_fields", field)
                    editable_fields_ids.append(id)
            if studio:
                recipe_metadata = {
                    "name": name,
                    "recipe": recipe_id,
                    "config": config_id,
                    "editable_fields": editable_fields_ids,
                }
                # Upload the combined recipe metadata to example_packings collection for studio
                db_handler.upload_data("example_packings", recipe_metadata)

        else:
            db_maintainer = DBMaintenance(db_handler)
            sys.exit(
                f"The selected database is not initialized. Please set up Firebase credentials to upload recipes. Refer to the instructions at {db_maintainer.readme_url()} "
            )


def main():
    fire.Fire(upload)


if __name__ == "__main__":
    main()
