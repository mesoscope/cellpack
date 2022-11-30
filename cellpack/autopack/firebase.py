import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# testing path for setup
cred_path = r"/Users/Ruge/Desktop/Allen Internship/cellPACK/cellpack-data-582d6-firebase-adminsdk-3pkkz-27a3ec0777.json"

# fetch the service key json file
login = credentials.Certificate(cred_path)

# initialize firebase
firebase_admin.initialize_app(login)

# connect to db
db = firestore.client()

#add documents with known IDs 
def save_to_firestore(collection,id,data):
    db.collection(collection).document(id).set(data)


#get a document with a known ID
def get_doc_from_firestore(collection, id):
    doc = db.collection(collection).document(id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return "requested doc doesn't exist in firestore"


#get all documents in a collection 
def get_all_docs_from_firestore(collection):
    docs = db.collection(collection).get()
    docs_list = []
    for doc in docs:
        docs_list.append(doc.to_dict())
    print(docs_list)
    return docs_list
