import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import numpy as np
import copy

# testing path for setup
cred_path = r"/Users/Ruge/Desktop/Allen Internship/cellPACK/cellpack-data-582d6-firebase-adminsdk-3pkkz-27a3ec0777.json"

# fetch the service key json file
login = credentials.Certificate(cred_path)

# initialize firebase
firebase_admin.initialize_app(login)

# connect to db
db = firestore.client()


def reconstruct_dict(data):
    modified_d = {}
    for key, value in data.items():
        # If the value is a list, convert it to a dictionary with keys "array_0", "array_1", etc.
        if isinstance(value, list):
            arr_dict = {}
            for i, element in enumerate(value):
                # Check if element is a nested list
                #TODO use recursion to convert nested lists too, an inner func?
                if not isinstance(element, list):
                    continue
                elif any(isinstance(ele, list) for ele in element):
                    nested_arr_dict = {}
                    for j, nested_element in enumerate(element):
                        nested_arr_dict["array_{}".format(j)] = nested_element
                    arr_dict["array_{}".format(i)] = nested_arr_dict
                # Otherwise, element is a flat list or a non-list, so we can just add it to arr_dict
                else:
                    arr_dict["array_{}".format(i)] = element
            modified_d[key] = arr_dict
        # If the value is an object, we want to convert it to dict 
        elif isinstance(value, object) and "__dict__" in dir(value):
            modified_d[key] = vars(value)
        # If the value is a dictionary, recursively convert its nested lists to dictionaries
        elif isinstance(value, dict):
            modified_d[key] = reconstruct_dict(value)
        else:
            modified_d[key] = value

    return modified_d


# add documents with known IDs
def save_to_firestore(collection,id,data):
    original_data = copy.deepcopy(data)
    modified_data = reconstruct_dict(data)
    db.collection(collection).document(id).set(modified_data)
    return original_data


# get a document with a known ID
# def get_doc_from_firestore(collection, id):
#     doc = db.collection(collection).document(id).get()
#     if doc.exists:
#         return doc.to_dict()
#     else:
#         return "requested doc doesn't exist in firestore"


# # get all documents in a collection
# def get_all_docs_from_firestore(collection):
#     docs = db.collection(collection).get()
#     docs_list = []
#     for doc in docs:
#         docs_list.append(doc.to_dict())
#     print(docs_list)
#     return docs_list
