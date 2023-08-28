import firebase_admin
import ast
from firebase_admin import credentials, firestore
from cellpack.autopack.loaders.utils import read_json_file, write_json_file


class FirebaseHandler(object):
    """
    Retrieve data and perform common tasks when working with firebase.
    """

    def __init__(self):
        cred_path = FirebaseHandler.get_creds()
        login = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(login)
        self.db = firestore.client()
        self.name = "firebase"

    @staticmethod
    def doc_to_dict(doc):
        return doc.to_dict()

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
    def get_creds():
        creds = read_json_file("./.creds")
        if creds is None or "firebase" not in creds:
            creds = FirebaseHandler.write_creds_path()
        return creds["firebase"]

    def db_name(self):
        return self.name

    @staticmethod
    def doc_id(doc):
        return doc.id

    @staticmethod
    def create_path(collection, doc_id):
        return f"firebase:{collection}/{doc_id}"

    @staticmethod
    def get_path_from_ref(doc):
        return doc.path

    @staticmethod
    def get_collection_id_from_path(path):
        # path example = firebase:composition/uid_1
        components = path.split(":")[1].split("/")
        collection = components[0]
        id = components[1]
        return collection, id

    @staticmethod
    def update_reference_on_doc(doc_ref, index, new_item_ref):
        doc_ref.update({index: new_item_ref})

    @staticmethod
    def update_elements_in_array(doc_ref, index, new_item_ref, remove_item):
        doc_ref.update({index: firestore.ArrayRemove([remove_item])})
        doc_ref.update({index: firestore.ArrayUnion([new_item_ref])})

    @staticmethod
    def is_reference(path):
        if not isinstance(path, str):
            return False
        if path is None:
            return False
        if path.startswith("firebase:"):
            return True
        return False

    def get_doc_by_name(self, collection, name):
        db = self.db
        data_ref = db.collection(collection)
        docs = data_ref.where("name", "==", name).get()  # docs is an array
        return docs

    # `doc` is a DocumentSnapshot object
    # `doc_ref` is a DocumentReference object to perform operations on the doc
    def get_doc_by_id(self, collection, id):
        doc_ref = self.db.collection(collection).document(id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict(), doc_ref
        else:
            return None, None

    def get_doc_by_ref(self, path):
        collection, id = FirebaseHandler.get_collection_id_from_path(path)
        return self.get_doc_by_id(collection, id)

    def set_doc(self, collection, id, data):
        doc, doc_ref = self.get_doc_by_id(collection, id)
        if not doc:
            doc_ref = self.db.collection(collection).document(id)
            doc_ref.set(data)
            print(f"successfully uploaded to path: {doc_ref.path}")
            return doc_ref
        else:
            print(
                f"ERROR: {doc_ref.path} already exists. If uploading new data, provide a unique recipe name."
            )
            return

    def upload_doc(self, collection, data):
        return self.db.collection(collection).add(data)

    @staticmethod
    def is_firebase_obj(obj):
        return isinstance(
            obj, (firestore.DocumentReference, firestore.DocumentSnapshot)
        )
