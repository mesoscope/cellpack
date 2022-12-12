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
        
    def reconstruct_dict(self, data):
        modified_data = {}
        for key, value in data.items():
            # convert bonding_box 2d array to dict
            if key == "bounding_box":
                bb_dict = dict(zip([str(i) for i in range(len(value))], value))
                modified_data[key] = bb_dict
            # If the value is an object, we want to convert it to dict 
            elif isinstance(value, object) and "__dict__" in dir(value):
                modified_data[key] = vars(value)
            # If the value is a dictionary, recursively convert its nested lists to dictionaries
            elif isinstance(value, dict):
                modified_data[key] = self.reconstruct_dict(value)
            else:
                modified_data[key] = value

        return modified_data


    # add documents with auto IDs
    def to_firestore(self, collection, data, id=None):
        # check if the incoming new data exists in db
        if id is None: 
            data_ref = self.db.collection(collection)
            name = data["name"]
            query_ref = data_ref.where("name", "==", name)
            docs = query_ref.get()
            if docs and data.isEqual(docs):
                print("this data already exists in firestore")
            else: 
                doc_ref = self.db.collection(collection).add(data)
                print(f"successfully uploaded to path: {doc_ref.path}")
        #TODO: check when the id will not be None
        else:
            doc_ref = self.db.collection(collection).add(data)
        return doc_ref

    def upload_recipe(self, recipe_data):
        recipe_name = recipe_data["name"]
        recipe_version = recipe_data["version"]
        key = f"{recipe_name}_v{recipe_version}"
        # TODO: check we want to use version or format_version 
        # if doc.exists()
            # if it already does, throw error, tell user to version the recipe
            # if they still want to upload it 
        # LONGER TERM: could check to see if all the data is the same and let the user know 
        recipe_ref = self.to_firestore("recipes", recipe_data, key)
        print(f"successfully uploaded recipe to path: {recipe_ref.path}")

    def divide_recipe_into_collections(self, recipe_meta_data, recipe_data):
        recipe_to_save = copy.deepcopy(recipe_meta_data)
        objects = recipe_data["objects"]
        composition = recipe_data["composition"]
        gradients = recipe_data.get("gradients")
        objects_to_path_map = {}
        comp_to_path_map = {}
        for obj_name in objects:
            object_doc = objects[obj_name]
            object_doc["name"] = obj_name
            obj_ref = self.to_firestore("objects", object_doc)
            objects_to_path_map[obj_name] = obj_ref.path

        for comp_name in composition:
            comp_obj = composition[comp_name]
            if "object" in comp_obj: 
                obj_name = comp_obj["object"]
                obj_path = objects_to_path_map.get(obj_name)
                comp_obj["object"] = obj_path
            if "regions" in comp_obj:
                for region_name, region_array in comp_obj["regions"].items():
                    for region_item in region_array:
                        if isinstance(region_item, dict):
                            obj_name = region_item["object"]
                            region_item["object"] = objects_to_path_map.get(obj_name)
                        else: 
                            #what cases are for else? 
                            pass
            comp_obj["name"] = comp_name
            comp_ref = self.to_firestore("composition", comp_obj)
            comp_to_path_map[comp_name] = comp_ref.path
            recipe_to_save["composition"][comp_name] = { "inherit" : comp_to_path_map[comp_name] }
            #TODO: update comp path -- i.e. replace "nucleus" with nucleus comp path in membrane comp              

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
