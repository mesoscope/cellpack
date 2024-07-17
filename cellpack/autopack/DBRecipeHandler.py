import copy
from datetime import datetime, timezone
from enum import Enum

from deepdiff import DeepDiff
import requests

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

    @staticmethod
    def is_nested_list(item):
        if not isinstance(item, list):
            return False
        for element in item:
            if isinstance(element, (list, tuple)):
                return True
        return False

    @staticmethod
    def is_db_dict(item):
        if isinstance(item, dict) and len(item) > 0:
            for key, value in item.items():
                if key.isdigit() and isinstance(value, list):
                    return True
        return False

    @staticmethod
    def is_obj(comp_or_obj):
        # in resolved DB data, if the top level of a downloaded comp doesn't have the key `name`, it's an obj
        # TODO: true for all cases? better approaches?
        return not comp_or_obj.get("name") and "object" in comp_or_obj


class CompositionDoc(DataDoc):
    """
    Declares required attributes for comps in the constructor, set default values.
    Handles the logic for comparing the local and db data to determine the uploading process.
    """

    SHALLOW_MATCH = ["object", "count", "molarity"]
    DEFAULT_VALUES = {"object": None, "count": None, "regions": {}, "molarity": None}
    KEY_TO_DICT_MAPPING = {"gradient": "gradients", "inherit": "objects"}

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

    @staticmethod
    def get_reference_in_obj(downloaded_data, db):
        for key in CompositionDoc.KEY_TO_DICT_MAPPING:
            if key in downloaded_data:
                # single gradient and inherited object
                if db.is_reference(downloaded_data[key]):
                    downloaded_data[key], _ = db.get_doc_by_ref(downloaded_data[key])
                # combined gradients
                elif isinstance(downloaded_data[key], list):
                    for gradient in downloaded_data[key]:
                        for gradient_name, path in gradient.items():
                            gradient[gradient_name], _ = db.get_doc_by_ref(path)

    @staticmethod
    def get_reference_data(key_or_dict, db):
        """
        Returns the db data for a reference, and the key if it exists.
        Key --> the name of a composition
        Dict --> the object data
        """
        if DataDoc.is_key(key_or_dict) and db.is_reference(key_or_dict):
            key = key_or_dict
            downloaded_data, _ = db.get_doc_by_ref(key)
            CompositionDoc.get_reference_in_obj(downloaded_data, db)
            return downloaded_data, None
        elif key_or_dict and isinstance(key_or_dict, dict):
            object_dict = key_or_dict
            if "object" in object_dict and db.is_reference(object_dict["object"]):
                key = object_dict["object"]
                downloaded_data, _ = db.get_doc_by_ref(key)
                CompositionDoc.get_reference_in_obj(downloaded_data, db)
                return downloaded_data, key
        return {}, None

    def resolve_db_regions(self, db_data, db):
        """
        Recursively resolves the regions of a composition from db.
        """
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

    @staticmethod
    def gradient_list_to_dict(prep_recipe_data):
        """
        Convert gradient list to dict for resolve_local_regions
        """
        if "gradients" in prep_recipe_data and isinstance(
            prep_recipe_data["gradients"], list
        ):
            gradient_dict = {}
            for gradient in prep_recipe_data["gradients"]:
                gradient_dict[gradient["name"]] = gradient
            prep_recipe_data["gradients"] = gradient_dict

    @staticmethod
    def create_combined_gradient_list(key, obj_data, prep_data):
        """
        When the gradients are combined, fetch and replace gradient data in a list.
        key --> the key in the object data that we want to modify its value
        obj_data --> the object data that contains the gradient list
        prep_data --> the data that contains the gradients (raw data or path) we want to fetch
        """
        new_grad_list = []
        for grad in obj_data[key]:
            new_grad_list.append({grad: prep_data[grad]})
        obj_data[key] = new_grad_list

    def resolve_object_data(self, object_data, prep_recipe_data):
        """
        Resolve the object data from the local data.
        """
        for key in CompositionDoc.KEY_TO_DICT_MAPPING:
            if key in object_data:
                # single gradient and inherited object
                if isinstance(object_data[key], str):
                    target_dict = CompositionDoc.KEY_TO_DICT_MAPPING[key]
                    object_data[key] = prep_recipe_data[target_dict][object_data[key]]
                # combined gradients
                elif isinstance(object_data[key], list):
                    self.create_combined_gradient_list(
                        key, object_data, prep_recipe_data["gradients"]
                    )

    def resolve_local_regions(self, local_data, recipe_data, db):
        """
        Recursively resolves the regions of a composition from local data.
        Restructure the local data to match the db data.
        """
        unpack_recipe_data = DBUploader.prep_data_for_db(recipe_data)
        prep_recipe_data = ObjectDoc.convert_representation(unpack_recipe_data, db)
        # `gradients` is a list, convert it to dict for easy access and replace
        CompositionDoc.gradient_list_to_dict(prep_recipe_data)
        if "object" in local_data and local_data["object"] is not None:
            if DataDoc.is_key(local_data["object"]):
                key_name = local_data["object"]
            else:
                key_name = local_data["object"]["name"]
            local_data["object"] = prep_recipe_data["objects"][key_name]
            self.resolve_object_data(local_data["object"], prep_recipe_data)
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
                    # replace reference in obj with actual data
                    obj_data = local_data["regions"][region_name][index]["object"]
                    self.resolve_object_data(obj_data, prep_recipe_data)
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
        """
        Within one recipe upload, we store the references for uploaded comps and objs.
        Checks if the object or comp is a reference in the nesting regions, and replaces it with the referenced db path.
        """
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

    @staticmethod
    def update_reference(
        db,
        composition_id,
        referring_comp_id,
        index,
        remove_comp_name,
        update_in_array=False,
    ):
        """
        Update comp references in the recipe
        """
        doc, doc_ref = db.get_doc_by_id("composition", composition_id)
        if doc is None:
            return
        _, new_item_ref = db.get_doc_by_id("composition", referring_comp_id)
        update_ref_path = f"{db.db_name()}:{db.get_path_from_ref(new_item_ref)}"
        if update_in_array:
            db.update_elements_in_array(
                doc_ref, index, update_ref_path, remove_comp_name
            )
        else:
            db.update_reference_on_doc(doc_ref, index, update_ref_path)

    def should_write(self, db, recipe_data):
        """
        Compares the resolved local composition to the resolved db composition.
        To determine whether the composition data already exists or if it needs to be written to the database.
        """
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
                    # deeply compare resolved regions data
                    self.resolve_db_regions(db_data, db)
                    self.resolve_local_regions(local_data, recipe_data, db)
                    difference = DeepDiff(
                        local_data,
                        db_data,
                        ignore_order=True,
                        ignore_type_in_groups=[tuple, list],
                    )
                    if not difference:
                        return doc, db.doc_id(doc)
        return None, None


