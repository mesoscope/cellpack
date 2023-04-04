from cellpack.autopack.DBRecipeHandler import DBRecipeHandler
from cellpack.tests.mocks.mock_db import MockDB

mock_db = MockDB({})


def test_prep_data_for_db():
    input_data = {
            "bounding_box": [[0,0,0], [1000, 1000, 1]],
            "positions": [[(0.0, 0.0, 0.0)], [(0.0, 50.0, 0.0), (43.26, -25.07, 0.0)]],
            "max_jitter": [1,1,0]
        }
    converted_data = {
            "bounding_box": {"0": [0,0,0], "1": [1000, 1000,1]},
            "positions": {"0": {"0": (0.0, 0.0, 0.0)}, "1": {"0": (0.0, 50.0, 0.0), "1": (43.26, -25.07, 0.0)}},
            "max_jitter": [1,1,0]
        }
    new_data = DBRecipeHandler.prep_data_for_db(input_data)
    assert new_data == converted_data