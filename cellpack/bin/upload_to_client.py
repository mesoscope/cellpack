import json
import fire

from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.autopack.loaders.config_loader import ConfigLoader
from cellpack.autopack.loaders.recipe_loader import RecipeLoader
from cellpack.bin.upload import get_recipe_metadata


def upload_to_client(
    recipe: str,
    config: str,
    fields: str,
    name: str
):
    """
    Uploads recipe, config, and editable fields, read from specified
    JSON files, to the database for client access

    :param recipe: string argument
    path to local recipe file to upload to firebase
    :param config: string argument
    path to local config file to upload to firebase
    :param fields: string argument
    path to local editable fields file to upload to firebase
    :param name: string argument
    display name for recipe in client selection menu
    """
    db_handler = FirebaseHandler()
    recipe_id = ""
    config_id = ""
    editable_fields_ids = []
    if FirebaseHandler._initialized:
        db_handler = DBUploader(db_handler)
        if recipe:
            recipe_loader = RecipeLoader(recipe)
            recipe_full_data = recipe_loader._read(resolve_inheritance=False)
            recipe_meta_data = get_recipe_metadata(recipe_loader)
            recipe_id = db_handler.upload_recipe(recipe_meta_data, recipe_full_data)
        if config:
            config_data = ConfigLoader(config).config
            config_id = db_handler.upload_config(config_data, config)
        if fields:
            editable_fields_data = json.load(open(fields, "r"))
            for field in editable_fields_data.get("editable_fields", []):
                id, _ = db_handler.upload_data("editable_fields", field)
                editable_fields_ids.append(id)
        recipe_metadata = {
            "name": name,
            "recipe": recipe_id,
            "config": config_id,
            "editable_fields": editable_fields_ids,
        }

        # Upload the combined recipe metadata to example_packings collection for client
        db_handler.upload_data("example_packings", recipe_metadata)


def main():
    fire.Fire(upload_to_client)


if __name__ == "__main__":
    main()
