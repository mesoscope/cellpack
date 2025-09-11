import copy
import logging
import shutil
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS


import hashlib
import json
import requests

from cellpack.autopack.utils import deep_merge


class DataDoc(object):
    def __init__(
        self,
    ):
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
        return not comp_or_obj.get("name") and "object" in comp_or_obj

    @staticmethod
    def generate_hash(doc_data):
        doc_str = json.dumps(doc_data, sort_keys=True)
        return hashlib.sha256(doc_str.encode()).hexdigest()


class CompositionDoc(DataDoc):
    """
    Declares required attributes for comps in the constructor, set default values.
    """

    DEFAULT_VALUES = {
        "object": None,
        "count": None,
        "regions": {},
        "molarity": None,
        "priority": None,
    }
    KEY_TO_DICT_MAPPING = {"gradient": "gradients", "inherit": "objects"}

    def __init__(
        self,
        name,
        object_key=None,
        count=None,
        regions=None,
        molarity=None,
        priority=None,
        object=None,
    ):
        super().__init__()
        self.name = name
        self.object = object_key or object
        self.count = count
        self.molarity = molarity
        self.priority = priority
        self.regions = regions or {}

    def as_dict(self):
        data = dict()
        data["name"] = self.name
        data["object"] = self.object
        data["count"] = self.count
        data["molarity"] = self.molarity
        data["priority"] = self.priority
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
    def resolve_combined_gradient(key, obj_data, prep_data):
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
                    self.resolve_combined_gradient(
                        key, object_data, prep_recipe_data["gradients"]
                    )

    @staticmethod
    def build_dependency_graph(compositions):
        """
        Creates a dependency map showing the relationships between compositions.
        """
        dependency_map = {}
        for key in compositions:
            if key not in dependency_map:
                dependency_map[key] = []

            comp = compositions[key]
            if isinstance(comp, dict) and "regions" in comp:
                for _, region_items in comp["regions"].items():
                    if isinstance(region_items, list):
                        for item in region_items:
                            if isinstance(item, str) and item in compositions:
                                dependency_map[key].append(item)
        return dependency_map

    def comp_upload_order(self, compositions):
        """
        Use topological sort to determine the order in which compositions should be uploaded.
        Returns a list of composition keys in the order they should be uploaded.
        """
        dependency_map = CompositionDoc.build_dependency_graph(compositions)

        in_degree = {node: 0 for node in compositions}

        # calculate in-degree for each node (how many compositions contain this one)
        for container, dependencies in dependency_map.items():
            for dependency in dependencies:
                in_degree[dependency] = in_degree.get(dependency, 0) + 1

        # start with nodes that are not contained by any other comp
        roots = [node for node in in_degree if in_degree[node] == 0]

        queue = roots.copy()
        upload_order = []

        while queue:
            current = queue.pop(0)  # process the first node in the queue
            upload_order.append(current)

            for dependency in dependency_map.get(current, []):
                in_degree[dependency] -= 1
                if in_degree[dependency] == 0:
                    queue.append(dependency)

        # check for cycles in the graph
        if len(upload_order) != len(in_degree):
            raise ValueError("Circular dependency detected in compositions.")

        # reverse the order since we need inner nodes first
        upload_order.reverse()
        return upload_order

    @staticmethod
    def replace_region_references(uploader, composition_data):
        """
        Replaces composition references with paths in the database.
        """
        if "object" in composition_data and DataDoc.is_key(composition_data["object"]):
            composition_data["object"] = uploader.objects_to_path_map.get(
                composition_data["object"]
            )

        if "regions" in composition_data and composition_data["regions"]:
            for region_name in composition_data["regions"]:
                if not composition_data["regions"][region_name]:
                    continue
                for index, item in enumerate(composition_data["regions"][region_name]):
                    if isinstance(item, str):
                        composition_data["regions"][region_name][index] = (
                            uploader.comp_to_path_map.get(item)
                        )
                    elif isinstance(item, dict):
                        # process nested regions recursively
                        CompositionDoc.replace_region_references(uploader, item)
        return composition_data


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
                convert_doc["representations"]["packing"]["positions"] = (
                    ObjectDoc.convert_positions_in_representation(position_value)
                )
        return convert_doc

    @staticmethod
    def _object_contains_grad_or_inherit(obj_data):
        return (
            "gradient" in obj_data and isinstance(obj_data["gradient"], dict)
        ) or "inherit" in obj_data


