from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

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


class CoordinateSystem(str, Enum):
    LEFT = "left"
    RIGHT = "right"


# 3-element float array - used for 3D vectors, colors, etc.
ThreeFloatArray = List[float]


# GRADIENT CLASSES
class GradientMode(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"
    VECTOR = "vector"
    RADIAL = "radial"
    SURFACE = "surface"


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


class ModeOptions(str, Enum):
    """
    All available options for individual modes
    """

    direction = "direction"
    center = "center"
    radius = "radius"
    gblob = "gblob"
    object = "object"
    scale_distance_between = "scale_distance_between"


class InvertOptions(str, Enum):
    """
    All available options for individual invert modes
    """

    weight = "weight"
    distance = "distance"


class WeightModeOptions(str, Enum):
    """
    All available options for individual weight modes
    """

    power = "power"
    decay_length = "decay_length"


REQUIRED_MODE_OPTIONS = {
    GradientMode.VECTOR: [ModeOptions.direction],
    GradientMode.SURFACE: [ModeOptions.object],
}


DIRECTION_MAP = {
    GradientMode.X: [1, 0, 0],
    GradientMode.Y: [0, 1, 0],
    GradientMode.Z: [0, 0, 1],
}


REQUIRED_WEIGHT_MODE_OPTIONS = {
    WeightMode.POWER: [WeightModeOptions.power],
    WeightMode.EXPONENTIAL: [WeightModeOptions.decay_length],
}


# default gradient settings for v2.0 to v2.1 migration
DEFAULT_GRADIENT_MODE_SETTINGS = {
    "mode": "X",
    "weight_mode": "linear",
    "pick_mode": "linear",
    "description": "Linear gradient in the X direction",
    "reversed": False,
    "invert": None,
    "mode_settings": {},
    "weight_mode_settings": {},
}


class WeightModeSettings(BaseModel):
    decay_length: Optional[float] = Field(None, gt=0)
    power: Optional[float] = Field(None, gt=0)


class GradientModeSettings(BaseModel):
    object: Optional[str] = None
    scale_to_next_surface: Optional[bool] = None
    direction: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)
    center: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)
    radius: Optional[float] = Field(None, gt=0)


