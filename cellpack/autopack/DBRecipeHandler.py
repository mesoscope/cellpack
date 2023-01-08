import copy
# from cellpack.autopack.FirebaseHandler import FirebaseHandler

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
        
    def should_write(self, collection, name, data):
        docs = self.db.get_doc_by_name(collection, name)
        if docs and len(docs) == 1:
            doc = docs[0]
            if doc.to_dict() == data:
                return docs[0].id, False
            else:
                return None, True
        elif isinstance(docs, list):
            for doc in docs:
                if doc.to_dict() == data:
                    return doc.id, False
        return None, True

    # add documents with auto IDs
    def to_db(self, collection, data, id=None):
        # check if we need to convert part of the data(2d arrays and objs to dict) 
        modified_data = DBRecipeHandler.reconstruct_dict(data)
        if id is None: 
            name = modified_data["name"]
            doc_id, write = self.should_write(collection, name, modified_data)
            if not write:
                print(f"{collection}/{name} is already exists in firestore")
                return doc_id, self.db.create_path(collection, doc_id)
            else: 
                doc = self.db.upload_doc(collection, modified_data)
                # doc is a tuple, e.g (DatetimeWithNanoseconds, data_obj)
                doc_path = doc[1].path
                doc_id = doc[1].id
                print(f"successfully uploaded {name} to path: {doc_path}")
                return doc_id, self.db.create_path(collection, doc_id)
        else:
            doc_path = f"{collection}/{id}"
            doc = self.db.set_doc(collection, id, modified_data)
    
    def upload_objects(self, objects, objects_to_path_map):
        for obj_name in objects:
            object_doc = objects[obj_name]
            object_doc["name"] = obj_name
            doc, obj_path = self.to_db("objects", object_doc)
            objects_to_path_map[obj_name] = obj_path   

    def get_recipe_id(self, recipe_data):
        recipe_name = recipe_data["name"]
        recipe_version = recipe_data["version"]
        key = f"{recipe_name}_v{recipe_version}"
        return key

    def upload_recipe(self, recipe_data):
        key = self.get_recipe_id(recipe_data)
        self.to_db("recipes", recipe_data, key)

    def update_reference(self, composition_id, referring_comp_id, index, remove_comp_name, update_in_array=False):
        doc = self.db.get_doc_by_id("composition", composition_id)
        if doc is None:
            return
        else:
            new_item_ref = self.db.get_doc_by_id("composition", referring_comp_id)
            update_ref_path = f"firebase:{new_item_ref.path}" 
            if update_in_array:
                self.db.update_elements_in_array(doc, index, update_ref_path, remove_comp_name)
            else:
                self.db.update_reference_on_doc(doc, index, update_ref_path)
            
    def check_comp_existence(self, composition, collection, name):
        #TODO: we need to get contents in each layer and compare the actual content instead of comparing literal values (recursion)
        comp_obj = composition[name]
        docs = self.db.get_doc_by_name(collection, name)
        if len(docs) == 1:
            doc = docs[0]
            comp_obj["name"] = name
            if doc.to_dict() == comp_obj:
                return doc.id
        elif len(docs) > 1:
            for doc in docs:
                if doc.to_dict() == comp_obj:
                    return doc.id
        return None



    def divide_recipe_into_collections(self, recipe_meta_data, recipe_data):
        recipe_to_save = copy.deepcopy(recipe_meta_data)
        recipe_id = self.get_recipe_id(recipe_data)
        # if the recipe is already exists in db, we dont need to re-upload, just return 
        if self.db.get_doc_by_id("recipes", recipe_id):
            print(f"{recipe_id} is already exists in firestore")
            return
        objects = recipe_data["objects"]
        composition = recipe_data["composition"]
        # TODO: test gradients recipes
        # gradients = recipe_data.get("gradients")
        objects_to_path_map = {}
        comp_to_path_map = {}
        references_to_update = {}
        # save objects to db
        self.upload_objects(objects, objects_to_path_map)
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
                    if len(region_array) > 0:
                        for region_item in region_array:
                            # replace nested objs in comp["regions"]
                            if isinstance(region_item, dict):
                                obj_name = region_item["object"]
                                region_item["object"] = objects_to_path_map.get(obj_name)
                            # replace comps
                            elif isinstance(region_item, str):
                                index = region_array.index(region_item)
                                #TODO-refine check_comp_existence func
                                if self.check_comp_existence(composition, "composition", region_item):
                                    doc_id = self.check_comp_existence(composition, "composition", region_item)
                                    path = self.db.create_path("composition", doc_id)
                                    region_array[index] = path
                                else:
                                    update_field_path = f"regions.{region_name}"
                                    if comp_name in references_to_update:
                                        references_to_update[comp_name].update({region_item:update_field_path})
                                    else:
                                        references_to_update[comp_name] ={region_item:update_field_path}
            comp_obj["name"] = comp_name
            doc_id, comp_path = self.to_db("composition", comp_obj)
            comp_to_path_map[comp_name] = {}
            comp_to_path_map[comp_name]["path"] = comp_path
            comp_to_path_map[comp_name]["id"] = doc_id
            recipe_to_save["composition"][comp_name] = { "inherit" : comp_to_path_map[comp_name]["path"] } 
            if comp_name in references_to_update:
                references_to_update[comp_name].update({"comp_id": doc_id})
        #update nested comp in comp
        if references_to_update:
            for comp_name in references_to_update:
                comp_id = references_to_update[comp_name]["comp_id"]
                for item in references_to_update[comp_name]:
                    if item != "comp_id" and item in comp_to_path_map:
                        item_id = comp_to_path_map[item]["id"]
                        index = references_to_update[comp_name][item]
                        self.update_reference(comp_id, item_id, index, item, update_in_array=True)
        self.upload_recipe(recipe_to_save)
        
        
# def download_recipe(path_to_recipe):
#     firebase_handler = FirebaseHandler()
#     collection, id = firebase_handler.get_collection_id_from_path(path_to_recipe)
#     data_ref = firebase_handler.get_doc_by_id(collection, id)
#     data = data_ref.to_dict()
#     print(data)

# download_recipe("firebase:recipes/peroxisomes_test_v1.0.0")





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

