import sys
import fire

from cellpack.autopack.FirebaseHandler import FirebaseHandler
from cellpack.autopack.DBRecipeHandler import DBUploader

from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS
from cellpack.autopack.loaders.recipe_loader import RecipeLoader


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
            recipe_meta_data = recipe_loader.get_only_recipe_metadata()
            recipe_db_handler = DBUploader(db_handler)
            recipe_db_handler.upload_recipe(recipe_meta_data, recipe_full_data)
        else:
            sys.exit(
                "The selected database is not initialized. Please set up Firebase credentials to upload recipes."
            )


def main():
    fire.Fire(upload)


if __name__ == "__main__":
    main()
