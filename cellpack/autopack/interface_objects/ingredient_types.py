from .meta_enum import MetaEnum


class INGREDIENT_TYPE(MetaEnum):
    SINGLE_SPHERE = "single_sphere"
    MULTI_SPHERE = "multi_sphere"
    SINGLE_CUBE = "single_cube"
    SINGLE_CYLINDER = "single_cylinder"
    MULTI_CYLINDER = "multi_cylinder"
    GROW = "grow"
    MESH = "mesh"
