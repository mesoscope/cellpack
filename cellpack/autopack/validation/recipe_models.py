from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class IngredientType(str, Enum):
    SINGLE_SPHERE = "single_sphere"
    MULTI_SPHERE = "multi_sphere"
    SINGLE_CUBE = "single_cube"
    SINGLE_CYLINDER = "single_cylinder"
    MULTI_CYLINDER = "multi_cylinder"
    GROW = "grow"
    MESH = "mesh"


class Representations(BaseModel):
    mesh: Optional[Dict] = None
    atomic: Optional[Dict] = None
    packing: Optional[Dict] = None


class RecipeObject(BaseModel):
    type: Optional[IngredientType] = IngredientType.SINGLE_SPHERE
    inherit: Optional[str] = None
    color: Optional[List[float]] = Field(None, min_length=3, max_length=3)
    radius: Optional[float] = Field(None, gt=0) # greater than 0
    representations: Optional[Representations] = None


class Recipe(BaseModel):
    name: str
    version: Optional[str] = "2.0.0"
    format_version: Optional[str] = "2.1"
    bounding_box: List[List[float]] = [[0.0, 0.0, 0.0], [100.0, 100.0, 100.0]]
    objects: Optional[Dict[str, Any]] = {}

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(model, value):
        if not value or not value.strip():
            raise ValueError("Recipe name cannot be empty")
        return value