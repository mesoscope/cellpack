"""
Integration tests for the `pack` CLI entry point (`cellpack/bin/pack.py`).

Two input types are covered:

    1. A string file path — the existing local CLI workflow invoked as
        `pack -r RECIPE_PATH -c CONFIG_PATH`. Accepting a recipe dict must not change anything about this
        path.

    2. A json dict — the new flow used by the docker server's
        `pack_handler` when it receives a json body. The dict must flow
        through `RecipeLoader` and the rest of the pipeline remains the same to a
        recipe loaded.

The packing config can be supplied as a file path or omitted entirely, in
which case `ConfigLoader` falls back to its built-in default values.
"""

import json
from pathlib import Path

from cellpack.bin.pack import pack


MINIMAL_RECIPE = {
    "version": "1.0.0",
    "format_version": "2.0",
    "name": "test_pack_cli",
    "bounding_box": [[0, 0, 0], [50, 50, 1]],
    "objects": {
        "sphere_5": {
            "type": "single_sphere",
            "radius": 5,
            "max_jitter": [1, 1, 0],
            "place_method": "jitter",
        }
    },
    "composition": {
        "space": {"regions": {"interior": ["A"]}},
        "A": {"object": "sphere_5", "count": 1},
    },
}


def _write_minimal_config(tmp_path: Path) -> Path:
    config = {
        "name": "test_pack_cli",
        "out": f"{tmp_path}/",
        "place_method": "jitter",
        "inner_grid_method": "raytrace",
        "save_analyze_result": False,
        "save_plot_figures": False,
        "number_of_packings": 1,
        "show_progress_bar": False,
        "load_from_grid_file": False,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


def test_pack_with_recipe_path(tmp_path):
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(MINIMAL_RECIPE))
    config_path = _write_minimal_config(tmp_path)
    pack(recipe=str(recipe_path), config_path=str(config_path))


def test_pack_with_recipe_dict(tmp_path):
    """
    `pack()` also accepts a recipe dict directly, so
    the docker server can forward a parsed JSON body without writing it to
    db first.
    """
    config_path = _write_minimal_config(tmp_path)
    pack(recipe=MINIMAL_RECIPE, config_path=str(config_path))


def test_pack_with_default_config(tmp_path, monkeypatch):
    """Omitting `config_path` falls back to `ConfigLoader.default_values`."""
    # default `out: "out/"` is relative, monkeypatch.chdir keeps outputs inside tmp_path.
    monkeypatch.chdir(tmp_path)
    pack(recipe=MINIMAL_RECIPE)
