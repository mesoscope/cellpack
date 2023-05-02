import copy

from ..interface_objects.gradient_data import GradientData, ModeOptions


def convert_partners(object_data):
    partners_list = []
    if "names" not in "partners":
        return partners_list
    for index, name in enumerate(object_data["partners"]["names"]):
        positions = object_data["partners"]["positions"]
        position = [0, 0, 0]
        if positions and index < len(positions):
            position = positions[index]

        binding_probably = 1.0
        if "probability_binding" in object_data["partners"]:
            binding_probably = object_data["partners"]["probability_binding"]
        if "probability_repelled" in object_data["partners"]:
            binding_probably = -object_data["partners"]["probability_repelled"]

        partner = {
            "name": name,
            "position": position,
            "binding_probably": binding_probably,
        }
        partners_list.append(partner)
    return partners_list


def convert_gradients(old_gradients_dict):
    new_gradients_dict = {}
    for gradient_name, gradient_dict in old_gradients_dict.items():
        gradient_data = copy.deepcopy(GradientData.default_values)

        for key, value in gradient_dict.items():
            if ModeOptions.is_member(key):
                gradient_data["mode_settings"][key] = value
            else:
                gradient_data[key] = value

        new_gradients_dict[gradient_name] = gradient_data
    return new_gradients_dict


def convert(recipe_data_2_0):
    new_recipe = copy.deepcopy(recipe_data_2_0)
    new_recipe["format_version"] = "2.1"
    for object_name in recipe_data_2_0["objects"]:
        object_data = recipe_data_2_0["objects"][object_name]
        if "partners" in object_data:
            new_partner_data = convert_partners(object_data)
            object_data["partners"] = new_partner_data
            new_recipe["objects"][object_name]["partners"] = new_partner_data
        if "gradients" in recipe_data_2_0:
            new_recipe["gradients"] = convert_gradients(recipe_data_2_0["gradients"])
    return new_recipe
