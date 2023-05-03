from unittest.mock import Mock


class MockDB(object):
    def __init__(self, data) -> None:
        for index, name in enumerate(data):
            obj = data[name]
            obj["id"] = index
        self.data = data
        self.name = "test_db"

    @staticmethod
    def is_firebase_obj(obj):
        return True

    def db_name(self):
        return "test_db"

    @staticmethod
    def doc_to_dict(doc):
        return doc

    def get_doc_by_name(self, _, name):
        if len(self.data) >= 1:
            if name in self.data["name"]:
                return [self.data]
        else:
            return None

    def doc_id(self, doc):
        if doc:
            doc["id"] = "test_id"
        return doc["id"]

    @staticmethod
    def is_reference(path):
        if path is None:
            return False
        if path.startswith("firebase:"):
            return True
        return False

    @staticmethod
    def get_doc_by_ref(key):
        if key:
            return {"test": "downloaded_data"}, key
        else:
            return {}, None

    def upload_doc(self, collection, doc):
        return ("test_datetime", doc)

    def set_doc(self, collection, id, data):
        doc_ref = Mock()
        return doc_ref

    def get_path_from_ref(self, doc):
        return "firebase:test_collection/test_id"

    def create_path(self, collection, doc_id):
        return f"firebase:{collection}/{doc_id}"

    def get_doc_by_id(self, collection, id):
        doc_ref = Mock()
        return self.data, doc_ref

    def update_reference_on_doc(self, doc_ref, index, new_item_ref):
        return True

    def update_elements_in_array(self, doc_ref, index, new_item_ref, remove_item):
        return True
