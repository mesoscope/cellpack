import pytest
from ..autopack.ingredient import Ingredient


@pytest.mark.parametrize(
    "ingredient_info, output",
    [
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {"distribution": "uniform", "min": 1, "max": 1},
            },
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {"distribution": "uniform", "min": 1, "max": 1},
            },
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
            },
            "Ingredient info must contain a count",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": -1,
            },
            "Ingredient count must be greater than or equal to 0",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {},
            },
            "Ingredient count options must contain a distribution",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {
                    "distribution": "invalid_distribution",
                },
            },
            "invalid_distribution is not a valid distribution",
        ),
        (
            {
                "name": "test",
                "type": "single_sphere",
                "count": 1,
                "count_options": {
                    "distribution": "uniform",
                },
            },
            "Missing option 'min' for uniform distribution",
        ),
    ],
)
def test_validate_ingredient_info(ingredient_info, output):
    try:
        validated_info = Ingredient.validate_ingredient_info(ingredient_info)
        assert validated_info == output
    except Exception as e:
        assert str(e) == output
