from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# note: ge(>=), le(<=), gt(>), lt(<)


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


class GradientModeSettings(BaseModel):
    object: Optional[str] = None
    scale_to_next_surface: Optional[bool] = None
    direction: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)
    center: Optional[ThreeFloatArray] = Field(None, min_length=3, max_length=3)


class Gradient(BaseModel):
    description: Optional[str] = None
    mode: GradientMode = Field(GradientMode.X)
    pick_mode: PickMode = Field(PickMode.LINEAR)
    weight_mode: Optional[WeightMode] = None
    reversed: Optional[bool] = None
    invert: Optional[bool] = None
    weight_mode_settings: Optional[WeightModeSettings] = None
    mode_settings: Optional[GradientModeSettings] = None


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


class Partner(BaseModel):
    names: Optional[List[str]] = None
    probability_binding: float = Field(0.5, ge=0, le=1)
    positions: Optional[List[ThreeFloatArray]] = None
    excluded_names: Optional[List[str]] = None
    probability_repelled: Optional[float] = Field(None, ge=0, le=1)
    weight: float = Field(0.2, ge=0)


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


class BaseRecipeObject(BaseModel):
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

    partners: Optional[Partner] = None
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

    @field_validator("gradient")
    @classmethod
    def validate_gradient(cls, v):
        allowed_gradients = ["nucleus_gradient", "membrane_gradient", "struct_gradient"]
        if v is not None:
            if isinstance(v, str):
                if v not in allowed_gradients:
                    raise ValueError(f"gradient must be one of {allowed_gradients}")
            elif isinstance(v, list):
                for gradient in v:
                    if gradient not in allowed_gradients:
                        raise ValueError(f"gradient must be one of {allowed_gradients}")
        return v


# TODO: check the requirement for specific object types(SingleSphereObject, MultiSphereObject, MeshObject)

RecipeObject = Union[BaseRecipeObject]


class Recipe(BaseModel):
    name: str
    version: str = Field("default")
    format_version: str = Field("1.0")
    bounding_box: List[List[float]] = Field([[0, 0, 0], [100, 100, 100]])
    grid_file_path: Optional[str] = None
    objects: Dict[str, RecipeObject] = Field(default_factory=dict)
    gradients: Dict[str, Gradient] = Field(default_factory=dict)
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

    # TODO make the validation error messages more readable
