import datetime
import os
import json
from pathlib import Path


def handle_positions(input_positions):
    positions = []
    if isinstance(input_positions, list) and isinstance(input_positions[0], int):
        for i in range(0, len(input_positions), 3):
            positions.append(input_positions[i : i + 3])
    elif (
        input_positions[0] is not None
        and isinstance(input_positions[0], dict)
        and input_positions[0]["coords"] is not None
    ):
        for i in range(0, len(input_positions[0]["coords"]), 3):
            positions.append(input_positions[0]["coords"][i : i + 3])
    return [positions]


def handle_radii(input_radii):
    radii = []
    # is just a list of radii
    if isinstance(input_radii, list) and isinstance(input_radii[0], int):
        radii = input_radii
    # is a list of dicts with radii
    elif input_radii[0] is not None and isinstance(input_radii[0], dict):
        obj = input_radii[0]
        radii = obj["radii"]
    return [radii]


def unpack_mesh_data(data):
    positions = data["verts"]
    faces = data["faces"]
    normals = data["normals"]

    return {
        "name": "direct_mesh" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "format": ".raw",
        "path": "default",
        "file": {
            "verts": positions,
            "faces": faces,
            "normals": normals,
        },
    }


def handle_mesh_file(data):

    if (
        data["verts"] is not None
        and data["faces"] is not None
        and data["normals"] is not None
    ):
        return unpack_mesh_data(data)
    else:
        return create_file_info_object_from_full_path(data["path"])


def create_file_info_object_from_full_path(full_path):
    path, filename = os.path.split(full_path)
    _, extension = os.path.splitext(filename)
    if "autoPACKserver" in path:
        path = path.replace("autoPACKserver/", "github:")
    return {
        "path": path,
        "name": filename,
        "format": extension,
    }


def create_output_dir(out_base_folder, recipe_name, sub_dir=None):
    os.makedirs(out_base_folder, exist_ok=True)
    output_folder = Path(out_base_folder, recipe_name)
    if sub_dir is not None:
        output_folder = Path(output_folder, sub_dir)
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def read_json_file(path):
    if not Path(path).exists():
        return None
    with open(path, "r") as file_name:
        return json.load(file_name)


def write_json_file(path, data):
    Path(path).parent.mkdir(exist_ok=True, parents=True)
    with open(path, "w") as file_name:
        json.dump(data, file_name)
