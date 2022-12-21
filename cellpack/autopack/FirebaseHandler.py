import firebase_admin
from firebase_admin import credentials, firestore

    
class FirebaseHandler(object):
    def __init__(self, cred_path):
        login = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(login)
        self.db = firestore.client()

    def get_doc_by_name(self, collection, name):
        db = self.db
        data_ref = db.collection(collection)
        docs = data_ref.where("name", "==", name).get() #docs is an array
        if len(docs) == 1:
            doc = docs[0]
            return doc.id, docs.to_dict()
        else: 
            # TODO: what to do with duplicate docs
            return None, None

    def set_doc(self, collection, id, data):
        if not self.get_doc_by_id(collection, id):
            return self.db.collection(collection).document(id).set(data)
        else:
            print(f"ERROR, already data at this path:{collection}/{id}")

    def upload_doc(self, collection, data):
        return self.db.collection(collection).add(data)

    def create_path(collection, doc_id):
        return  f"firebase:{collection}/{doc_id}"

    def get_doc_by_id(self, collection, id):
        return self.db.collection(collection).document(id).get()

    def update_reference_on_doc(self, doc_ref, index, new_item_ref):
        doc_ref.update({ index: new_item_ref })

    # # get a document with a known ID
    # def read_from_firestore(self, collection, id):
    #     doc = self.db.collection(collection).document(id).get()
    #     if doc.exists:
    #         return doc.to_dict()
    #     else:
    #         return "requested doc doesn't exist in firestore"