class GradientDoc(DataDoc):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings


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
            logging.info("Results cleanup complete.")
        else:
            logging.info("No results found in the database.")

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
        modified_data = DBUploader.prep_data_for_db(data)
        modified_data["dedup_hash"] = DataDoc.generate_hash(modified_data)

        # customized id for recipe
        if id:
            self.db.set_doc(collection, id, modified_data)
            doc_path = self.db.create_path(collection, id)
            return id, doc_path
        doc_ref = self.db.check_doc_existence(collection, modified_data)
        # if the doc already exists, return the path
        if doc_ref:
            doc_id = self.db.doc_id(doc_ref)
            doc_path = self.db.create_path(collection, doc_id)
            return doc_id, doc_path
        # if the doc doesn't exist, upload it
        doc_ref = self.db.upload_doc(collection, modified_data)
        doc_id = self.db.doc_id(doc_ref[1])
        doc_path = self.db.create_path(collection, doc_id)
        logging.info(f"successfully uploaded {doc_id} to path: {doc_path}")
        return doc_id, doc_path

    def upload_gradients(self, gradients):
        for gradient in gradients:
            gradient_name = gradient["name"]
            gradient_doc = GradientDoc(settings=gradient)
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
                CompositionDoc.resolve_combined_gradient(
                    "gradient", obj_data[obj_name], self.grad_to_path_map
                )
        object_doc = ObjectDoc(name=obj_name, settings=obj_data[obj_name])
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

    def upload_compositions(self, compositions, recipe_to_save):
        comp_order = CompositionDoc.comp_upload_order(self, compositions)

        for comp_name in comp_order:
            comp = copy.deepcopy(compositions[comp_name])
            comp["name"] = comp_name

            # apply default values
            comp_data = deep_merge(copy.deepcopy(CompositionDoc.DEFAULT_VALUES), comp)
            # replace composition references with ids
            comp_data = CompositionDoc.replace_region_references(self, comp_data)
            comp_doc = CompositionDoc(
                comp_name,
                object_key=comp_data["object"],
                count=comp_data["count"],
                regions=comp_data["regions"],
                molarity=comp_data["molarity"],
                priority=comp_data["priority"],
            )

            comp_ready_for_db = comp_doc.as_dict()
            _, comp_path = self.upload_data("composition", comp_ready_for_db)

            self.comp_to_path_map[comp_name] = comp_path

            # update the recipe reference
            recipe_to_save["composition"][comp_name] = {"inherit": comp_path}

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
        self.upload_compositions(compositions, recipe_to_save)
        return recipe_to_save

    def upload_recipe(self, recipe_meta_data, recipe_data):
        """
        After all other collections are checked or uploaded, upload the recipe with references into db
        """
        recipe_id = self._get_recipe_id(recipe_data)
        recipe_to_save = self.upload_collections(recipe_meta_data, recipe_data)
        recipe_to_save["recipe_path"] = self.db.create_path("recipes", recipe_id)
        self.upload_data("recipes", recipe_to_save, recipe_id)

    def upload_config(self, config_data, source_path):
        """
        Upload the config data to the database.
        """
        config_data["source_path"] = source_path
        id, doc_path = self.upload_data("configs", config_data)
        print(f"Config uploaded to {doc_path}")
        # update the config data with the firebase doc path
        config_data["config_path"] = doc_path
        self.db.update_doc("configs", id, config_data)
        return

    def upload_result_metadata(self, file_name, url, job_id=None):
        """
        Upload the metadata of the result file to the database.
        """
        if self.db:
            username = self.db.get_username()
            timestamp = self.db.create_timestamp()
            self.db.update_or_create(
                "results",
                file_name,
                {
                    "user": username,
                    "timestamp": timestamp,
                    "url": url,
                    "batch_job_id": job_id,
                },
            )
        if job_id:
            self.upload_job_status(job_id, "DONE", result_path=url)

    def upload_job_status(self, job_id, status, result_path=None, error_message=None):
        """
        Update status for a given job ID
        """
        if self.db:
            timestamp = self.db.create_timestamp()
            self.db.update_or_create(
                "job_status",
                job_id,
                {
                    "timestamp": timestamp,
                    "status": str(status),
                    "result_path": result_path,
                    "error_message": error_message,
                },
            )

    def upload_packing_results_workflow(self, source_folder, recipe_name, job_id):
        """
        Complete packing results upload workflow including folder preparation and s3 upload
        """
        try:
            if job_id:

                source_path = Path(source_folder)
                if not source_path.exists():
                    error_msg = f"Source folder does not exist: {source_folder}"
                    logging.error(error_msg)
                    return {"success": False, "error": error_msg}

                # prepare unique S3 upload folder
                parent_folder = source_path.parent
                unique_folder_name = f"{source_path.name}_run_{job_id}"
                s3_upload_folder = parent_folder / unique_folder_name

                logging.debug(f"outputs will be copied to: {s3_upload_folder}")

                # copy outputs to unique upload folder
                s3_upload_folder.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source_folder, s3_upload_folder, dirs_exist_ok=True)

                upload_result = self.upload_outputs_to_s3(
                    output_folder=s3_upload_folder,
                    recipe_name=recipe_name,
                    job_id=job_id,
                )

                # clean up temporary folder after upload
                if s3_upload_folder.exists():
                    shutil.rmtree(s3_upload_folder)
                    logging.debug(
                        f"Cleaned up temporary upload folder: {s3_upload_folder}"
                    )

                # update outputs directory in firebase
                self.update_outputs_directory(
                    job_id, upload_result.get("outputs_directory")
                )

                return upload_result

        except Exception as e:
            logging.error(e)
            return {"success": False, "error": e}

    def upload_outputs_to_s3(self, output_folder, recipe_name, job_id):
        """
        Upload packing outputs to S3 bucket
        """

        bucket_name = self.db.bucket_name
        region_name = self.db.region_name
        sub_folder_name = self.db.sub_folder_name
        s3_prefix = f"{sub_folder_name}/{recipe_name}/{job_id}"

        try:
            upload_result = self.db.upload_directory(
                local_directory_path=output_folder, s3_prefix=s3_prefix
            )

            if upload_result["success"]:
                # generate public URLs for the uploaded files
                base_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com"
                public_urls = [
                    f"{base_url}/{file_info['s3_key']}"
                    for file_info in upload_result["uploaded_files"]
                ]
                outputs_directory = f"https://us-west-2.console.aws.amazon.com/s3/buckets/{bucket_name}/{s3_prefix}/"

                logging.info(
                    f"Successfully uploaded {upload_result['total_files']} files to {outputs_directory}"
                )
                logging.debug(f"Total size: {upload_result['total_size']:,} bytes")
                logging.debug(f"Public URL base: {base_url}/{s3_prefix}/")

                return {
                    "success": True,
                    "run_id": job_id,
                    "s3_bucket": bucket_name,
                    "s3_prefix": s3_prefix,
                    "public_url_base": f"{base_url}/{s3_prefix}/",
                    "uploaded_files": upload_result["uploaded_files"],
                    "total_files": upload_result["total_files"],
                    "total_size": upload_result["total_size"],
                    "urls": public_urls,
                    "outputs_directory": outputs_directory,
                }
        except Exception as e:
            logging.error(e)
            return {"success": False, "error": e}

    def update_outputs_directory(self, job_id, outputs_directory):
        if not self.db or self.db.s3_client:
            # switch to firebase handler to update job status
            handler = DATABASE_IDS.handlers().get("firebase")
            initialized_db = handler(default_db="staging")
        if job_id:
            timestamp = initialized_db.create_timestamp()
            initialized_db.update_or_create(
                "job_status",
                job_id,
                {
                    "timestamp": timestamp,
                    "outputs_directory": outputs_directory,
                },
            )
            logging.debug(
                f"Updated outputs s3 location {outputs_directory} for job ID: {job_id}"
            )


