import ast
import logging
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from google.cloud.exceptions import NotFound
from cellpack.autopack.loaders.utils import read_json_file, write_json_file
from cellpack.autopack.interface_objects.default_values import (
    default_firebase_collection_names,
)


class FirebaseHandler(object):
    """
    Retrieve data and perform common tasks when working with firebase.
    """

    # use class attributes to maintain a consistent state across all instances
    _initialized = False
    _db = None

    def __init__(self, default_db=None):
        # check if firebase is already initialized
        if not FirebaseHandler._initialized:
            db_choice = FirebaseHandler.which_db(default_db=default_db)
            cred = FirebaseHandler.get_creds(db_choice)
            if cred:
                login = credentials.Certificate(cred)
                firebase_admin.initialize_app(login)
                FirebaseHandler._db = firestore.client()
                FirebaseHandler._initialized = True

        self.db = FirebaseHandler._db
        self.name = "firebase"

    # common utility methods
    @staticmethod
    def which_db(default_db=None):
        options = {"1": "dev", "2": "staging"}
        if default_db in options.values():
            print(f"Using {default_db} database -------------")
            return default_db
        for key, value in options.items():
            print(f"[{key}] {value}")
        choice = input("Enter number: ").strip()
        print(f"Using {options.get(choice, 'dev')} database -------------")
        return options.get(choice, "dev")  # default to dev db for recipe uploads

    @staticmethod
    def get_creds(db_choice):
        if db_choice == "staging":
            cred = FirebaseHandler.get_staging_creds()
        else:
            cred = FirebaseHandler.get_dev_creds()
        return cred

    @staticmethod
    def doc_to_dict(doc):
        return doc.to_dict()

    @staticmethod
    def doc_id(doc):
        return doc.id

    @staticmethod
    def create_path(collection, doc_id):
        return f"firebase:{collection}/{doc_id}"

    @staticmethod
    def create_timestamp():
        return firestore.SERVER_TIMESTAMP

    @staticmethod
    def get_path_from_ref(doc):
        return doc.path

    @staticmethod
    def get_collection_id_from_path(path):
        try:
            components = path.split(":")[1].split("/")
            collection = components[0]
            id = components[1]
            if collection not in default_firebase_collection_names:
                raise ValueError(
                    f"Invalid collection name: '{collection}'. Choose from: {default_firebase_collection_names}"
                )
        except IndexError:
            raise ValueError(
                "Invalid path provided. Expected format: firebase:collection/id"
            )
        return collection, id

    # Create methods
    def set_doc(self, collection, id, data):
        doc, doc_ref = self.get_doc_by_id(collection, id)
        if not doc:
            doc_ref = self.db.collection(collection).document(id)
            doc_ref.set(data)
            logging.info(f"successfully uploaded to path: {doc_ref.path}")
            return doc_ref
        else:
            logging.error(
                f"ERROR: {doc_ref.path} already exists. If uploading new data, provide a unique recipe name."
            )
            return

    def upload_doc(self, collection, data):
        return self.db.collection(collection).add(data)

    # Read methods
    @staticmethod
    def get_dev_creds():
        creds = read_json_file("./.creds")
        if creds is None or "firebase" not in creds:
            creds = FirebaseHandler.write_creds_path()
        return creds["firebase"]

    @staticmethod
    def get_staging_creds():
        # set override=True to refresh the .env file if softwares or tokens updated
        load_dotenv(dotenv_path="./.env", override=False)
        FIREBASE_TOKEN = os.getenv("FIREBASE_TOKEN")
        FIREBASE_EMAIL = os.getenv("FIREBASE_EMAIL")
        if not FIREBASE_TOKEN or not FIREBASE_EMAIL:
            return
        firebase_key = FIREBASE_TOKEN.replace("\\n", "\n")
        return {
            "type": "service_account",
            "project_id": "cell-pack-database",
            "client_email": FIREBASE_EMAIL,
            "private_key": firebase_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }

    @staticmethod
    def get_username():
        creds = read_json_file("./.creds")
        try:
            return creds["username"]
        except KeyError:
            raise ValueError("No username found in .creds file")

    def db_name(self):
        return self.name

    def get_doc_by_name(self, collection, name):
        db = self.db
        data_ref = db.collection(collection)
        docs = data_ref.where("name", "==", name).get()  # docs is an array
        return docs

    def get_doc_by_id(self, collection, id):
        # `doc` is a DocumentSnapshot object
        # `doc_ref` is a DocumentReference object to perform operations on the doc
        doc_ref = self.db.collection(collection).document(id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict(), doc_ref
        else:
            return None, None

    def get_doc_by_ref(self, path):
        collection, id = FirebaseHandler.get_collection_id_from_path(path)
        return self.get_doc_by_id(collection, id)

    def get_all_docs(self, collection):
        try:
            docs_stream = self.db.collection(collection).stream()
            docs = list(docs_stream)
            return docs
        except Exception as e:
            logging.error(
                f"An error occurred while retrieving docs from collection '{collection}': {e}"
            )
            return None

    def get_value(self, collection, id, field):
        doc, _ = self.get_doc_by_id(collection, id)
        if doc is None:
            return None
        return doc[field]

    # Update methods
    def update_doc(self, collection, id, data):
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.update(data)
        logging.info(f"successfully updated to path: {doc_ref.path}")
        return doc_ref

    @staticmethod
    def update_reference_on_doc(doc_ref, index, new_item_ref):
        doc_ref.update({index: new_item_ref})

    @staticmethod
    def update_elements_in_array(doc_ref, index, new_item_ref, remove_item):
        doc_ref.update({index: firestore.ArrayRemove([remove_item])})
        doc_ref.update({index: firestore.ArrayUnion([new_item_ref])})

    def update_or_create(self, collection, id, data):
        """
        If the input id exists, update the doc. If not, create a new file.
        """
        try:
            self.update_doc(collection, id, data)
        except NotFound:
            self.set_doc(collection, id, data)

    # Delete methods
    def delete_doc(self, collection, id):
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.delete()
        logging.info(f"successfully deleted path: {doc_ref.path}")
        return doc_ref.id

    # other utils
    @staticmethod
    def write_creds_path():
        path = ast.literal_eval(input("provide path to firebase credentials: "))
        data = read_json_file(path)
        if data is None:
            raise ValueError("The path to your credentials doesn't exist")
        firebase_cred = {"firebase": data}
        creds = read_json_file("./.creds")
        if creds is None:
            write_json_file("./.creds", firebase_cred)
        else:
            creds["firebase"] = data
            write_json_file("./.creds", creds)
        return firebase_cred

    @staticmethod
    def is_reference(path):
        if not isinstance(path, str):
            return False
        if path is None:
            return False
        if path.startswith("firebase:"):
            return True
        return False

    @staticmethod
    def is_firebase_obj(obj):
        return isinstance(
            obj, (firestore.DocumentReference, firestore.DocumentSnapshot)
        )

    def check_doc_existence(self, collection, doc_data):
        doc_hash = doc_data.get("dedup_hash")
        query = (
            self.db.collection(collection).where("dedup_hash", "==", doc_hash).limit(1)
        )
        docs = list(query.stream())
        if any(docs):
            logging.info("Document already exists in database.")
            return docs[0].reference
        return None
