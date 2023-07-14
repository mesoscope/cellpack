from cellpack.autopack.DBHandler import ObjectDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_object_doc_as_dict():
    object_doc = ObjectDoc("test", {"test_key": "test_value"})
    expected_dict = {"name": "test", "test_key": "test_value"}
    assert object_doc.as_dict() == expected_dict


def test_convert_position_in_representation():
    position_data_db = {
        "positions": {
            "0": {"0": [0.0, 0.0, 0.0]},
            "1": {"0": [0.0, 50.0, 0.0], "1": [43.26, -25.07, 0.0]},
        }
    }
    converted_position_data = {
        "positions": {
            "0": {"0": (0.0, 0.0, 0.0)},
            "1": {"0": (0.0, 50.0, 0.0), "1": (43.26, -25.07, 0.0)},
        }
    }
    convert_position_to_tuple = ObjectDoc.convert_positions_in_representation(
        position_data_db
    )
    assert convert_position_to_tuple == converted_position_data


def test_convert_representation():
    test_data = {
        "name": "test_name",
        "other_value": "other_value",
        "representations": {"packing": {"positions": {"0": {}, "1": {}}}},
    }
    expected_result = {
        "name": "test_name",
        "other_value": "other_value",
        "representations": {"packing": {"positions": {"0": {}, "1": {}}}},
    }
    result = ObjectDoc.convert_representation(test_data, mock_db)
    assert result == expected_result


def test_object_doc_should_write_with_no_existing_doc():
    object_doc = ObjectDoc("test", {"test_key": "test_value"})
    doc, doc_id = object_doc.should_write(mock_db)
    assert doc_id is None
    assert doc is None


def test_object_doc_should_write_with_existing_doc():
    existing_doc = {"name": "test", "test_key": "test_value"}
    mock_db.data = existing_doc
    object_doc = ObjectDoc("test", {"test_key": "test_value"})

    doc, doc_id = object_doc.should_write(mock_db)
    assert doc_id is not None
    assert doc == existing_doc
