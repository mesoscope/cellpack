import os


def create_file_info_object_from_full_path(full_path):
    path, filename = os.path.split(full_path)
    _, extension = os.path.splitext(filename)
    return {
        "path": path,
        "name": filename,
        "format": extension,
    }


def create_output_dir(out_base_folder, recipe_name, sub_dir=None):
    os.makedirs(out_base_folder, exist_ok=True)
    output_folder = os.path.join(out_base_folder, recipe_name)
    if sub_dir is not None:
        output_folder = os.path.join(output_folder, sub_dir)
    os.makedirs(output_folder, exist_ok=True)
    return output_folder
