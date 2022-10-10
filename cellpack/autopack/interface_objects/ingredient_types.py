from enum import Enum
import json


class INGREDIENT_TYPE(Enum):
    SINGLE_SPHERE = "single_sphere"
    MULTI_SPHERE = "multi_sphere"
    SINGLE_CUBE = "single_cube"
    SINGLE_CYLINDER = "single_cylinder"
    MULTI_CYLINDER = "multi_cylinder"
    GROW = "grow"

#     @property
#     def to_JSON(self):
#         return json.dumps(self, default=lambda o: o.__dict__, 
#             sort_keys=True, indent=4)
# print(INGREDIENT_TYPE.to_JSON())