class ObjectDoc(DataDoc):
    def __init__(self, name, settings):
        super().__init__()
        self.name = name
        self.settings = settings

    def as_dict(self):
        data = dict()
        data["name"] = self.name
        for key in self.settings:
            data[key] = self.settings[key]
        return data

    @staticmethod
    def convert_positions_in_representation(data):
        convert_data = {}
        for key, value in data.items():
            if isinstance(value, list):
                convert_data[key] = tuple(value)
            elif isinstance(value, dict):
                convert_data[key] = ObjectDoc.convert_positions_in_representation(value)
            else:
                data[key] = value
        return convert_data

    @staticmethod
    def convert_representation(doc, db):
        """
        Get object doc from database, convert it back to the original text
        i.e. in object, convert lists back to tuples in representations/packing/positions
        """
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

    @staticmethod
    def _object_contains_grad_or_inherit(obj_data):
        return (
            "gradient" in obj_data and isinstance(obj_data["gradient"], dict)
        ) or "inherit" in obj_data

    def should_write(self, db):
        docs = db.get_doc_by_name("objects", self.name)
        if docs and len(docs) >= 1:
            for doc in docs:
                # if there is repr in the obj doc from db
                full_doc_data = ObjectDoc.convert_representation(doc, db)
                # unpack objects to dicts in local data for comparison
                local_data = DBUploader.prep_data_for_db(self.as_dict())
                difference = DeepDiff(full_doc_data, local_data, ignore_order=True)
                if not difference:
                    return doc, db.doc_id(doc)
        return None, None


class GradientDoc(DataDoc):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def should_write(self, db, grad_name):
        docs = db.get_doc_by_name("gradients", grad_name)
        if docs and len(docs) >= 1:
            for doc in docs:
                local_data = DBUploader.prep_data_for_db(db.doc_to_dict(doc))
                db_data = db.doc_to_dict(doc)
                difference = DeepDiff(db_data, local_data, ignore_order=True)
                if not difference:
                    return doc, db.doc_id(doc)
        return None, None


