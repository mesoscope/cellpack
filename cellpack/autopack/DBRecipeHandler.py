import copy


# default_creds = r"/Users/Ruge/Desktop/Allen Internship/cellPACK/cellpack-data-582d6-firebase-adminsdk-3pkkz-27a3ec0777.json"


# # fetch the service key json file
# login = credentials.Certificate(default_creds)
# # initialize firebase
# firebase_admin.initialize_app(login)
# # connect to db
# db = firestore.client()

recipe_data = {
    "version": "1.0.0",
    "format_version": "2.0",
    "name": "peroxisomes_test",
    "bounding_box": [
        [
            -110,
            -45,
            -62
        ],
        [
            110,
            45,
            62
        ]
    ],
    "objects": {
        "mean_membrane": {
            "type": "mesh",
            "color": [
                0.5,
                0.5,
                0.5
            ],
            "representations": {
                "mesh": {
                    "path": "https://www.dl.dropboxusercontent.com/s/4d7rys8uwqz72xy/",
                    "name": "mean-membrane.obj",
                    "format": "obj"
                }
            }
        },
        "mean_nucleus": {
            "type": "mesh",
            "color": [
                0.25,
                0.25,
                0.25
            ],
            "representations": {
                "mesh": {
                    "path": "https://www.dl.dropboxusercontent.com/s/3194r3t40ewypxh/",
                    "name": "mean-nuc.obj",
                    "format": "obj"
                }
            }
        },
        "peroxisome": {
            "jitter_attempts": 300,
            "type": "single_sphere",
            "color": [
                0.20,
                0.70,
                0.10
            ],
            "radius": 2.30
        }
    },
    "composition": {
        "bounding_area": {
            "regions": {
                "interior": [
                    "membrane"
                ]
            }
        },
        "membrane": {
            "object": "mean_membrane",
            "count": 1,
            "regions": {
                "interior": [
                    "nucleus",
                    {
                        "object": "peroxisome",
                        "count": 121
                    }
                ]
            }
        },
        "nucleus": {
            "object": "mean_nucleus",
            "count": 1,
            "regions": {
                "interior": []
            }
        }
    }
}


recipe_meta_data = {
            "format_version": recipe_data["format_version"],
            "version": recipe_data["version"],
            "name": recipe_data["name"],
            "bounding_box": recipe_data["bounding_box"],
            "composition": {},
        }

