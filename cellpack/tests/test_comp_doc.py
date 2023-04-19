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


def test_get_reference_data_with_dict():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object={"object": "firebase:objects/test_id"},
        regions={},
        molarity=None,
    )
    downloaded_data, key = composition_db_doc.get_reference_data(
        composition_db_doc.as_dict()["object"], mock_db
    )
    assert downloaded_data == {"test": "downloaded_data"}
    assert key == "firebase:objects/test_id"


def test_get_reference_data_with_key():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object="firebase:objects/test_id",
        regions={},
        molarity=None,
    )
    downloaded_data, key = composition_db_doc.get_reference_data(
        composition_db_doc.as_dict()["object"], mock_db
    )
    assert downloaded_data == {"test": "downloaded_data"}
    assert key is None


def test_get_reference_data_with_none():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions={},
        molarity=None,
    )
    downloaded_data, key = composition_db_doc.get_reference_data(
        composition_db_doc.as_dict()["object"], mock_db
    )
    assert downloaded_data == {}
    assert key is None


def test_resolve_db_regions():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions={
            "test_region_name": [
                "firebase:composition/test_id",
                {"count": 1, "object": "firebase:objects/test_id"},
            ]
        },
        molarity=None,
    )
    resolved_data = {
        "name": "test",
        "object": None,
        "count": 1,
        "molarity": None,
        "regions": {
            "test_region_name": [
                {"test": "downloaded_data"},
                {"count": 1, "object": {"test": "downloaded_data"}},
            ]
        },
    }
    composition_db_doc.resolve_db_regions(composition_db_doc.as_dict(), mock_db)
    assert composition_db_doc.as_dict() == resolved_data


def test_resolve_db_regions_with_none():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions=None,
        molarity=None,
    )
    resolved_data = {
        "name": "test",
        "object": None,
        "count": 1,
        "molarity": None,
        "regions": {},
    }
    composition_db_doc.resolve_db_regions(composition_db_doc.as_dict(), mock_db)
    assert composition_db_doc.as_dict() == resolved_data


def test_resolve_local_regions():
    full_recipe_data = {
        "name": "one_sphere",
        "objects": {
            "sphere_25": {
                "type": "single_sphere",
                "max_jitter": [1, 1, 0],
            },
        },
        "composition": {
            "space": {"regions": {"interior": ["A"]}},
            "A": {"object": "sphere_25", "count": 500},
        },
    }

    local_data = CompositionDoc(
        name="space",
        count=None,
        object=None,
        regions={
            "interior": [
                "A",
            ]
        },
        molarity=None,
    )

    resolved_data = {
        "name": "space",
        "object": None,
        "count": None,
        "molarity": None,
        "regions": {
            "interior": [
                {
                    "name": "A",
                    "object": {"type": "single_sphere", "max_jitter": [1, 1, 0]},
                    "count": 500,
                    "molarity": None,
                    "regions": {},
                }
            ]
        },
    }
    local_data.resolve_local_regions(local_data.as_dict(), full_recipe_data, mock_db)
    assert local_data.as_dict() == resolved_data


def test_check_and_replace_references():
    objects_to_path_map = {"test_obj": "firebase:objects/test_id"}
    references_to_update = {}
    composition_doc = CompositionDoc(
        name="test",
        count=1,
        object="firebase:objects/test_id",
        regions={"interior": [{"object": "test_obj", "count": 1}]},
        molarity=None,
    )
    composition_doc.check_and_replace_references(
        objects_to_path_map, references_to_update, mock_db
    )
    assert composition_doc.as_dict()["object"] == "firebase:objects/test_id"
    assert composition_doc.as_dict()["regions"] == {
        "interior": [{"object": "firebase:objects/test_id", "count": 1}]
    }


def test_composition_oc_should_write_with_no_existing_doc():
    recipe_data = {
        "bounding_box": [[0, 0, 0], [10, 10, 10]],
        "name": "test",
        "count": 1,
        "objects": None,
        "regions": {},
    }
    composition_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions={},
        molarity=None,
    )
    doc, doc_id = composition_doc.should_write(mock_db, recipe_data)
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

    doc, doc_id = composition_doc.should_write(mock_db, recipe_data)
    assert doc_id is not None
    assert doc == existing_doc
