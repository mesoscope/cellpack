from cellpack.autopack.DBRecipeHandler import CompositionDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_composition_doc_as_dict():
    composition_doc = CompositionDoc(
        name="test",
        count=1,
        object={"test_key": "test_value"},
        regions={},
        molarity=None,
    )
    expected_dict = {
        "name": "test",
        "count": 1,
        "object": {"test_key": "test_value"},
        "regions": {},
        "molarity": None,
    }
    assert composition_doc.as_dict() == expected_dict

def test_composition_oc_should_write_with_no_existing_doc():
    recipe_data = {
        "bounding_box": [[0,0,0], [10,10,10]],
        "name": "test",
        "count": 1,
        "objects": None,
        "regions": {}
    }
    composition_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions={},
        molarity=None,
    )
    doc, doc_id = composition_doc.should_write(mock_db,recipe_data)
    assert doc_id is None
    assert doc is None

def test_composition_doc_should_write_with_existing_doc():
    existing_doc = {
        "name": "test",
        "count": 1,
        "object": None,
        "regions": {},
        "molarity": None,
    }
    mock_db.data = existing_doc
    recipe_data = {
        "name": "test",
        "count": 1,
        "objects": None,
    }
    composition_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions={},
        molarity=None,
    )

    doc, doc_id = composition_doc.should_write(mock_db,recipe_data)
    assert doc_id is not None
    assert doc == existing_doc
