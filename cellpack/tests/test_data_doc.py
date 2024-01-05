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
