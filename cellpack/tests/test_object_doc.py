from cellpack.autopack.DBRecipeHandler import ObjectDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_object_doc_should_write():
    object_doc = ObjectDoc("test", {"test_setting": "test_value"})
    doc, doc_id = object_doc.should_write(mock_db)
    assert doc_id is None
