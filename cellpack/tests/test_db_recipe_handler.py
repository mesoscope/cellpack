from cellpack.autopack.DBRecipeHandler import DBRecipeHandler
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_is_nested_list():
    assert DBRecipeHandler.is_nested_list([]) == False
    assert DBRecipeHandler.is_nested_list([[], []]) == True
    assert DBRecipeHandler.is_nested_list([[1, 2], [3, 4]]) == True


def test_prep_data_for_db():
    input_data = {
        "bounding_box": [[0, 0, 0], [1000, 1000, 1]],
        "positions": [[(0.0, 0.0, 0.0)], [(0.0, 50.0, 0.0), (43.26, -25.07, 0.0)]],
        "max_jitter": [1, 1, 0],
    }
    converted_data = {
        "bounding_box": {"0": [0, 0, 0], "1": [1000, 1000, 1]},
        "positions": {
            "0": {"0": (0.0, 0.0, 0.0)},
            "1": {"0": (0.0, 50.0, 0.0), "1": (43.26, -25.07, 0.0)},
        },
        "max_jitter": [1, 1, 0],
    }
    new_data = DBRecipeHandler.prep_data_for_db(input_data)
    assert new_data == converted_data


def test_upload_data_with_recipe_and_id():
    collection = "recipe"
    data = {
        "name": "test",
        "bounding_box": [[0, 0, 0], [1000, 1000, 1]],
        "version": "1.0.0",
        "composition": {"test": {"inherit": "firebase:test_collection/test_id"}},
    }
    id = "test_id"
    recipe_doc = DBRecipeHandler(mock_db)
    expected_result = recipe_doc.upload_data(collection, data, id)

    assert expected_result[0] == "test_id"
    assert expected_result[1] == "firebase:recipe/test_id"


def test_upload_data_with_object():
    collection = "objects"
    data = {
        "name": "test",
        "test_key": "test_value",
    }
    object_doc = DBRecipeHandler(mock_db)
    expected_result = object_doc.upload_data(collection, data)

    assert expected_result[0] == "test_id"
    assert expected_result[1] == "firebase:objects/test_id"


def test_upload_objects():
    data = {"test": {"test_key": "test_value"}}
    object_doc = DBRecipeHandler(mock_db)
    object_doc.upload_objects(data)

    assert object_doc.objects_to_path_map == {"test": "firebase:objects/test_id"}


def test_upload_compositions():
    composition = {
        "space": {"regions": {"interior": ["A"]}},
    }
    recipe_to_save = {"format_version": "2.1", "name": "one_sphere", "composition": {}}
    recipe_data = {
        "name": "one_sphere",
        "objects": {
            "sphere_25": {
                "type": "single_sphere",
                "max_jitter": [1, 1, 0],
            },
        },
        "composition": {
            "space": {"regions": {"interior": ["A"]}},
        },
    }

    composition_doc = DBRecipeHandler(mock_db)
    references_to_update = composition_doc.upload_compositions(composition, recipe_to_save, recipe_data)
    assert composition_doc.comp_to_path_map == {
        "space": {"id": "test_id", "path": "firebase:composition/test_id"},
    }
    assert references_to_update == {"space": {"comp_id": "test_id", "index": "regions.interior", "name": "A"}}

def test_get_recipe_id():
    recipe_data = {
    "name": "test",
    "version": "1.0.0",
    "objects": None,
    "composition": {},
}   
    recipe_doc = DBRecipeHandler(mock_db)
    assert recipe_doc.get_recipe_id(recipe_data) == "test_v1.0.0"

# def test_upload_collections():
#     recipe_meta_data = {
#         "name": "one_sphere",
#         "version": "1.0.0",
#         "composition": {},
#     }
#     recipe_data = {
#         "name": "one_sphere",
#         "objects": {
#             "sphere_25": {
#                 "type": "single_sphere",
#                 "max_jitter": [1, 1, 0],
#             },
#         },
#         "composition": {
#             "space": {"regions": {"interior": ["A"]}},
#             "A": {"object": "sphere_25", "count": 1},
#         },
#     }

#     collection_doc = DBRecipeHandler(mock_db)
#     collection_doc.upload_collections(recipe_meta_data, recipe_data)
#     assert collection_doc.recipe_to_save == {"test_v1.0.0": "firebase:recipe/test_v1.0.0"}