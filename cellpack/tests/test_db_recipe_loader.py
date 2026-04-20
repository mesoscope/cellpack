import pytest
from cellpack.autopack.DBRecipeHandler import DBRecipeLoader
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})

downloaded_data_from_firebase = {
    "version": "linear",
    "format_version": "2.1",
    "composition": {
        "membrane": {
            "count": 1,
            "regions": {
                "interior": [
                    {
                        "count": 121,
                        "object": {
                            "gradient": {
                                "mode": "surface",
                                "name": "nucleus_surface_gradient",
                            },
                            "name": "peroxisome",
                        },
                    },
                    {
                        "count": 1,
                        "regions": {"interior": []},
                        "object": {
                            "name": "mean_nucleus",
                            "partners": {"all_partners": []},
                        },
                        "name": "nucleus",
                    },
                ]
            },
            "object": {
                "name": "mean_membrane",
                "type": "mesh",
            },
            "name": "membrane",
        },
        "nucleus": {
            "count": 1,
            "regions": {"interior": []},
            "object": {
                "name": "mean_nucleus",
                "partners": {"all_partners": []},
            },
            "name": "nucleus",
        },
        "bounding_area": {
            "count": None,
            "regions": {
                "interior": [
                    {
                        "count": 1,
                        "regions": {
                            "interior": [
                                {
                                    "count": 121,
                                    "object": {
                                        "gradient": {
                                            "mode": "surface",
                                            "name": "nucleus_surface_gradient",
                                        },
                                        "name": "peroxisome",
                                    },
                                },
                                {
                                    "count": 1,
                                    "regions": {"interior": []},
                                    "object": {
                                        "name": "mean_nucleus",
                                        "partners": {"all_partners": []},
                                    },
                                    "name": "nucleus",
                                },
                            ]
                        },
                        "object": {
                            "name": "mean_membrane",
                            "type": "mesh",
                        },
                        "name": "membrane",
                    }
                ]
            },
            "name": "bounding_area",
        },
    },
    "version": "linear",
    "bounding_box": [[-110, -45, -62], [110, 45, 62]],
    "name": "test_recipe",
    "description": "test_description",
}


compiled_firebase_recipe_example = {
    "name": "test_recipe",
    "description": "test_description",
    "format_version": "2.1",
    "version": "linear",
    "bounding_box": [[-110, -45, -62], [110, 45, 62]],
    "objects": {
        "mean_membrane": {
            "name": "mean_membrane",
            "type": "mesh",
        },
        "peroxisome": {
            "name": "peroxisome",
            "gradient": "nucleus_surface_gradient",
        },
        "mean_nucleus": {
            "name": "mean_nucleus",
            "partners": {"all_partners": []},
        },
    },
    "gradients": [
        {
            "name": "nucleus_surface_gradient",
            "mode": "surface",
        }
    ],
    "composition": {
        "bounding_area": {"regions": {"interior": ["membrane"]}},
        "membrane": {
            "count": 1,
            "object": "mean_membrane",
            "regions": {
                "interior": [{"object": "peroxisome", "count": 121}, "nucleus"]
            },
        },
        "nucleus": {
            "count": 1,
            "object": "mean_nucleus",
            "regions": {"interior": []},
        },
    },
}


def test_get_grad_and_obj():
    obj_data = downloaded_data_from_firebase["composition"]["membrane"]["regions"][
        "interior"
    ][0]["object"]
    obj_dict = {
        "peroxisome": {
            "gradient": {
                "mode": "surface",
                "name": "nucleus_surface_gradient",
            },
            "name": "peroxisome",
        }
    }
    grad_dict = {}
    obj_dict, grad_dict = DBRecipeLoader._get_grad_and_obj(
        obj_data, obj_dict, grad_dict
    )
    assert obj_dict == {
        "peroxisome": {"gradient": "nucleus_surface_gradient", "name": "peroxisome"}
    }
    assert grad_dict == {
        "nucleus_surface_gradient": {
            "mode": "surface",
            "name": "nucleus_surface_gradient",
        }
    }


@pytest.fixture
def sort_data_from_composition():
    return DBRecipeLoader.collect_and_sort_data(
        downloaded_data_from_firebase["composition"]
    )


def test_collect_and_sort_data(sort_data_from_composition):
    objects, gradients, composition = sort_data_from_composition
    assert objects == compiled_firebase_recipe_example["objects"]
    assert gradients == {
        "nucleus_surface_gradient": {
            "name": "nucleus_surface_gradient",
            "mode": "surface",
        }
    }
    assert composition == compiled_firebase_recipe_example["composition"]


def test_compile_db_recipe_data(sort_data_from_composition):
    objects, gradients, composition = sort_data_from_composition
    compiled_recipe = DBRecipeLoader.compile_db_recipe_data(
        downloaded_data_from_firebase, objects, gradients, composition
    )
    assert compiled_recipe == compiled_firebase_recipe_example
