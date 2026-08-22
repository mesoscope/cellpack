from cellpack.autopack.DBRecipeHandler import DataDoc
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})

object_example = {
    "count": 121,
    "object": {
        "gradient": {
            "mode": "surface",
            "name": "nucleus_surface_gradient",
        },
        "name": "peroxisome",
    },
}

composition_example = {
    "count": 1,
    "regions": {"interior": []},
    "object": {
        "name": "mean_nucleus",
        "partners": {"all_partners": []},
    },
    "name": "nucleus",
}


def test_is_nested_list():
    assert DataDoc.is_nested_list([]) is False
    assert DataDoc.is_nested_list([[], []]) is True
    assert DataDoc.is_nested_list([[1, 2], [3, 4]]) is True
    assert DataDoc.is_nested_list([1, [1, 2]]) is True
    assert DataDoc.is_nested_list([[1, 2], 1]) is True


def test_is_obj():
    assert DataDoc.is_obj(object_example) is True
    assert DataDoc.is_obj(composition_example) is False


def test_generate_hash():
    test_cases = [object_example, composition_example, None]

    for input_data in test_cases:
        generated_hash = DataDoc.generate_hash(input_data)
        assert isinstance(generated_hash, str)
        assert generated_hash == DataDoc.generate_hash(input_data)


def test_generate_hash_is_stable_across_key_order():
    recipe_a = {"name": "test", "version": "1.0", "count": 1}
    recipe_b = {"count": 1, "version": "1.0", "name": "test"}
    assert DataDoc.generate_hash(recipe_a) == DataDoc.generate_hash(recipe_b)


def test_generate_hash_is_stable_across_string_list_order():
    recipe_a = {
        "composition": {
            "space": {"regions": {"interior": ["A", "B", "C", "D", "E"]}},
            "A": {"object": "sphere_100", "count": 6},
            "B": {"object": "sphere_200", "count": 2},
            "C": {"object": "sphere_50", "count": 15},
        }
    }
    recipe_b = {
        "composition": {
            "A": {"count": 6, "object": "sphere_100"},
            "C": {"object": "sphere_50", "count": 15},
            "B": {"object": "sphere_200", "count": 2},
            "space": {"regions": {"interior": ["E", "C", "A", "D", "B"]}},
        }
    }
    assert DataDoc.generate_hash(recipe_a) == DataDoc.generate_hash(recipe_b)


def test_generate_hash_preserves_positional_list_order():
    # numeric/nested lists encode positional data (bounding boxes, vectors, colors) and must remain order-sensitive.
    bbox_a = {"bounding_box": [[0, 0, 0], [1000, 1000, 1]]}
    bbox_b = {"bounding_box": [[1000, 1000, 1], [0, 0, 0]]}
    assert DataDoc.generate_hash(bbox_a) != DataDoc.generate_hash(bbox_b)

    axis_a = {"rotation_axis": [0, 0, 1]}
    axis_b = {"rotation_axis": [1, 0, 0]}
    assert DataDoc.generate_hash(axis_a) != DataDoc.generate_hash(axis_b)


def test_generate_hash_is_stable_across_mixed_list_order():
    # region lists that mix string refs with inline dicts should dedup regardless of element order.
    recipe_a = {
        "composition": {
            "bounding_area": {
                "regions": {
                    "interior": [
                        "outer_sphere",
                        {"object": "green_sphere", "count": 5},
                    ]
                }
            }
        }
    }
    recipe_b = {
        "composition": {
            "bounding_area": {
                "regions": {
                    "interior": [
                        {"object": "green_sphere", "count": 5},
                        "outer_sphere",
                    ]
                }
            }
        }
    }
    assert DataDoc.generate_hash(recipe_a) == DataDoc.generate_hash(recipe_b)
