import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import copy

# testing path for setup
cred_path = r"/Users/Ruge/Desktop/Allen Internship/cellPACK/cellpack-data-582d6-firebase-adminsdk-3pkkz-27a3ec0777.json"

# fetch the service key json file
login = credentials.Certificate(cred_path)

# initialize firebase
firebase_admin.initialize_app(login)

# connect to db
db = firestore.client()

d = {
    "version": "1.0.0",
    "format_version": "2.0",
    "name": "one_sphere",
    "bounding_box": [
        [0, 0, 0],
        [100, 100, 100],
    ],
    "objects": {
        "base": {
            "jitter_attempts": 10,
            "orient_bias_range": [
                -3.1415927,
                3.1415927
            ],
            "rotation_range": 6.2831,
            "cutoff_boundary": 0,
            "max_jitter": [
                0.2,
                0.2,
                0.01
            ],
            "perturb_axis_amplitude": 0.1,
            "packing_mode": "random",
            "principal_vector": [
                0,
                0,
                1
            ],
            "rejection_threshold": 50,
            "place_method": "jitter",
            "cutoff_surface": 42,
            "rotation_axis": [
                0,
                0,
                1
            ],
            "available_regions": {
                "interior": {},
                "surface": {},
                "outer_leaflet": {},
                "inner_leaflet": {}
            }
        },
        "sphere_25": {
            "type": "single_sphere",
            "inherit": "base",
            "color": [
                0.5,
                0.5,
                0.5
            ],
            "radius": 25,
            "max_jitter": [
                1,
                1,
                0
            ]
        }
    },
    "composition": {
        "space": {
            "regions": {
                "interior": [[["A", "B", "C"], ["A"], ["C"]], [["foo"], ["bar"]]]
            }
        },
        "A": {"object": "sphere_25", "count": 1},
    },
}




def reconstruct_dict(d):
    # Initialize an empty dictionary to store the modified version of d
    modified_d = {}

    # Iterate over the key-value pairs in d
    for k, v in d.items():
        # If the value is a list, convert it to a dictionary with keys "array_0", "array_1", etc.
        if isinstance(v, list):
            arr_dict = {}
            for i, element in enumerate(v):
                # Check if element is a list, in which case we need to convert it to a dictionary as well
                if isinstance(element, list):
                    nested_arr_dict = {}
                    for j, nested_element in enumerate(element):
                        nested_arr_dict["array_{}".format(j)] = nested_element
                    arr_dict["array_{}".format(i)] = nested_arr_dict
                # Otherwise, element is not a list, so we can just add it to arr_dict
                else:
                    arr_dict["array_{}".format(i)] = element
            modified_d[k] = arr_dict
        # If the value is a dictionary, recursively convert its nested lists to dictionaries
        elif isinstance(v, dict):
            modified_d[k] = reconstruct_dict(v)
        # Otherwise, the value is not a list or a dictionary, so we can just add it to modified_d
        else:
            modified_d[k] = v

    # Return the modified dictionary
    return modified_d

print(reconstruct_dict(d))




# helper function -- we need to convert 2d array(bbox) into dict before storing in firestore
# def convert_nested_array_to_dict(data):
#     for k, v in data.items():
#         if isinstance(v, list):
#             if any(isinstance(ele, list) for ele in v):
#                 converted_dict = dict(zip(["array_" + str(i) for i in range(len(v))], v))
#                 data[k] = converted_dict
#     print(data)
#     return data

# convert_nested_array_to_dict(data)

# add documents with known IDs
# def save_to_firestore(collection,id,data):
#     original_data = copy.deepcopy(data)
#     convert_nested_array_to_dict(data)
#     db.collection(collection).document(id).set(data)
#     return original_data


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
