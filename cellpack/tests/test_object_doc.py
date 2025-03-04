from cellpack.autopack.DBRecipeHandler import ObjectDoc
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


def test_check_doc_existence_for_object():
    object_doc = {
        "peroxisome": {
            "gradient": {
                "mode": "surface",
                "name": "nucleus_surface_gradient",
            },
            "name": "peroxisome",
        }
    }

    test_data = {
        "doc": object_doc,
        "dedup_hash": ObjectDoc.generate_hash({"doc": object_doc}),
    }

    result = mock_db.check_doc_existence("objects", test_data)
    assert result is None

    existing_doc = mock_db._existing_doc[0]
    assert existing_doc["dedup_hash"] == test_data["dedup_hash"]
