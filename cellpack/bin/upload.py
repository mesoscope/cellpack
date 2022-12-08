from enum import Enum
import fire
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from cellpack.autopack.firebase import FirebaseHandler

from cellpack.autopack.loaders.recipe_loader import RecipeLoader

class DATABASE_IDS(Enum):
    FIREBASE = "firebase"
    GITHUB = "github"

def upload(cred_path, recipe_path, db_id=DATABASE_IDS.FIREBASE):
    """
    Uploads a recipe to the database

    :return: void
    """
    if db_id==DATABASE_IDS.FIREBASE:
        # testing path for setup
        cred_path = cred_path
        # fetch the service key json file
  
        handler = FirebaseHandler(cred_path)

        recipe_loader = RecipeLoader(recipe_path)
        recipe_full_data = recipe_loader.recipe_data
        recipe_meta_data = recipe_loader.get_only_recipe_metadata()
        

def main():
    fire.Fire(upload)

if __name__ == "__main__":
    main()
