from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# note: ge(>=), le(<=), gt(>), lt(<)


# OBJECT-LEVEL CLASSES
class IngredientType(str, Enum):
    SINGLE_SPHERE = "single_sphere"
    MULTI_SPHERE = "multi_sphere"
    SINGLE_CUBE = "single_cube"
    SINGLE_CYLINDER = "single_cylinder"
    MULTI_CYLINDER = "multi_cylinder"
    GROW = "grow"
    MESH = "mesh"


class PackingMode(str, Enum):
    RANDOM = "random"
    CLOSE = "close"
    CLOSE_PARTNER = "closePartner"
    RANDOM_PARTNER = "randomPartner"
    GRADIENT = "gradient"
    HEXATILE = "hexatile"
    SQUARETILE = "squaretile"
    TRIANGLETILE = "triangletile"


class PlaceMethod(str, Enum):
    JITTER = "jitter"
    SPHERES_SST = "spheresSST"


class WeightMode(str, Enum):
    LINEAR = "linear"
    SQUARE = "square"
    CUBE = "cube"
    POWER = "power"
    EXPONENTIAL = "exponential"


class PickMode(str, Enum):
    MAX = "max"
    MIN = "min"
    RANDOM = "rnd"
    LINEAR = "linear"
    BINARY = "binary"
    SUB = "sub"
    REG = "reg"


class GradientMode(str, Enum):
    X = "x"
    Y = "y"
    Z = "z"
    VECTOR = "vector"
    RADIAL = "radial"
    SURFACE = "surface"


class CoordinateSystem(str, Enum):
    LEFT = "left"
    RIGHT = "right"


# 3-element float array - used for 3D vectors, colors, etc.
ThreeFloatArray = List[float]


class WeightModeSettings(BaseModel):
    decay_length: Optional[float] = Field(None, ge=0, le=1)
    power: Optional[float] = Field(None, gt=0)


class GradientModeSettings(BaseModel):
    object: Optional[str] = None
    scale_to_next_surface: Optional[bool] = None
    direction: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)
    center: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)
    radius: Optional[float] = Field(None, gt=0)


class RecipeGradient(BaseModel):
    description: Optional[str] = None
    mode: GradientMode = Field(GradientMode.X)
    pick_mode: PickMode = Field(PickMode.LINEAR)
    weight_mode: Optional[WeightMode] = None
    reversed: Optional[bool] = None
    invert: Optional[bool] = None
    weight_mode_settings: Optional[WeightModeSettings] = None
    mode_settings: Optional[GradientModeSettings] = None

    @model_validator(mode="after")
    def validate_mode_requirements(self):
        """Validate that required `mode_settings` exist for modes that need them"""
        # surface mode requires mode_settings with object
        if self.mode == GradientMode.SURFACE:
            if not self.mode_settings:
                raise ValueError("Surface gradient mode requires 'mode_settings' field")
            if (
                not hasattr(self.mode_settings, "object")
                or not self.mode_settings.object
            ):
                raise ValueError(
                    "Surface gradient mode requires 'object' in mode_settings"
                )

        # vector mode requires mode_settings with direction
        elif self.mode == GradientMode.VECTOR:
            if not self.mode_settings:
                raise ValueError("Vector gradient mode requires 'mode_settings' field")
            if (
                not hasattr(self.mode_settings, "direction")
                or not self.mode_settings.direction
            ):
                raise ValueError(
                    "Vector gradient mode requires 'direction' in mode_settings"
                )

        return self

    @field_validator("mode_settings")
    @classmethod
    def validate_direction_vector(cls, v, info):
        if v and hasattr(v, "direction") and v.direction:
            import math

            magnitude = math.sqrt(sum(x**2 for x in v.direction))
            if magnitude == 0:
                raise ValueError("Direction vector cannot be a zero vector")
        return v


class Partner(BaseModel):
    name: str
    binding_probability: float = Field(0.5, ge=0, le=1)
    positions: Optional[List[ThreeFloatArray]] = None
    excluded_names: Optional[List[str]] = None
    probability_repelled: Optional[float] = Field(None, ge=0, le=1)
    weight: Optional[float] = Field(None, ge=0)


class MeshRepresentation(BaseModel):
    path: str
    name: str
    format: str
    coordinate_system: CoordinateSystem = Field(default=CoordinateSystem.LEFT)
    transform: Optional[Dict[str, Any]] = None


class PackingRepresentation(BaseModel):
    path: str
    name: str
    format: str
    radii: Optional[List[List[float]]] = None
    positions: Optional[List[List[ThreeFloatArray]]] = None


class AtomicRepresentation(BaseModel):
    path: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    transform: Optional[Dict[str, Any]] = None


class Representations(BaseModel):
    mesh: Optional[MeshRepresentation] = None
    atomic: Optional[AtomicRepresentation] = None
    packing: Optional[PackingRepresentation] = None


