import copy

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
        upload_objects(self, objects, objects_to_path_map)
        # save comps to db
        for comp_name in composition:
            comp_obj = composition[comp_name]
            # replace with paths for outer objs in comp 
            if "object" in comp_obj: 
                obj_name = comp_obj["object"]
                obj_database_path = objects_to_path_map.get(obj_name)
                comp_obj["object"] = obj_database_path
            if "regions" in comp_obj:
                for region_name, region_array in comp_obj["regions"].items():
                    if len(region_array) == 0:
                        comp_obj["name"] = comp_name
                        comp_path = self.to_db("composition", comp_obj)
                        comp_to_path_map[comp_name] = comp_path
                        continue
                    for region_item in region_array:
                        # replace nested objs in comp["regions"]
                        if isinstance(region_item, dict):
                            obj_name = region_item["object"]
                            region_item["object"] = objects_to_path_map.get(obj_name)
                        # replace comps
                        elif isinstance(region_item, str):
                            references_to_update[comp_name] = references_to_update.update({region_item:region_array.index(region_item)})
                            #e.g.references_to_update = {"membrane": {"nucleus": 0}}
                            # if region_item in comp_to_path_map:
                            #     comp_obj["regions"][region_name][region_array.index(region_item)] = comp_to_path_map[region_item]
                            #     print(f"comp path of {region_item} updated in {comp_name}")
            comp_obj["name"] = comp_name
            comp_path = self.to_db("composition", comp_obj)
                            # comp_to_path_map[comp_name] = comp_path
        
        for comp_name in references_to_update:
            id, doc_ref = self.db.get_doc_by_name("composition", comp_name)
            doc_path = doc_ref.path
            index = references_to_update[comp_name]
            # should give us something like "bounding_area/regions/interior/membrane"
            self.update_reference(comp_name, doc_path)
            # comp_obj["name"] = comp_name
            # comp_obj_check_update[comp_name] = comp_obj
            # comp_path = to_firestore("composition_sun", comp_obj)
            # comp_to_path_map[comp_name] = comp_path
        recipe_to_save["composition"][comp_name] = { "inherit" : comp_to_path_map[comp_name] }  
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
        obj_path = self.to_db("objects", object_doc)
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

