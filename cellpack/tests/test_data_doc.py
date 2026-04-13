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


def test_generate_hash_shuffled_entries():
    recipe = {
        "name": "test_recipe",
        "version": "2.0",
        "objects": {
            "sphere_a": {"type": "sphere", "radius": 10},
            "sphere_b": {"type": "sphere", "radius": 20},
        },
        "composition": {
            "space": {
                "regions": {"interior": ["sphere_a", "sphere_b"]},
                "object": {"name": "cell"},
            }
        },
    }
    shuffled_recipe = {
        "composition": {
            "space": {
                "object": {"name": "cell"},
                "regions": {"interior": ["sphere_a", "sphere_b"]},
            }
        },
        "objects": {
            "sphere_b": {"radius": 20, "type": "sphere"},
            "sphere_a": {"radius": 10, "type": "sphere"},
        },
        "version": "2.0",
        "name": "test_recipe",
    }
    assert DataDoc.generate_hash(recipe) == DataDoc.generate_hash(shuffled_recipe)


# The following tests document known cases where recipes that are semantically
# equivalent produce *different* hashes because generate_hash uses json.dumps,
# which is sensitive to list ordering, numeric types, and key presence.


def test_hash_differs_for_reordered_list_values():
    """
    List order is NOT normalized by sort_keys=True.
    Ingredient names in a region listed in different order yield different hashes,
    even though the packing result would be identical.
    """
    recipe_a = {
        "composition": {"space": {"regions": {"interior": ["sphere_a", "sphere_b"]}}}
    }
    recipe_b = {
        "composition": {"space": {"regions": {"interior": ["sphere_b", "sphere_a"]}}}
    }
    assert DataDoc.generate_hash(recipe_a) != DataDoc.generate_hash(recipe_b)


def test_hash_differs_for_int_vs_float():
    """
    Integer and float values that are numerically equal serialize differently
    (10 -> "10", 10.0 -> "10.0"), producing different hashes.
    """
    recipe_int = {"objects": {"sphere": {"radius": 10}}}
    recipe_float = {"objects": {"sphere": {"radius": 10.0}}}
    assert DataDoc.generate_hash(recipe_int) != DataDoc.generate_hash(recipe_float)


def test_hash_differs_for_explicit_null_vs_missing_key():
    """
    A key explicitly set to None/null and a key that is simply absent produce
    different hashes, even though downstream code may treat both the same way.
    """
    recipe_with_null = {"name": "test", "count": None}
    recipe_without_key = {"name": "test"}
    assert DataDoc.generate_hash(recipe_with_null) != DataDoc.generate_hash(
        recipe_without_key
    )


def test_hash_differs_for_bool_vs_int():
    """
    Python True/False serialize as JSON true/false, not 1/0.
    Code that stores a flag as a boolean in one place and an integer in another
    will produce different hashes for an otherwise identical recipe.
    """
    recipe_bool = {"options": {"randomize": True}}
    recipe_int = {"options": {"randomize": 1}}
    assert DataDoc.generate_hash(recipe_bool) != DataDoc.generate_hash(recipe_int)