class RecipeObject(BaseModel):
    type: Optional[IngredientType] = None
    inherit: Optional[str] = None
    color: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)

    jitter_attempts: int = Field(5, ge=1)
    max_jitter: ThreeFloatArray = Field([1, 1, 1], min_length=3, max_length=3)
    rotation_range: Optional[float] = Field(None, ge=0)
    rotation_axis: Optional[Union[ThreeFloatArray, None]] = None
    use_rotation_axis: Optional[bool] = None
    principal_vector: Optional[ThreeFloatArray] = Field(
        None, min_length=3, max_length=3
    )
    orient_bias_range: Optional[List[float]] = Field(None, min_length=2, max_length=2)

    packing_mode: PackingMode = Field(PackingMode.RANDOM)
    place_method: PlaceMethod = Field(PlaceMethod.JITTER)
    rejection_threshold: Optional[int] = Field(None, ge=1)
    cutoff_boundary: Optional[float] = Field(None, ge=0)
    cutoff_surface: Optional[float] = Field(None, gt=0)
    perturb_axis_amplitude: Optional[float] = Field(None, ge=0)
    encapsulating_radius: Optional[float] = Field(None, gt=0)
    radius: Optional[float] = Field(None, gt=0)
    available_regions: Optional[Dict[str, Any]] = None
    partners: Optional[List[Partner]] = None
    gradient: Optional[Union[str, List[str]]] = None
    weight: Optional[float] = Field(None, ge=0)
    is_attractor: Optional[bool] = None
    priority: Optional[int] = None

    jitterMax: Optional[ThreeFloatArray] = Field(
        None, min_length=3, max_length=3, alias="jitterMax"
    )
    packing: Optional[Dict[str, Any]] = None

    representations: Optional[Representations] = None

    @field_validator("color")
    @classmethod
    def validate_color_range(cls, v):
        if v is not None:
            for component in v:
                if not (0 <= component <= 1):
                    raise ValueError("Color components must be between 0 and 1")
        return v

    @field_validator("orient_bias_range")
    @classmethod
    def validate_orient_bias_range(cls, v):
        if v is not None and len(v) == 2:
            if v[0] > v[1]:
                raise ValueError("orient_bias_range min must be <= max")
        return v


# COMPOSITION-LEVEL CLASSES
"""
"composition": {
        "bounding_area": {       <= this is a CompositionEntry
            "regions": {
                "interior": [
                    "outer_sphere",    <= this is a string reference to a CompositionEntry
                    {
                        "object": "green_sphere",
                        "count": 5
                    }
                ]
            }
        },
        "outer_sphere": {         <= this is a CompositionEntry
            "object": "large_sphere",
            "count": 1,
            "regions": {      <= this is CompositionRegions
                "interior": [
                    "inner_sphere",
                    {                               <= this is a CompositionItem
                        "object": "red_sphere",      <= CompositionItem.object
                        "count": 40                  <= CompositionItem.count
                    }
                ],
                "surface": [{
                    "object": "green_sphere",
                    "count": 40
                }]
            }
        },
        "inner_sphere": {       <= this is a CompositionEntry
            "object": "medium_sphere",
            "regions": {
                "interior": [
                    {
                        "object": "green_sphere",
                        "count": 20
                    }
                ]
            }
        }
    }
}

All referenced objects must be defined in the objects section.
"""


class CompositionItem(BaseModel):
    object: str
    count: int = Field(5, ge=0)
    priority: Optional[int] = None


class CompositionRegions(BaseModel):
    interior: Optional[List[Union[str, CompositionItem]]] = None
    surface: Optional[List[Union[str, CompositionItem]]] = None
    inner_leaflet: Optional[List[Union[str, CompositionItem]]] = None
    outer_leaflet: Optional[List[Union[str, CompositionItem]]] = None


class CompositionEntry(BaseModel):
    object: Optional[str] = None
    count: Optional[int] = Field(None, ge=0)
    priority: Optional[int] = None
    regions: Optional[CompositionRegions] = None

    @model_validator(mode="after")
    def validate_entry_content(self):
        """validates entry has either object or regions (not both empty)"""
        if not self.object and not self.regions:
            raise ValueError("CompositionEntry must have either 'object' or 'regions'")
        return self


