import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseHandler(object):
    """
    Retrieve data and perform common tasks when working with firebase.
    """

    def __init__(self, cred_path):
        login = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(login)
        self.db = firestore.client()
        self.name = "firebase"

    @staticmethod
    def doc_to_dict(doc):
        return doc.to_dict()

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
            print(f"ERROR, already data at this path:{collection}/{id}")
            return

    def upload_doc(self, collection, data):
        return self.db.collection(collection).add(data)

    @staticmethod
    def is_firebase_obj(obj):
        return isinstance(
            obj, (firestore.DocumentReference, firestore.DocumentSnapshot)
        )
