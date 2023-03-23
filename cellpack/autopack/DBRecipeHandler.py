import copy

from deepdiff import DeepDiff

from cellpack.autopack.utils import deep_merge





class DataDoc(object):
    def __init__(
        self,
    ):
        pass

    def as_dict():
        pass

    def should_write():
        pass

    @staticmethod
    def is_key(string_or_dict):
        return not isinstance(string_or_dict, dict)

class CompositionDoc(DataDoc):
    SHALLOW_MATCH = ["object", "count", "molarity"]
    DEFAULT_VALUES = {"object": None, "count": None, "regions": {}, "molarity": None}

    def __init__(
        self,
        name,
        object_key=None,
        count=None,
        regions=None,
        molarity=None,
        object=None,
    ):
        super().__init__()
        self.name = name
        self.object = object_key or object
        self.count = count
        self.molarity = molarity
        self.regions = regions or {}

    def as_dict(self):
        data = dict()
        data["name"] = self.name
        data["object"] = self.object
        data["count"] = self.count
        data["molarity"] = self.molarity
        data["regions"] = self.regions
        return data

    def get_reference_data(self, key_or_dict, db):
        if DataDoc.is_key(key_or_dict) and db.is_reference(key_or_dict):
            key = key_or_dict
            downloaded_data, _ = db.get_doc_by_ref(key)
            return downloaded_data, None
        else:
            object_dict = key_or_dict
            if "object" in object_dict and db.is_reference(object_dict["object"]):
                key = object_dict["object"]
                downloaded_data, _ = db.get_doc_by_ref(key)
                return downloaded_data, key
            else:
                return {}, None

    def resolve_db_regions(self, db_data, db):
        if "object" in db_data and db_data["object"] is not None:
            downloaded_data, _ = self.get_reference_data(db_data["object"], db)
            db_data["object"] = downloaded_data
        for region_name in db_data["regions"]:
            for index, key_or_dict in enumerate(db_data["regions"][region_name]):
                downloaded_data, key = self.get_reference_data(key_or_dict, db)
                if key:
                    db_data["regions"][region_name][index]["object"] = downloaded_data
                else:
                    db_data["regions"][region_name][index] = downloaded_data

                if (
                    "regions" in downloaded_data
                    and downloaded_data["regions"] is not None
                ):
                    self.resolve_db_regions(downloaded_data, db)

    def resolve_local_regions(self, local_data, recipe_data, db):
        unpack_recipe_data = DBRecipeHandler.prep_data_for_db(recipe_data)
        prep_recipe_data = ObjectDoc.convert_representation(unpack_recipe_data, db)
        if "object" in local_data and local_data["object"] is not None:
            if DataDoc.is_key(local_data["object"]):
                key_name = local_data["object"]
            else:
                key_name = local_data["object"]["name"]
            local_data["object"] = prep_recipe_data["objects"][key_name]
        for region_name in local_data["regions"]:
            for index, key_or_dict in enumerate(local_data["regions"][region_name]):
                if not DataDoc.is_key(key_or_dict):
                    obj_item = local_data["regions"][region_name][index]["object"]
                    if DataDoc.is_key(obj_item):
                        local_data["regions"][region_name][index][
                            "object"
                        ] = prep_recipe_data["objects"][obj_item]
                    else:
                        local_data["regions"][region_name][index][
                            "object"
                        ] = prep_recipe_data["objects"][obj_item["name"]]
                else:
                    comp_name = local_data["regions"][region_name][index]
                    prep_comp_data = prep_recipe_data["composition"][comp_name]
                    prep_comp_data["name"] = comp_name
                    local_data["regions"][region_name][index] = CompositionDoc(
                        **prep_comp_data
                    ).as_dict()
                if (
                    "regions" in local_data["regions"][region_name][index]
                    and local_data["regions"][region_name][index]["regions"] is not None
                ):
                    self.resolve_local_regions(
                        local_data["regions"][region_name][index], recipe_data, db
                    )

    def check_and_replace_references(
        self, objects_to_path_map, references_to_update, db
    ):
        obj_name = self.object
        if obj_name is not None and not db.is_reference(obj_name):
            obj_database_path = objects_to_path_map.get(obj_name)
            self.object = obj_database_path

        if self.regions is not None:
            for region_name, region_array in self.regions.items():
                if len(region_array) > 0:
                    for region_item in region_array:
                        # replace nested objs in comp["regions"]
                        if DataDoc.is_key(region_item):
                            update_field_path = f"regions.{region_name}"
                            if self.name in references_to_update:
                                references_to_update[self.name].update(
                                    {"index": update_field_path, "name": region_item}
                                )
                            else:
                                references_to_update[self.name] = {
                                    "index": update_field_path,
                                    "name": region_item,
                                }

                        elif not db.is_reference(region_item["object"]):
                            obj_name = region_item["object"]
                            region_item["object"] = objects_to_path_map.get(obj_name)

    def should_write(self, db, recipe_data):
        db_docs = db.get_doc_by_name("composition", self.name)
        local_data = {
            "name": self.name,
            "object": self.object,
            "count": self.count,
            "molarity": self.molarity,
            "regions": copy.deepcopy(self.regions),
        }

        if db_docs and len(db_docs) >= 1:
            for doc in db_docs:
                db_data = db.doc_to_dict(doc)
                for item in CompositionDoc.SHALLOW_MATCH:
                    if db_data[item] != local_data[item]:
                        break
                if local_data["regions"] is None and db_data["regions"] is None:
                    # found a match, so shouldn't write
                    return False, db.doc_id(doc)
                else:
                    self.resolve_db_regions(db_data, db)
                    self.resolve_local_regions(local_data, recipe_data, db)
                    difference = DeepDiff(
                        local_data,
                        db_data,
                        ignore_order=True,
                        ignore_type_in_groups=[tuple, list],
                    )
                    if not difference:
                        return False, db.doc_id(doc)
        return True, None