class RecipeGradient(BaseModel):
    name: Optional[str] = None  # required when gradients are in list format
    description: Optional[str] = None
    mode: GradientMode = Field(GradientMode.X)
    pick_mode: PickMode = Field(PickMode.LINEAR)
    weight_mode: Optional[WeightMode] = None
    reversed: Optional[bool] = None
    invert: Optional[InvertOptions] = None
    weight_mode_settings: Optional[WeightModeSettings] = None
    mode_settings: Optional[GradientModeSettings] = None

    @model_validator(mode="after")
    def validate_mode_requirements(self):
        """Validate that required `mode_settings` exist for modes that need them"""
        required_options = REQUIRED_MODE_OPTIONS.get(self.mode)

        if required_options:
            if not self.mode_settings:
                raise ValueError(
                    f"{self.mode.value} gradient mode requires 'mode_settings' field"
                )

            for option in required_options:
                option_name = option.value if hasattr(option, "value") else option
                if (
                    not hasattr(self.mode_settings, option_name)
                    or getattr(self.mode_settings, option_name) is None
                ):
                    raise ValueError(
                        f"{self.mode.value} gradient mode requires '{option_name}' in mode_settings"
                    )

        # vector mode direction must be non-zero
        if self.mode == GradientMode.VECTOR and self.mode_settings:
            if self.mode_settings.direction:
                import math

                magnitude = math.sqrt(sum(x**2 for x in self.mode_settings.direction))
                if magnitude == 0:
                    raise ValueError(
                        "Vector gradient mode requires a non-zero direction vector"
                    )

        return self

    @model_validator(mode="after")
    def validate_weight_mode_requirements(self):
        """Validate that required `weight_mode_settings` exist for weight modes that need them"""
        if self.weight_mode is None:
            return self

        required_options = REQUIRED_WEIGHT_MODE_OPTIONS.get(self.weight_mode)

        if required_options:
            if not self.weight_mode_settings:
                raise ValueError(
                    f"{self.weight_mode.value} weight mode requires 'weight_mode_settings' field"
                )

            for option in required_options:
                option_name = option.value if hasattr(option, "value") else option
                if (
                    not hasattr(self.weight_mode_settings, option_name)
                    or getattr(self.weight_mode_settings, option_name) is None
                ):
                    raise ValueError(
                        f"{self.weight_mode.value} weight mode requires '{option_name}' in weight_mode_settings"
                    )

        return self


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
    # support both standard format and Firebase dictionary format
    radii: Optional[Union[List[List[float]], Dict[str, Any]]] = None
    positions: Optional[Union[List[List[ThreeFloatArray]], Dict[str, Any]]] = None


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
    partners: Optional[Union[List[Partner], Dict[str, Any]]] = None
    # Gradient field supports multiple formats:
    # - str: Simple reference to gradient name (standard format)
    # - List[str]: List of gradient names (for multiple gradients)
    # - RecipeGradient: Full gradient definition (for unnested Firebase recipes)
    # - List[RecipeGradient]: List of full gradient definitions (for unnested Firebase recipes)
    #
    # Examples:
    # Standard format: "gradient_name"
    # Multiple gradients: ["gradient1", "gradient2"]
    # Unnested Firebase: {"name": "gradient_name", "mode": "surface", ...}
    # Converted Firebase list: [{"name": "grad1", "mode": "X"}, {"name": "grad2", "mode": "Y"}]
    gradient: Optional[
        Union[str, List[str], "RecipeGradient", List["RecipeGradient"]]
    ] = None
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

    @field_validator("partners")
    @classmethod
    def validate_partners_format(cls, v):
        if v is not None:
            # handle Firebase format: {"all_partners": [...]}
            if isinstance(v, dict):
                if "all_partners" in v:
                    # Firebase format is valid - it will be converted later in recipe_loader
                    return v
                else:
                    raise ValueError(
                        "partners dict format must have 'all_partners' key"
                    )
            # handle regular list format: [...], this is the expected converted format, validate individual partners
            elif isinstance(v, list):
                for i, partner in enumerate(v):
                    if isinstance(partner, dict):
                        if "name" not in partner:
                            raise ValueError(f"partners[{i}] must have 'name' field")
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
    gradients: Union[Dict[str, RecipeGradient], List[Dict[str, Any]]] = Field(
        default_factory=dict
    )
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

    @field_validator("gradients")
    @classmethod
    def validate_gradients_format(cls, v):
        if isinstance(v, list):
            for i, gradient in enumerate(v):
                if isinstance(gradient, dict):
                    if "name" not in gradient or not gradient["name"]:
                        raise ValueError(
                            f"gradients[{i}]: List format gradients must have a 'name' field"
                        )
        return v

    # CROSS-FIELD VALIDATIONS
    # the "after" model validator runs after all individual fields
    def _get_gradient_names(self):
        """Helper method to extract gradient names from both dict and list formats"""
        if not self.gradients:
            return set()

        if isinstance(self.gradients, dict):
            return set(self.gradients.keys())
        elif isinstance(self.gradients, list):
            gradient_names = set()
            for gradient in self.gradients:
                if isinstance(gradient, dict) and "name" in gradient:
                    gradient_names.add(gradient["name"])
            return gradient_names
        else:
            return set()

    @model_validator(mode="after")
    def validate_object_gradients(self):
        """Validate that object gradients reference existing gradients in the recipe"""
        if hasattr(self, "objects") and self.objects:
            available_gradients = self._get_gradient_names()
            for obj_name, obj_data in self.objects.items():
                if hasattr(obj_data, "gradient") and obj_data.gradient is not None:
                    gradient_value = obj_data.gradient
                    gradient_refs = []
                    if isinstance(gradient_value, str):
                        # standard format: gradient name string
                        gradient_refs = [gradient_value]
                    elif isinstance(gradient_value, RecipeGradient):
                        # unnested Firebase format: full gradient object
                        # skip validation for embedded gradients - they are self-contained
                        continue
                    elif isinstance(gradient_value, list):
                        # handle list of gradients (either strings or RecipeGradient objects)
                        for item in gradient_value:
                            if isinstance(item, str):
                                gradient_refs.append(item)
                            elif isinstance(item, RecipeGradient):
                                # skip validation for embedded gradients
                                pass
                            else:
                                raise ValueError(
                                    f"objects.{obj_name}.gradient contains invalid item type: {type(item)}"
                                )
                    else:
                        raise ValueError(
                            f"objects.{obj_name}.gradient has invalid type: {type(gradient_value)}"
                        )

                    # check that all referenced gradients exist (only for string references)
                    for gradient_ref in gradient_refs:
                        if gradient_ref not in available_gradients:
                            raise ValueError(
                                f"objects.{obj_name}.gradient references '{gradient_ref}' which does not exist in gradients section"
                            )
        return self

    @model_validator(mode="after")
    def validate_gradient_surface_objects(self):
        """Validate that surface gradients reference existing objects or composition keys"""
        if hasattr(self, "gradients") and self.gradients:
            available_objects = set(self.objects.keys()) if self.objects else set()
            available_composition = (
                set(self.composition.keys()) if self.composition else set()
            )
            gradients_to_check = []
            if isinstance(self.gradients, dict):
                gradients_to_check = list(self.gradients.items())
            elif isinstance(self.gradients, list):
                gradients_to_check = [
                    (g.get("name", f"gradient_{i}"), g)
                    for i, g in enumerate(self.gradients)
                ]

            for gradient_name, gradient_data in gradients_to_check:
                mode = (
                    gradient_data.get("mode")
                    if isinstance(gradient_data, dict)
                    else getattr(gradient_data, "mode", None)
                )

                if mode == "surface":
                    mode_settings = (
                        gradient_data.get("mode_settings")
                        if isinstance(gradient_data, dict)
                        else getattr(gradient_data, "mode_settings", None)
                    )
                    if mode_settings:
                        obj_ref = (
                            mode_settings.get("object")
                            if isinstance(mode_settings, dict)
                            else getattr(mode_settings, "object", None)
                        )
                        if obj_ref and (
                            obj_ref not in available_objects
                            and obj_ref not in available_composition
                        ):
                            raise ValueError(
                                f"gradients.{gradient_name}.mode_settings.object references '{obj_ref}' which does not exist in objects or composition sections"
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
