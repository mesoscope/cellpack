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
                print("self.data--- ", self.data)
                return [self.data]
        else:
            return None
        
    def doc_id(self, doc):
        if doc:
            doc["id"] = "test_id"
        return doc["id"]
    
    def if_reference(path):
        return True
    
    def get_doc_by_ref(obj):
        return {}, None
    