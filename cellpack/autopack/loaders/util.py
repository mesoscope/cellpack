import os


def create_file_info_object_from_full_path(full_path):
    path, filename = os.path.split(full_path)
    _, extension = os.path.splitext(filename)
    return {
        "path": path,
        "name": filename,
        "format": extension,
    }
