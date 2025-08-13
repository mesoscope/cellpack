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
        priority=None,
    )
    expected_dict = {
        "name": "test",
        "count": 1,
        "object": {"test_key": "test_value"},
        "regions": {},
        "molarity": None,
        "priority": None,
    }
    assert composition_doc.as_dict() == expected_dict


def test_get_reference_data_with_dict():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object={"object": "firebase:objects/test_id"},
        regions={},
        molarity=None,
        priority=None,
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
        priority=None,
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
        priority=None,
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
        priority=None,
    )
    resolved_data = {
        "name": "test",
        "object": None,
        "count": 1,
        "molarity": None,
        "priority": None,
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
        priority=-1,
    )
    resolved_data = {
        "name": "test",
        "object": None,
        "count": 1,
        "molarity": None,
        "priority": -1,
        "regions": {},
    }
    composition_db_doc.resolve_db_regions(composition_db_doc.as_dict(), mock_db)
    assert composition_db_doc.as_dict() == resolved_data


def test_build_dependency_graph():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions=None,
        molarity=None,
        priority=-1,
    )
    compositions = {
        "space": {"regions": {"interior": ["A"]}},
        "A": {"object": "sphere_25", "count": 5},
    }
    dependency_map = composition_db_doc.build_dependency_graph(compositions)
    assert dependency_map == {"space": ["A"], "A": []}


def test_build_dependency_graph_with_complex_compositions():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions=None,
        molarity=None,
        priority=None,
    )
    complex_compositions = {
        "space": {"regions": {"interior": ["tree", "A", "B", "C"]}},
        "tree": {"object": "sphere_tree_A", "molarity": 1},
        "A": {
            "object": "sphere_100",
            "regions": {
                "surface": [
                    {"object": "sphere_50", "count": 5},
                    {"object": "sphere_75", "count": 1},
                ],
                "interior": [{"object": "sphere_25", "count": 30, "priority": -1}],
            },
        },
        "B": {
            "object": "sphere_100",
            "regions": {"surface": ["B_sphere_75"], "interior": ["B_sphere_50"]},
        },
        "B_sphere_50": {"object": "sphere_50", "count": 8, "priority": -1},
        "B_sphere_75": {"object": "sphere_75", "count": 3},
    }

    dependency_map = composition_db_doc.build_dependency_graph(complex_compositions)
    assert dependency_map == {
        "space": ["tree", "A", "B"],
        "tree": [],
        "A": [],
        "B": ["B_sphere_75", "B_sphere_50"],
        "B_sphere_75": [],
        "B_sphere_50": [],
    }


def test_comp_upload_order():
    composition_db_doc = CompositionDoc(
        name="test",
        count=1,
        object=None,
        regions=None,
        molarity=None,
        priority=None,
    )
    compositions = {
        "space": {"regions": {"interior": ["A"]}},
        "A": {"object": "sphere_25", "count": 5},
    }
    upload_order = composition_db_doc.comp_upload_order(compositions)
    assert upload_order == ["A", "space"]
