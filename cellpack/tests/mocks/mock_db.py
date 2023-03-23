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
        if name in self.data:
            return self.data[name]
        else:
            return None
        
    def doc_id(self, doc):
        return doc["id"]
    