class DBRecipeLoader(object):
    """
    Handles the logic for downloading and parsing the recipe data from the database.
    """

    def __init__(self, db_handler):
        self.db = db_handler

    def read_config(self, config_path):
        """
        Read the config data from the database.
        """
        collection, id = self.db.get_collection_id_from_path(config_path)
        config_data, _ = self.db.get_doc_by_id(collection, id)
        if config_data:
            return config_data
        else:
            raise ValueError(f"Config not found at path: {config_path}")

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
                        if ref_link := reference.get("inherit"):
                            comp_doc = CompositionDoc(
                                comp_name,
                                object_key=None,
                                count=None,
                                regions={},
                                molarity=None,
                                priority=None,
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
    def remove_dedup_hash(data):
        """Recursively removes 'dedup_hash' from dictionaries and lists."""
        if isinstance(data, dict):
            return {
                k: DBRecipeLoader.remove_dedup_hash(v)
                for k, v in data.items()
                if k != "dedup_hash"
            }
        elif isinstance(data, list):
            return [DBRecipeLoader.remove_dedup_hash(item) for item in data]
        return data

    def remove_empty(data):
        """Recursively removes empty values from dictionaries and lists."""
        if isinstance(data, dict):
            return {
                k: DBRecipeLoader.remove_empty(v)
                for k, v in data.items()
                if v is not None and v != {}
            }
        return data

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
            "objects": DBRecipeLoader.remove_dedup_hash(obj_dict),
            "composition": DBRecipeLoader.remove_dedup_hash(comp_dict),
        }
        if db_recipe_data.get("grid_file_path"):
            recipe_data["grid_file_path"] = db_recipe_data.get("grid_file_path")
        if grad_dict:
            recipe_data["gradients"] = [
                {**v} for v in DBRecipeLoader.remove_dedup_hash(grad_dict).values()
            ]
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
