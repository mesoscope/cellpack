from cellpack.autopack.DBRecipeHandler import DBUploader
from cellpack.tests.mocks.mock_db import MockDB
from unittest.mock import MagicMock, patch

mock_db = MockDB({})


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
    new_data = DBUploader.prep_data_for_db(input_data)
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
    recipe_doc = DBUploader(mock_db)
    expected_result = recipe_doc.upload_data(collection, data, id)

    assert expected_result[0] == "test_id"
    assert expected_result[1] == "firebase:recipe/test_id"


def test_upload_data_with_object():
    collection = "objects"
    data = {
        "name": "test",
        "test_key": "test_value",
    }
    object_doc = DBUploader(mock_db)
    expected_result = object_doc.upload_data(collection, data)

    assert expected_result[0] == "test_id"
    assert expected_result[1] == "firebase:objects/test_id"


def test_upload_objects():
    data = {"test": {"test_key": "test_value"}}
    object_doc = DBUploader(mock_db)
    object_doc.upload_objects(data)
    assert object_doc.objects_to_path_map == {"test": "firebase:objects/test_id"}


def test_upload_objects_with_gradient():
    data = {"test": {"test_key": "test_value", "gradient": "test_grad_name"}}
    object_handler = DBUploader(mock_db)
    object_handler.grad_to_path_map = {"test_grad_name": "firebase:gradients/test_id"}

    with patch(
        "cellpack.autopack.DBRecipeHandler.ObjectDoc", return_value=MagicMock()
    ) as mock_object_doc:
        mock_object_doc.return_value.should_write.return_value = (
            None,
            "firebase:gradients/test_id",
        )
        object_handler.upload_objects(data)
        mock_object_doc.assert_called()
        called_with_settings = mock_object_doc.call_args.kwargs["settings"]
    assert data["test"]["gradient"] == "test_grad_name"
    assert called_with_settings["gradient"] == "firebase:gradients/test_id"


def test_upload_compositions():
    composition = {
        "space": {"regions": {"interior": ["A"]}},
    }
    recipe_to_save = {"format_version": "2.1", "name": "one_sphere", "composition": {}}

    composition_doc = DBUploader(mock_db)
    references_to_update = composition_doc.upload_compositions(
        composition, recipe_to_save
    )
    assert composition_doc.comp_to_path_map == {
        "space": {"id": "test_id", "path": "firebase:composition/test_id"},
    }
    assert references_to_update == {
        "space": [{"comp_id": "test_id", "index": "regions.interior", "name": "A"}]
    }


def test_upload_gradients():
    data = [{"name": "test_grad_name", "test_key": "test_value"}]
    gradient_doc = DBUploader(mock_db)
    gradient_doc.upload_gradients(data)
    assert gradient_doc.grad_to_path_map == {
        "test_grad_name": "firebase:gradients/test_id"
    }


def test_get_recipe_id():
    recipe_data = {
        "name": "test",
        "version": "1.0.0",
        "objects": None,
        "composition": {},
    }
    recipe_doc = DBUploader(mock_db)
    assert recipe_doc._get_recipe_id(recipe_data) == "test_v_1.0.0"


def test_upload_collections():
    recipe_meta_data = {
        "name": "one_sphere",
        "version": "1.0.0",
        "composition": {},
    }
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
            "A": {"object": "sphere_25", "count": 1},
        },
    }

    recipe_doc = DBUploader(mock_db)
    expected_result = {
        "name": "one_sphere",
        "version": "1.0.0",
        "composition": {
            "space": {"inherit": "firebase:composition/test_id"},
            "A": {"inherit": "firebase:composition/test_id"},
        },
    }
    recipe_to_save = recipe_doc.upload_collections(recipe_meta_data, recipe_data)
    assert recipe_to_save == expected_result


def test_upload_recipe():
    recipe_meta_data = {
        "name": "one_sphere",
        "version": "1.0.0",
        "composition": {},
    }
    recipe_data = {
        "name": "one_sphere",
        "version": "1.0.0",
        "objects": {
            "sphere_25": {
                "type": "single_sphere",
                "max_jitter": [1, 1, 0],
            },
        },
        "composition": {
            "space": {"regions": {"interior": ["A"]}},
            "A": {"object": "sphere_25", "count": 1},
        },
    }

    recipe_doc = DBUploader(mock_db)
    recipe_doc.upload_recipe(recipe_meta_data, recipe_data)
    assert recipe_doc.comp_to_path_map == {
        "space": {"path": "firebase:composition/test_id", "id": "test_id"},
        "A": {"path": "firebase:composition/test_id", "id": "test_id"},
    }
    assert recipe_doc.objects_to_path_map == {"sphere_25": "firebase:objects/test_id"}