# RECIPE-METADATA-LEVEL
class Recipe(BaseModel):
    name: str
    version: str = Field("1.0.0")
    format_version: str = Field("2.0")
    bounding_box: List[List[float]] = Field([[0, 0, 0], [100, 100, 100]])
    grid_file_path: Optional[str] = None
    objects: Dict[str, RecipeObject] = Field(default_factory=dict)
    gradients: Dict[str, RecipeGradient] = Field(default_factory=dict)
    composition: Dict[str, CompositionEntry] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, value):
        if not value or not value.strip():
            raise ValueError("Recipe name cannot be empty")
        return value

    @field_validator("bounding_box")
    @classmethod
    def validate_bounding_box(cls, v):
        if len(v) != 2:
            raise ValueError("Bounding box must have exactly 2 points [min, max]")
        if len(v[0]) != 3 or len(v[1]) != 3:
            raise ValueError("Bounding box points must be 3D coordinates")

        min_point, max_point = v[0], v[1]
        for i in range(3):
            if min_point[i] >= max_point[i]:
                axis = ["x", "y", "z"][i]
                raise ValueError(f"Bounding box min_{axis} must be < max_{axis}")
        return v

    # CROSS-FIELD VALIDATIONS
    # the "after" model validator runs after all individual fields
    @model_validator(mode="after")
    def validate_object_gradients(self):
        """Validate that object gradients reference existing gradients in the recipe"""
        if hasattr(self, "objects") and self.objects:
            available_gradients = (
                set(self.gradients.keys()) if self.gradients else set()
            )
            for obj_name, obj_data in self.objects.items():
                if hasattr(obj_data, "gradient") and obj_data.gradient is not None:
                    gradient_value = obj_data.gradient
                    # Handle both string and list gradient references
                    gradient_refs = []
                    if isinstance(gradient_value, str):
                        gradient_refs = [gradient_value]
                    elif isinstance(gradient_value, list):
                        gradient_refs = gradient_value
                    # Check that all referenced gradients exist
                    for gradient_ref in gradient_refs:
                        if gradient_ref not in available_gradients:
                            raise ValueError(
                                f"objects.{obj_name}.gradient references '{gradient_ref}' which does not exist in gradients section"
                            )
        return self

    @model_validator(mode="after")
    def validate_gradient_surface_objects(self):
        """Validate that surface gradients reference existing objects"""
        if hasattr(self, "gradients") and self.gradients:
            available_objects = set(self.objects.keys()) if self.objects else set()

            for gradient_name, gradient_data in self.gradients.items():
                if hasattr(gradient_data, "mode") and gradient_data.mode == "surface":
                    if (
                        hasattr(gradient_data, "mode_settings")
                        and gradient_data.mode_settings
                    ):
                        if (
                            hasattr(gradient_data.mode_settings, "object")
                            and gradient_data.mode_settings.object
                        ):
                            if (
                                gradient_data.mode_settings.object
                                not in available_objects
                            ):
                                raise ValueError(
                                    f"gradients.{gradient_name}.mode_settings.object references '{gradient_data.mode_settings.object}' which does not exist in objects section"
                                )
        return self

    @model_validator(mode="after")
    def validate_gradient_combinations(self):
        """Validate gradient combinations in object gradient lists"""
        if hasattr(self, "objects") and self.objects:
            for obj_name, obj_data in self.objects.items():
                if hasattr(obj_data, "gradient") and obj_data.gradient is not None:
                    if isinstance(obj_data.gradient, list):
                        # multiple gradients - validate combination
                        if len(obj_data.gradient) < 2:
                            raise ValueError(
                                f"objects.{obj_name}.gradient: gradient lists must contain at least 2 gradients"
                            )
        return self

    @model_validator(mode="after")
    def validate_object_inheritance(self):
        """Validate that object inherit references point to existing objects in the objects section"""
        if hasattr(self, "objects") and self.objects:
            available_objects = set(self.objects.keys())
            for obj_name, obj_data in self.objects.items():
                if hasattr(obj_data, "inherit") and obj_data.inherit is not None:
                    inherit_ref = obj_data.inherit
                    if inherit_ref not in available_objects:
                        raise ValueError(
                            f"objects.{obj_name}.inherit references '{inherit_ref}' which does not exist in objects section"
                        )
                    # check for self-inheritance
                    if inherit_ref == obj_name:
                        raise ValueError(
                            f"objects.{obj_name}.inherit cannot reference itself"
                        )
        return self

    @model_validator(mode="after")
    def validate_composition_references(self):
        """validates that composition references point to existing composition entries or objects"""
        if hasattr(self, "composition") and self.composition:
            available_composition_entries = set(self.composition.keys())
            available_objects = set(self.objects.keys()) if self.objects else set()

            for comp_name, comp_entry in self.composition.items():

                if hasattr(comp_entry, "regions") and comp_entry.regions:
                    self._validate_regions_references(
                        comp_entry.regions,
                        f"composition.{comp_name}.regions",
                        available_composition_entries,
                        available_objects,
                    )
                if hasattr(comp_entry, "object") and comp_entry.object:
                    if comp_entry.object not in available_objects:
                        raise ValueError(
                            f"composition.{comp_name}.object references '{comp_entry.object}' which does not exist in objects section"
                        )

        return self

    def _validate_regions_references(
        self, regions, path, available_composition_entries, available_objects
    ):
        """validates references in composition regions"""
        for region_name in ["interior", "surface", "inner_leaflet", "outer_leaflet"]:
            region_items = getattr(regions, region_name, None)
            if region_items:
                for i, item in enumerate(region_items):
                    current_path = f"{path}.{region_name}[{i}]"
                    if isinstance(item, str):
                        # str ref - must exist in composition entries
                        if item not in available_composition_entries:
                            raise ValueError(
                                f"{current_path} references '{item}' which does not exist in composition section"
                            )
                    elif isinstance(item, dict) and "object" in item:
                        # CompositionItem.object ref - must exist in objects
                        if item["object"] not in available_objects:
                            raise ValueError(
                                f"{current_path}.object references '{item['object']}' which does not exist in objects section"
                            )
