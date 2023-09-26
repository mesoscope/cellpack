default_recipe_values = {
    "bounding_box": [[0, 0, 0], [100, 100, 100]],
    "representations": {"atomic": None, "packing": None, "mesh": None},
}

DEFAULT_GRADIENT_MODE_SETTINGS = {
    "mode": "X",
    "weight_mode": "linear",
    "pick_mode": "linear",
    "description": "Linear gradient in the X direction",
    "reversed": False,  # is the direction of the vector reversed?
    "invert": False, # is the gradient inverted? (this does weights = 1 - weights)
    "mode_settings": {},
    "weight_mode_settings": {},
}
