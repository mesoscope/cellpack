class MockDB(object):
    def __init__(self, data) -> None:
        for index, name in enumerate(data):
            obj = data[name]
            obj["id"] = index
        self.data = data

    @staticmethod
    def is_firebase_obj(obj):
        return True
    
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
        return True
    
    @staticmethod
    def get_doc_by_ref(key):
        if key:
            return {"test": "downloaded_data"}, key
        else:
            return {}, None
    