class DBRecipeHandler(object):
    def __init__(self, db_handler):
        self.db = db_handler
    
    @staticmethod
    def reconstruct_dict(data):
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
                modified_data[key] = DBRecipeHandler.reconstruct_dict(value)
            else:
                modified_data[key] = value

        return modified_data

    def should_write(self, local_data, db_data) -> bool:
        # compare everything except literal value of references 
        # ie, don't compare "nucleus" to "firebase:path_to_nucleus_object"
        # compare contents of "nucleus" object to contents of what is at 
        # "firebase:path_to_nucleus_object"
        # return True if no duplicate data is found 
        # return False if data already exists in database
        pass

    # add documents with auto IDs
    def to_db(self, collection, data, id=None):
        # check if we need to convert part of the data(2d arrays and objs to dict) 
        modified_data = DBRecipeHandler.reconstruct_dict(data)
        # check if the incoming new data exists in db
        if id is None: 
            # data_ref = db.collection(collection)
            name = modified_data["name"]
            # docs = data_ref.where("name", "==", name).get() #docs is an array
            doc_id, doc = self.db.get_doc_by_name(collection, name)
            if not self.should_write(modified_data, doc):
                print(f"{collection}/{name} is already exists in firestore")
                return self.db.create_path(collection, doc_id)
            else: 
                doc, id = self.db.upload_doc(collection, modified_data)
                #doc_ref is a tuple, path example: collection/id
                doc_path = id.path
                print(f"successfully uploaded {name} to path: {doc_path}")
        else:
            doc_path = f"{collection}/{id}"
            doc = self.db.set_doc(collection, id, modified_data)
            print(f"successfully uploaded to path: {doc_path}")
        return f"firebase:{doc_path}"

    def upload_recipe(self, recipe_data):
        recipe_name = recipe_data["name"]
        recipe_version = recipe_data["version"]
        key = f"{recipe_name}_v{recipe_version}"
        self.to_db("recipes", recipe_data, key)

    #update
    def update_reference(self, composition_name, path_to_referring_comp, index):
        id, doc = self.db.get_doc_by_name("composition", composition_name)
        if id is None:
            return
        else:
            new_item_ref = self.db.create_path("composition", id)
            self.db.update_reference_on_doc(path_to_referring_comp, index, new_item_ref)
        
    def divide_recipe_into_collections(self, recipe_meta_data, recipe_data):
        recipe_to_save = copy.deepcopy(recipe_meta_data)
        objects = recipe_data["objects"]
        composition = recipe_data["composition"]
        # gradients = recipe_data.get("gradients")
        objects_to_path_map = {}
        comp_to_path_map = {}
        references_to_update = {}
        # {"nucleus": path in db }
        # save objects to db
        upload_objects(objects, objects_to_path_map)
        # save comps to db
        # while not updated_all:
        for comp_name in composition:
            comp_obj = composition[comp_name]
            # replace with paths for outer objs in comp 
            if "object" in comp_obj.keys(): 
                obj_name = comp_obj["object"]
                obj_database_path = objects_to_path_map.get(obj_name)
                comp_obj["object"] = obj_database_path
            if "regions" in comp_obj:
                for region_name, region_array in comp_obj["regions"].items():
                    if len(region_array) == 0:
                        comp_obj["name"] = comp_name
                        comp_path = self.db.to_db("composition", comp_obj)
                        comp_to_path_map[comp_name] = comp_path
                        continue
                    for region_item in region_array:
                        # replace with paths for inner objs in comp["regions"]
                        if isinstance(region_item, dict):
                            obj_name = region_item["object"]
                            region_item["object"] = objects_to_path_map.get(obj_name)
                        # replace with paths for comps
                        elif isinstance(region_item, str):
                            # region item is a string 
                            # if region_item in comp_to_path_map:
                            #     comp_obj["regions"][region_name][region_array.index(region_item)] = comp_to_path_map[region_item]
                            #     print(f"comp path of {region_item} updated in {comp_name}")
                            #     comp_obj["name"] = comp_name
                            references_to_update[region_item] = f"{comp_name}/regions/{region_name}"
                        comp_path = self.db.to_db("composition", comp_obj)
                        comp_to_path_map[comp_name] = comp_path
        
        # once we are done uploading all the composition objects
        # we need to go through each one and update the 
        # reference to other db objects  
        for comp_name in comp_to_path_map:
            id, doc = self.db.get_doc_by_name("composition", comp_name)
            ref_path_to_update = references_to_update[comp_name]
            # should give us something like "bounding_area/regions/interior"
            self.update_reference(comp_name)
            # comp_obj["name"] = comp_name
            # comp_obj_check_update[comp_name] = comp_obj
            # comp_path = to_firestore("composition_sun", comp_obj)
            # comp_to_path_map[comp_name] = comp_path
            # recipe_to_save["composition"][comp_name] = { "inherit" : comp_to_path_map[comp_name] }  
        # _update_comp_ref_in_comp_obj(comp_obj_check_update, comp_to_path_map)         
        self.upload_recipe(recipe_to_save)
        


def get_collection_id_from_path(path_to_recipe):
        #path example = firebase:composition/uid_1
        components = path_to_recipe.split(":")[1].split("/")
        collection = components[0]
        id = components[1]
        return collection, id



        
def upload_objects(self, objects, objects_to_path_map):
    for obj_name in objects:
        object_doc = objects[obj_name]
        object_doc["name"] = obj_name
        obj_path = to_firestore("objects", object_doc)
        objects_to_path_map[obj_name] = obj_path        


    
        



# #example of using `Reference` class 
# composition_ref = firestore.collection("composition")
# nucleus_ref = composition_ref.document("uid_1")

# membrane_comp_doc = {
#                         "name": "membrane",
#                         "object": "firebase:objects/uid_",
#                         "count": 1,
#                         "regions": {
#                             "interior": {
#                                 "0": Reference(nucleus_ref),
#                                 "1": {
#                                     "object": "firebase:objects/uid_",
#                                     "count": 121
#                                 }
#                             }
#                         },
#                     }
# membrane_comp_doc_ref = to_firestore("composition", membrane_comp_doc)

# #example of getting data from the referenced doc 
# nucleus_doc = membrane_comp_doc["regions"]["interior"]["0"].get()
# print(nucleus_doc.to_dict())
        



    # def read_recipe(self, path_to_recipe):
    #     collection, id = self.get_collection_id_from_path(path_to_recipe)
    #     data_from_firebase = self.read_from_firestore(collection, id)
    #     # TODO: convert to recipe that looks like it was read from a file
    #     for k, v in data_from_firebase.items():
    #         if k == "composition":
    #             # convert comp_path
    #             for comp_name in v:
    #                 comp_path = comp_name["inherit"]
    #                 comp_doc = (self.db.document(comp_path).get()).to_dict()
    #                 if "name" in comp_doc:
    #                     del comp_doc["name"]
    #                 #convert obj_path here 
    #     return data_from_firebase
                    
    # def convert_obj_in_comp(self, comp_doc):
    #     for k, v in comp_doc.items():
    #         pass