class ResultDoc:
    def __init__(self, db):
        self.db = db

    def handle_expired_results(self):
        """
        Check if the results in the database are expired and delete them if the linked object expired.
        """
        current_utc = datetime.now(timezone.utc)
        results = self.db.get_all_docs("results")
        if results:
            for result in results:
                result_data = self.db.doc_to_dict(result)
                result_age = current_utc - result_data["timestamp"]
                if result_age.days > 180 and not self.validate_existence(
                    result_data["url"]
                ):
                    self.db.delete_doc("results", self.db.doc_id(result))
            print("Results cleanup complete.")
        else:
            print("No results found in the database.")

    def validate_existence(self, url):
        """
        Validate the existence of an S3 object by checking if the URL is accessible.
        Returns True if the URL is accessible.
        """
        return requests.head(url).status_code == requests.codes.ok


class DBUploader(object):
    """
    Handles the uploading of data to the database.
    """

    def __init__(self, db_handler):
        self.db = db_handler
        self.objects_to_path_map = {}
        self.comp_to_path_map = {}
        self.grad_to_path_map = {}
        self.objects_with_inherit_key = []

    @staticmethod
    def prep_data_for_db(data):
        """
        Recursively convert data to a format that can be written to the database.
        """
        modified_data = {}
        for key, value in data.items():
            # convert 2d array to dict
            if DataDoc.is_nested_list(value):
                flatten_dict = dict(zip([str(i) for i in range(len(value))], value))
                modified_data[key] = DBUploader.prep_data_for_db(flatten_dict)
            # If the value is an object, we want to convert it to dict
            elif isinstance(value, object) and "__dict__" in dir(value):
                unpacked_value = vars(value)
                modified_data[key] = unpacked_value
                if isinstance(unpacked_value, dict):
                    modified_data[key] = DBUploader.prep_data_for_db(unpacked_value)
            # If the value is an enum, convert it to a string. e.g. during a version migration process where "type" in a v1 recipe is an enum
            elif isinstance(value, Enum):
                modified_data[key] = value.name
            # If the value is a dictionary, recursively convert its nested lists to dictionaries
            elif isinstance(value, dict):
                modified_data[key] = DBUploader.prep_data_for_db(value)
            else:
                modified_data[key] = value
        return modified_data

    def upload_data(self, collection, data, id=None):
        """
        If should_write is true, upload the data to the database
        """
        # check if we need to convert part of the data(2d arrays and objs to dict)
        modified_data = DBUploader.prep_data_for_db(data)
        if id is None:
            name = modified_data["name"]
            doc = self.db.upload_doc(collection, modified_data)
            # doc is a tuple, e.g (DatetimeWithNanoseconds, data_obj)
            doc_path = self.db.get_path_from_ref(doc[1])
            doc_id = self.db.doc_id(doc[1])
            print(f"successfully uploaded {name} to path: {doc_path}")
            return doc_id, self.db.create_path(collection, doc_id)
        else:
            doc_path = f"{collection}/{id}"
            doc = self.db.set_doc(collection, id, modified_data)
            return id, self.db.create_path(collection, id)

    def upload_gradients(self, gradients):
        for gradient in gradients:
            gradient_name = gradient["name"]
            gradient_doc = GradientDoc(settings=gradient)
            _, doc_id = gradient_doc.should_write(self.db, gradient_name)
            if doc_id:
                print(f"gradients/{gradient_name} is already in firestore")
                self.grad_to_path_map[gradient_name] = self.db.create_path(
                    "gradients", doc_id
                )
            else:
                _, grad_path = self.upload_data("gradients", gradient_doc.settings)
                self.grad_to_path_map[gradient_name] = grad_path

    def upload_single_object(self, obj_name, obj_data):
        # replace gradient name with path to check if gradient exists in db
        if "gradient" in obj_data[obj_name]:
            # single gradient
            if isinstance(obj_data[obj_name]["gradient"], str):
                grad_name = obj_data[obj_name]["gradient"]
                obj_data[obj_name]["gradient"] = self.grad_to_path_map[grad_name]
            # combined gradients
            elif isinstance(obj_data[obj_name]["gradient"], list):
                CompositionDoc.create_combined_gradient_list(
                    "gradient", obj_data[obj_name], self.grad_to_path_map
                )
        object_doc = ObjectDoc(name=obj_name, settings=obj_data[obj_name])
        _, doc_id = object_doc.should_write(self.db)
        if doc_id:
            print(f"objects/{object_doc.name} is already in firestore")
            obj_path = self.db.create_path("objects", doc_id)
            self.objects_to_path_map[obj_name] = obj_path
        else:
            _, obj_path = self.upload_data("objects", object_doc.as_dict())
            self.objects_to_path_map[obj_name] = obj_path

    def upload_objects(self, objects):
        # modify a copy of objects to avoid key error when resolving local regions
        modify_objects = copy.deepcopy(objects)
        for obj_name in objects:
            objects[obj_name]["name"] = obj_name
            if "inherit" not in objects[obj_name]:
                self.upload_single_object(obj_name, modify_objects)
            else:
                self.objects_with_inherit_key.append(obj_name)

        # upload objs having `inherit` key only after all their base objs are uploaded
        for obj_name in self.objects_with_inherit_key:
            inherited_from = objects[obj_name]["inherit"]
            modify_objects[obj_name]["inherit"] = self.objects_to_path_map[
                inherited_from
            ]
            self.upload_single_object(obj_name, modify_objects)

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
                print(f"composition/{comp_name} is already in firestore")
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

    def _get_recipe_id(self, recipe_data):
        """
        We use customized recipe id to declare recipe's name and version
        """
        recipe_name = recipe_data["name"]
        recipe_version = recipe_data["version"]
        key = f"{recipe_name}_v_{recipe_version}"
        return key

    def upload_collections(self, recipe_meta_data, recipe_data):
        """
        Separate collections from recipe data and upload them to db
        """
        recipe_to_save = copy.deepcopy(recipe_meta_data)
        gradients = recipe_data.get("gradients")
        objects = recipe_data["objects"]
        compositions = recipe_data["composition"]
        # save gradients to db
        if gradients:
            self.upload_gradients(gradients)
        # save objects to db
        self.upload_objects(objects)
        # save comps to db
        references_to_update = self.upload_compositions(
            compositions, recipe_to_save, recipe_data
        )
        # update nested comp in composition
        if references_to_update:
            for comp_name in references_to_update:
                inner_data = references_to_update[comp_name]
                comp_id = inner_data["comp_id"]
                index = inner_data["index"]
                name = inner_data["name"]

                item_id = self.comp_to_path_map[name]["id"]
                CompositionDoc.update_reference(
                    self.db, comp_id, item_id, index, name, update_in_array=True
                )
        return recipe_to_save

    def upload_recipe(self, recipe_meta_data, recipe_data):
        """
        After all other collections are checked or uploaded, upload the recipe with references into db
        """
        recipe_id = self._get_recipe_id(recipe_data)
        # if the recipe is already exists in db, just return
        recipe, _ = self.db.get_doc_by_id("recipes", recipe_id)
        if recipe:
            print(f"{recipe_id} is already in firestore")
            return
        recipe_to_save = self.upload_collections(recipe_meta_data, recipe_data)
        recipe_to_save["recipe_path"] = self.db.create_path("recipes", recipe_id)
        self.upload_data("recipes", recipe_to_save, recipe_id)

    def upload_result_metadata(self, file_name, url):
        """
        Upload the metadata of the result file to the database.
        """
        if self.db:
            username = self.db.get_username()
            timestamp = self.db.create_timestamp()
            self.db.update_or_create(
                "results",
                file_name,
                {"user": username, "timestamp": timestamp, "url": url},
            )


