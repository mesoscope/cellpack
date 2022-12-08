import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import copy


default_creds = r"/Users/Ruge/Desktop/Allen Internship/cellPACK/cellpack-data-582d6-firebase-adminsdk-3pkkz-27a3ec0777.json"

class FirebaseHandler(object):
    def __init__(self, credentials=default_creds):
        # fetch the service key json file
        login = credentials.Certificate(credentials)
        # initialize firebase
        firebase_admin.initialize_app(login)
        # connect to db
        self.db = firestore.client()

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


    def convert_to_firebase_data(self, data):
        modified_data = reconstruct_dict(data)

    # add documents with known IDs
    def save_to_firestore(self, collection, data, id=None):
        if id is None:
            # use random id
            name = data["name"]
            # but first check db for same name
            # ref = self.db.collection(collection)
            # "query" query_ref = cities_ref.where(u'name', u'==', name)
            # then check if all data is the same, (deep equals)
            # if all data the same, don't upload
            # else, upload with new id 
            id = create_random_id
            self.db.collection(collection).document(id).set(modified_data)
        else:
            self.db.collection(collection).document(id).set(modified_data)
        return f"firebase:{collection}/{id}"

    def upload_recipe(self, recipe_data):
        key = f"{recipe_data["name"]}_v{recipe_data["version"]}"
        # check if recipe exists
        # doc = self.db.collection(collection).document(id)
        # if doc.exists()
            # if it already does, throw error, tell user to version the recipe
            # if they still want to upload it 
        # LONGER TERM: could check to see if all the data is the same and let the user know 
        path = self.save_to_firestore("recipes", recipe_data, id=key)
        # log("successfully uploaded to path:", path)

def divide_recipe_into_collections(self, recipe_meta_data, recipe_data):
    recipe_to_save = recipe_meta_data.copy.deepcopy()
    objects = recipe_data["objects"]
    composition = recipe_data["composition"]
    gradients = recipe_data.get("gradients")
    objects_to_path_map = {}
    for obj_name in objects:
        version = 1.0
        if "version" in objects[obj_name]:
            version = objects[obj_name]["version"]
        objects[obj_name]["version"] = version
        path = self.save_to_firestore("objects", f"{obj_name}/{version}", objects[obj_name])
        objects_to_path_map[obj_name] = path

    for comp_name in composition:
        comp_obj = composition[comp_name]
        if "regions" in comp_obj:
            for region_name, region_array in comp_obj["regions"].items():
                for index in range(len(region_array)):
                    region_item = region_array[index]
                    is_dict = isinstance(region_item, dict)
                    if (is_dict):
                        # if it is a dictionary we want to update the refeence
                        # to the object in the database
                        obj_name = region_item["object"]
                        region_item["object"] = objects_to_path_map[obj_name]
                        
        else: 
            obj_name = comp_obj["object"]
            obj_path = objects_to_path_map[obj_name]
            comp_obj["object"] = obj_path
            path_to_comp = self.save_to_firestore("composition", comp_obj)
            recipe_to_save["composition"][comp_name] = { "inherit" : path_to_comp }


        self.upload_recipe(recipe_to_save)
# get a document with a known ID
# def get_doc_from_firestore(collection, id):
#     doc = db.collection(collection).document(id).get()
#     if doc.exists:
#         return doc.to_dict()
#     else:
#         return "requested doc doesn't exist in firestore"
    get_collection_id_from_path(self )

# # get all documents in a collection
# def get_all_docs_from_firestore(collection):
#     docs = db.collection(collection).get()
#     docs_list = []
#     for doc in docs:
#         docs_list.append(doc.to_dict())
#     print(docs_list)
#     return docs_list
    def read(self, collection, id):
        return self.db.collection(collection).get(id)

    def read_recipe(self, path_to_recipe):
        collection, id = self.get_collection_id_from_path(path_to_recipe)
        data_from_firebase = self.read(collection, id)
        # TODO: convert to recipe that looks like it was read from a file
        # return converted data
