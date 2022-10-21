from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE
from .grow import ActinIngredient, GrowIngredient  # noqa: F401
from .multi_cylinder import MultiCylindersIngr  # noqa: F401
from .multi_sphere import MultiSphereIngr  # noqa: F401
from .single_cube import SingleCubeIngr  # noqa: F401
from .single_sphere import SingleSphereIngr  # noqa: F401
from .single_cylinder import SingleCylinderIngr  # noqa: F401
from .Ingredient import Ingredient  # noqa: F401

__all__ = ["grow", "multi_cylinder", "multi_sphere", "single_cube", "single_sphere"]


type_to_class_map = {
    INGREDIENT_TYPE.SINGLE_SPHERE: SingleSphereIngr,
    INGREDIENT_TYPE.MULTI_SPHERE: MultiSphereIngr,
    INGREDIENT_TYPE.SINGLE_CUBE: SingleCubeIngr,
    INGREDIENT_TYPE.SINGLE_CYLINDER: SingleCylinderIngr,
    INGREDIENT_TYPE.MULTI_CYLINDER: MultiCylindersIngr,
    INGREDIENT_TYPE.GROW: GrowIngredient,
}


def get_ingredient_class(ingredient_type):
    return type_to_class_map[ingredient_type]