class DBRecipeLoader(object):
    """
    Handles the logic for downloading and parsing the recipe data from the database.
    """

    def __init__(self, db_handler):
        self.db = db_handler

    def prep_db_doc_for_download(self, db_doc):
        """
        convert data from db and resolve references.
        """
        prep_data = {}
        if isinstance(db_doc, dict):
            for key, value in db_doc.items():
                if DataDoc.is_db_dict(value):
                    unpack_dict = [value[str(i)] for i in range(len(value))]
                    prep_data[key] = unpack_dict
                elif key == "composition":
                    compositions = db_doc["composition"]
                    for comp_name, reference in compositions.items():
                        ref_link = reference["inherit"]
                        comp_doc = CompositionDoc(
                            comp_name,
                            object_key=None,
                            count=None,
                            regions={},
                            molarity=None,
                        )
                        composition_data, _ = comp_doc.get_reference_data(
                            ref_link, self.db
                        )
                        comp_doc.resolve_db_regions(composition_data, self.db)
                        compositions[comp_name] = composition_data
                    prep_data[key] = compositions
                else:
                    prep_data[key] = value
        return prep_data

    def collect_docs_by_id(self, collection, id):
        return self.db.get_doc_by_id(collection, id)

    def validate_input_recipe_path(self, path):
        """
        Validates if the input path corresponds to a recipe path in the database.
        Format of a recipe path: firebase:recipes/[RECIPE-ID]
        """
        collection, id = self.db.get_collection_id_from_path(path)
        recipe_path = self.db.get_value(collection, id, "recipe_path")
        if not recipe_path:
            raise ValueError(
                f"No recipe found at the input path: '{path}'. Please ensure the recipe exists in the database and is spelled correctly. Expected path format: 'firebase:recipes/[RECIPE-ID]'"
            )

    @staticmethod
    def _get_grad_and_obj(obj_data, obj_dict, grad_dict):
        """
        Collect gradient and inherited object data from the downloaded object data
        return object data dict and gradient data dict with name as key
        """
        obj_name = obj_data["name"]
        for key, target_dict in CompositionDoc.KEY_TO_DICT_MAPPING.items():
            if key in obj_data:
                # single gradient and inherited object
                if isinstance(obj_data[key], dict):
                    item_name = obj_data[key]["name"]
                    target_dict = grad_dict if key == "gradient" else obj_dict
                    target_dict[item_name] = obj_data[key]
                    obj_dict[obj_name][key] = item_name
                # combined gradients
                elif key == "gradient" and isinstance(obj_data[key], list):
                    new_grad_list = []
                    for grad in obj_data[key]:
                        for name in grad:
                            grad_dict[name] = grad[name]
                            new_grad_list.append(name)
                    obj_dict[obj_name][key] = new_grad_list
        return obj_dict, grad_dict

    @staticmethod
    def collect_and_sort_data(comp_data):
        """
        Collect all object and gradient info from the downloaded composition data
        Return autopack object data dict and gradient data dict with name as key
        Return restructured composition dict with "composition" as key
        """
        objects = {}
        gradients = {}
        composition = {}
        for comp_name, comp_value in comp_data.items():
            composition[comp_name] = {}
            if "count" in comp_value and comp_value["count"] is not None:
                composition[comp_name]["count"] = comp_value["count"]
            if "object" in comp_value and comp_value["object"] is not None:
                composition[comp_name]["object"] = comp_value["object"]["name"]
                object_copy = copy.deepcopy(comp_value["object"])
                objects[object_copy["name"]] = object_copy
                if ObjectDoc._object_contains_grad_or_inherit(object_copy):
                    objects, gradients = DBRecipeLoader._get_grad_and_obj(
                        object_copy, objects, gradients
                    )
            if "regions" in comp_value and comp_value["regions"] is not None:
                for region_name in comp_value["regions"]:
                    composition[comp_name].setdefault("regions", {})[region_name] = []
                    for region_item in comp_value["regions"][region_name]:
                        if DataDoc.is_obj(region_item):
                            composition[comp_name]["regions"][region_name].append(
                                {
                                    "object": region_item["object"].get("name"),
                                    "count": region_item.get("count"),
                                }
                            )
                            object_copy = copy.deepcopy(region_item["object"])
                            objects[object_copy["name"]] = object_copy
                            if ObjectDoc._object_contains_grad_or_inherit(object_copy):
                                objects, gradients = DBRecipeLoader._get_grad_and_obj(
                                    object_copy, objects, gradients
                                )
                        else:
                            composition[comp_name]["regions"][region_name].append(
                                region_item["name"]
                            )
        return objects, gradients, composition

    @staticmethod
    def compile_db_recipe_data(db_recipe_data, obj_dict, grad_dict, comp_dict):
        """
        Compile recipe data from db recipe data into a ready-to-pack structure
        """
        recipe_data = {
            **{
                k: db_recipe_data[k]
                for k in ["format_version", "version", "name", "bounding_box"]
            },
            "objects": obj_dict,
            "composition": comp_dict,
        }
        if grad_dict:
            recipe_data["gradients"] = [{**v} for v in grad_dict.values()]
        return recipe_data


class DBMaintenance(object):
    """
    Handles the maintenance of the database.
    """

    def __init__(self, db_handler):
        self.db = db_handler
        self.result_doc = ResultDoc(self.db)

    def cleanup_results(self):
        """
        Check if the results in the database are expired and delete them if the linked object expired.
        """
        self.result_doc.handle_expired_results()

    def readme_url(self):
        """
        Return the URL to the README file for the database setup section.
        """
        return "https://github.com/mesoscope/cellpack?tab=readme-ov-file#introduction-to-remote-databases"