class ObjectDoc(DataDoc):
    def __init__(
            self,
            name,
            settings

        ):
        super().__init__()
        self.name = name
        self.settings = settings

    @staticmethod
    def convert_positions_in_representation(data):
        convert_data = {}
        for key, value in data.items():
            if isinstance(value, list):
                convert_data[key] = tuple(value)
            elif isinstance(value, dict):
                convert_data[key] = ObjectDoc.convert_positions_in_representation(
                    value
                )
            else:
                data[key] = value
        return convert_data

    # get doc from database, convert it back to the original text
    # i.e. in object, convert lists back to tuples in representations/packing/positions
    @staticmethod
    def convert_representation(doc, db):
        if isinstance(doc, object) and db.is_firebase_obj(doc):
            doc = db.doc_to_dict(doc)
        elif isinstance(doc, object) and "__dict__" in dir(doc):
            doc = vars(doc)
        convert_doc = copy.deepcopy(doc)
        for doc_key, doc_value in doc.items():
            if (
                doc_key == "representations"
                and "packing" in doc_value
                and doc_value["packing"] is not None
            ):
                position_value = doc_value["packing"]["positions"]
                convert_doc["representations"]["packing"][
                    "positions"
                ] = ObjectDoc.convert_positions_in_representation(position_value)
        return convert_doc

    def as_dict(self):
        data = dict()
        data["name"] = self.name
        for key in self.settings:
            data[key] = self.settings[key]
        return data

    def should_write(self, db):
        docs = db.get_doc_by_name("objects", self.name)
        if docs and len(docs) >= 1:
            for doc in docs:
                full_doc_data = ObjectDoc.convert_representation(
                    doc, db
                )  # if there is repr in obj
                local_data = DBRecipeHandler.prep_data_for_db(self.as_dict())
                difference = DeepDiff(full_doc_data, local_data, ignore_order=True)
                if not difference:
                    return doc, db.doc_id(doc)
        return None, None


