from cellpack.autopack.interface_objects.ingredient_types import INGREDIENT_TYPE

v1_to_v2_name_map = {
    "Type": "type",
    "distExpression": "distance_expression",
    "distFunction": "distance_function",
    "isAttractor": "is_attractor",
    "jitterMax": "max_jitter",
    "nbJitter": "jitter_attempts",
    "nbMol": "count",
    "overwrite_distFunc": "overwrite_distance_function",
    "packingMode": "packing_mode",
    "packingPriority": "priority",
    "perturbAxisAmplitude": "perturb_axis_amplitude",
    "placeType": "place_method",
    "principalVector": "principal_vector",
    "rejectionThreshold": "rejection_threshold",
    "rotAxis": "rotation_axis",
    "rotRange": "rotation_range",
    "useRotAxis": "use_rotation_axis",
}

unused_attributes_list = [
    "encapsulatingRadius",
    "meshObject",
    "meshType",
    "name",
    "properties",
]

convert_to_partners_map = {
    "partners_name": "names",
    "partners_position": "positions",
    "partners_weight": "weight",
    "proba_binding": "probability_binding",
    "proba_not_binding": "probability_repelled",
    "excluded_partners_name": "excluded_names",
}

attributes_move_to_composition = [
    "count",
    "molarity",
    "priority",
]


required_attributes = {
    "SingleSphere": ["radii"],
    "MultiSphere": ["sphereFile"],
    "SingleCylinder": [],
    "mesh": [],
}

ingredient_types_map = {
    "SingleSphere": INGREDIENT_TYPE.SINGLE_SPHERE,
    "MultiSphere": INGREDIENT_TYPE.MULTI_SPHERE,
    "SingleCube": INGREDIENT_TYPE.SINGLE_CUBE,
    "SingleCylinder": INGREDIENT_TYPE.SINGLE_CYLINDER,
    "MultiCylinder": INGREDIENT_TYPE.MULTI_CYLINDER,
    "Grow": INGREDIENT_TYPE.GROW,
    "mesh": INGREDIENT_TYPE.MESH,
}
