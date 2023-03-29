from cellpack.autopack.DBRecipeHandler import ObjectDoc, DBRecipeHandler
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_object_doc_should_write_with_no_existing_doc():
    object_doc = ObjectDoc("test", {"test_setting": "test_value"})
    doc, doc_id = object_doc.should_write(mock_db)
    assert doc_id is None
    assert doc is None


def test_object_doc_should_write_with_existing_doc():
    existing_doc = {
        "name": "test",
        "test_setting": "test_value"
    }
    mock_db.data = existing_doc
    object_doc = ObjectDoc("test", {"test_setting": "test_value"})
    doc, doc_id = object_doc.should_write(mock_db)
    assert doc_id is not None
    assert doc == existing_doc


def test_convert_position_in_representation():
    position_data_db = {
            "positions": {'0': {'0': [0.0, 0.0, 0.0]}, '1': {'0': [0.0, 50.0, 0.0], '1': [43.26, -25.07, 0.0]}}
        }
    converted_position_data = {
            "positions": {'0': {'0': (0.0, 0.0, 0.0)}, '1': {'0': (0.0, 50.0, 0.0), '1': (43.26, -25.07, 0.0)}}
        }
    convert_position_to_tuple = ObjectDoc.convert_positions_in_representation(position_data_db)
    assert convert_position_to_tuple == converted_position_data

def test_convert_representation_with_object():
    obj = ObjectDoc("test", {"test_setting": "test_value"})
    doc = vars(obj)
    expected_result = {"name": "test", "settings": {"test_setting": "test_value"}}
    result = ObjectDoc.convert_representation(doc, mock_db)
    assert result == expected_result


def test_prep_data_for_db():
    input_data = {
            "bounding_box": [[0,0,0], [1000, 1000, 1]],
            "positions": [[(0.0, 0.0, 0.0)], [(0.0, 50.0, 0.0), (43.26, -25.07, 0.0)]],
            "max_jitter": [1,1,0]
        }
    converted_data = {
            "bounding_box": {"0": [0,0,0], "1": [1000, 1000,1]},
            "positions": {"0": {"0": (0.0, 0.0, 0.0)}, "1": {"0": (0.0, 50.0, 0.0), "1": (43.26, -25.07, 0.0)}},
            "max_jitter": [1,1,0]
        }
    new_data = DBRecipeHandler.prep_data_for_db(input_data)
    assert new_data == converted_data