class DBRecipeHandler(object):
    def __init__(self, db_handler):
        self.db = db_handler
        self.objects_to_path_map = {}
        self.comp_to_path_map = {}

    @staticmethod
    def is_nested_list(item):
        return (
            isinstance(item, list)
            and len(item) > 0
            and isinstance(item[0], (list, tuple))
        )

    @staticmethod
    def prep_data_for_db(data):
        modified_data = {}
        for key, value in data.items():
            # convert 2d array to dict
            if DBRecipeHandler.is_nested_list(value):
                flatten_dict = dict(zip([str(i) for i in range(len(value))], value))
                modified_data[key] = DBRecipeHandler.prep_data_for_db(flatten_dict)
            # If the value is an object, we want to convert it to dict
            elif isinstance(value, object) and "__dict__" in dir(value):
                unpacked_value = vars(value)
                modified_data[key] = unpacked_value
                if isinstance(unpacked_value, dict):
                    modified_data[key] = DBRecipeHandler.prep_data_for_db(
                        unpacked_value
                    )
            # If the value is a dictionary, recursively convert its nested lists to dictionaries
            elif isinstance(value, dict):
                modified_data[key] = DBRecipeHandler.prep_data_for_db(value)
            else:
                modified_data[key] = value
        return modified_data

    # add documents with auto IDs
    def upload_data(self, collection, data, id=None):
        # check if we need to convert part of the data(2d arrays and objs to dict)
        modified_data = DBRecipeHandler.prep_data_for_db(data)
        if id is None:
            name = modified_data["name"]
            doc = self.db.upload_doc(collection, modified_data)
            # doc is a tuple, e.g (DatetimeWithNanoseconds, data_obj)
            doc_path = doc[1].path
            doc_id = self.db.doc_id(doc[1])
            print(f"successfully uploaded {name} to path: {doc_path}")
            return doc_id, self.db.create_path(collection, doc_id)
        else:
            doc_path = f"{collection}/{id}"
            doc = self.db.set_doc(collection, id, modified_data)
            return id, self.db.create_path(collection, id)

    def upload_objects(self, objects):
        for obj_name in objects:
            objects[obj_name]["name"] = obj_name
            object_doc = ObjectDoc(name=obj_name, settings=objects[obj_name])            
            _, doc_id = object_doc.should_write(self.db)
            if doc_id:
                print(f"objects/{object_doc.name} is already exists in firestore")
            else:
                _, obj_path = self.upload_data("objects", object_doc.as_dict())
                self.objects_to_path_map[obj_name] = obj_path

    def upload_compositions(self, compositions, recipe_to_save, recipe_data):
        references_to_update = {}
        for comp_name in compositions:
            comp_obj = compositions[comp_name]
            self.comp_to_path_map[comp_name] = {}
            comp_obj["name"] = comp_name
            comp_data = deep_merge(
                copy.deepcopy(CompositionDoc.DEFAULT_VALUES), comp_obj
            )
            comp_doc = CompositionDoc(
                comp_name,
                object_key=comp_data["object"],
                count=comp_data["count"],
                regions=comp_data["regions"],
                molarity=comp_data["molarity"],
            )
            # if comp exists, don't upload
            _, doc_id = comp_doc.should_write(self.db, recipe_data)
            if doc_id:
                path = self.db.create_path("composition", doc_id)
                self.comp_to_path_map[comp_name]["path"] = path
                self.comp_to_path_map[comp_name]["id"] = doc_id
                print(f"composition/{comp_name} is already exists in firestore")
            else:
                # replace with paths for outer objs in comp, then upload
                comp_doc.check_and_replace_references(
                    self.objects_to_path_map, references_to_update, self.db
                )
                comp_ready_for_db = comp_doc.as_dict()
                doc_id, comp_path = self.upload_data("composition", comp_ready_for_db)
                self.comp_to_path_map[comp_name]["path"] = comp_path
                self.comp_to_path_map[comp_name]["id"] = doc_id

            recipe_to_save["composition"][comp_name] = {
                "inherit": self.comp_to_path_map[comp_name]["path"]
            }

            recipe_to_save["composition"][comp_name] = {
                "inherit": self.comp_to_path_map[comp_name]["path"]
            }
            if comp_name in references_to_update:
                references_to_update[comp_name].update({"comp_id": doc_id})
        return references_to_update

    def get_recipe_id(self, recipe_data):
        recipe_name = recipe_data["name"]
        recipe_version = recipe_data["version"]
        key = f"{recipe_name}_v{recipe_version}"
        return key

    def update_reference(
        self,
        composition_id,
        referring_comp_id,
        index,
        remove_comp_name,
        update_in_array=False,
    ):
        doc, doc_ref = self.db.get_doc_by_id("composition", composition_id)
        if doc is None:
            return
        else:
            _, new_item_ref = self.db.get_doc_by_id("composition", referring_comp_id)
            update_ref_path = f"{self.db.name}:{new_item_ref.path}"
            if update_in_array:
                self.db.update_elements_in_array(
                    doc_ref, index, update_ref_path, remove_comp_name
                )
            else:
                self.db.update_reference_on_doc(doc_ref, index, update_ref_path)

    def upload_collections(self, recipe_meta_data, recipe_data):
        recipe_to_save = copy.deepcopy(recipe_meta_data)
        objects = recipe_data["objects"]
        compositions = recipe_data["composition"]
        # TODO: test gradients recipes
        # gradients = recipe_data.get("gradients")
        # save objects to db
        self.upload_objects(objects)
        # save comps to db
        references_to_update = self.upload_compositions(
            compositions, recipe_to_save, recipe_data
        )
        # update nested comp in comp
        if references_to_update:
            for comp_name in references_to_update:
                inner_data = references_to_update[comp_name]
                comp_id = inner_data["comp_id"]
                index = inner_data["index"]
                name = inner_data["name"]

                item_id = self.comp_to_path_map[name]["id"]
                self.update_reference(
                    comp_id, item_id, index, name, update_in_array=True
                )
        return recipe_to_save

    def upload_recipe(self, recipe_meta_data, recipe_data):
        recipe_id = self.get_recipe_id(recipe_data)
        # if the recipe is already exists in db, just return
        recipe, _ = self.db.get_doc_by_id("recipes", recipe_id)
        if recipe:
            print(f"{recipe_id} is already in firestore")
            return
        recipe_to_save = self.upload_collections(recipe_meta_data, recipe_data)
        key = self.get_recipe_id(recipe_to_save)
        self.upload_data("recipes", recipe_to_save, key)
