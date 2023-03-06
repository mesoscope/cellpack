import copy


def convert_partners(object_data):

    partners_list = []
    if "names" not in "partners":
        return partners_list
    for index, name in enumerate(object_data["partners"]["names"]):
        positions = object_data["partners"]["positions"]
        position = [0,0,0]
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
            "binding_probably": binding_probably
        }
        partners_list.append(partner)
    return partners_list

def convert(recipe_data_2_0):
    new_recipe = copy.deepcopy(recipe_data_2_0)
    new_recipe["format_version"] = "2.1"
    for object_name in recipe_data_2_0["objects"]:
        object_data = recipe_data_2_0["objects"][object_name]
        if "partners" in object_data:
            new_partner_data = convert_partners(object_data)
            object_data["partners"] = new_partner_data
            new_recipe["objects"][object_name]["partners"] = new_partner_data
    return new_recipe