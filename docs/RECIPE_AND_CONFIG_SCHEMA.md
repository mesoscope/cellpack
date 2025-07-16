# cellPACK Recipe and Config Schema
### Version 2.0

This document provides a schema for cellPACK recipes and configurations.


## Recipe

The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

### Metadata section
The top-level fields  include metadata about the recipe, such as its name, version, and bounding box. It also specifies the file path for grid data.

| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `name` | string | Name of the recipe | Yes | | |
| `version` | string | Recipe version string | No | "default" | Version of the recipe is appended to the output file name. |
| `format_version` | string | Schema format version | No | "1.0" | Older recipe formats do not have this field. Recipes are automatically migrated to the latest format version before packing.|
| `bounding_box` | array `[[minX, minY, minZ], [maxX, maxY, maxZ]]` | Bounding box of the packing result | No | `[[ 0, 0, 0 ], [ 100, 100, 100 ]]` | |
| `grid_file_path` | string | File path to read/write grid data | No | | If not specified, a grid file is created and stored at the output path. |

**Example:**
```JSON
{
    "name": "one_sphere",
    "version": "1.0.0",
    "format_version": "2.0",
    "bounding_box": [
        [
            0,
            0,
            0
        ],
        [
            20,
            20,
            20
        ]
    ],
    "grid_file_path": "/path/to/local/file" // optional
    ...
}
```


### Objects Section
This section contains information about the objects to be packed, including their types, colors, sizes, and packing methods. Each object can inherit properties from another object.

| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `color` | array (RGB 0–1) `[float, float, float]` | RGB color of object | No | | |
| `type` | string (enum) | Object type | Yes | `single_sphere` | Accepts a type from `"single_sphere"`, `"multi_sphere"`, `"single_cube"`, `"single_cylinder"`, `"multi_cylinder"`, `"grow"`, `mesh` |
| `inherit` | string | Linked name of the inherited object | No | | Defined by the object. Must exist in `objects` |
| `radius` | number | Object radius | Yes | |  |
| `jitter_attempts` | number | Max retries for packing | No | 5 | | 
| `max_jitter` | array (0–1 per axis) | Vector with maximum jitter distance in units of grid spacing | No | [1, 1, 1] | |
| `place_method` | string(enum) | Method used for packing the object | No | `jitter` | Accepts a method from `jitter`, `spheresSST`. Can be overwritten by a global config. |
| `available_regions` | array | Regions where the object can be placed | | |e.g. `interior`, `surface`, `outer_leaflet`, `inner_leaflet` |
| `packing_mode` | string(enum) | Packing behavior mode | No | `random` | Tied to the recipe. Accepts a packing mode from `random`, `close`, `closePartner`, `randomPartner`, `gradient`, `hexatile`, `squaretile`, `triangletile` |
| `gradient` | string or list of strings | Gradient(s) applied to object | No | | Must exist in `gradients` |
| `representations.mesh.path` | string | Mesh file path | No | | |
| `representations.mesh.name` | string | Mesh file name | No | | Tied to the object |
| `representations.mesh.format` | string | Mesh file format | No | | Tied to the object |
| `representations.mesh.coordinate_system` | string (`left` or `right`) | Depends on generating software | No | `left` | |
| `partners.names` | array(string[]) | List of partner object names | No | | Objects that attract to this one, must exist in `objects`|
| `partners.probability_binding` | number (0–1) | Probability of binding with partners | No | 0.5 | |
| `partners.positions` | array | Partner relative positions | No | | Relative positions for partner placement |
| `partners.excluded_names` | array(string[]) | List of excluded partner objects | No | | Objects that repel from this one |
| `partners.probability_repelled` | number (0–1) | Probability of repulsion from excluded partners | No | | |
| `partners.weight` | number | Weight factor for partner interactions | No | 0.2 | Influence strength of partner effects |

**Example:**
```
"objects": {
    "base": {
        "jitter_attempts": 10,
        "rotation_range": 6.2831,
        "cutoff_boundary": 0,
        "max_jitter": [
            0.2,
            0.2,
            0.01
        ],
        "perturb_axis_amplitude": 0.1,
        "packing_mode": "random",
        "principal_vector": [
            0,
            0,
            1
        ],
        "rejection_threshold": 50,
        "place_method": "spheresSST",
        "cutoff_surface": 42,
        "rotation_axis": [
            0,
            0,
            1
        ],
        "available_regions": {
            "interior": {},
            "surface": {},
            "outer_leaflet": {},
            "inner_leaflet": {}
        }
    },
    "sphere_25": {
        "type": "single_sphere",
        "inherit": "base",
        "color": [
            0.5,
            0.5,
            0.5
        ],
        "radius": 5,
        "max_jitter": [
            1,
            1,
            0
        ],
        "representations": {
            "mesh": {
                "path": "path/to/local/folder/",
                "name": "mesh.obj",
                "format": "obj"
            }
        }
    }
}
```



### Gradients Section


| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `description` | string | Description of gradient | No | | |
| `mode` | string(enum) | Type of gradient | No | "X" | Defined by gradient. Accepts a mode from `"x"`, `"y"`, `"z"`, `"vector"`, `"radial"`, `"surface"` |
| `pick_mode` | string(enum) | Gradient sampling method | No | `"linear"`| Accepts a pick mode from `"max"`, `"min"`, `"rnd"`, `"linear"`, `"binary"`, `"sub"`, `"reg"` |
| `weight_mode` | string(enum) | Modulates the form of the grid point weight dropoff | Yes | | Accepts a weight mode from `"linear"`, `"square"`, `"cube"`, `"power"`, `"exponential"` |
| `reversed` | boolean | Reverse gradient direction | No | | |
| `invert` | boolean | Invert gradient weights | No | |  |
| `weight_mode_settings.decay_length` | number | Decay rate parameter | No | | Controls gradient falloff |
| `mode_settings.object` | string | Reference object for gradient | No | | Links to a mesh object |
| `mode_settings.scale_to_next_surface` | boolean | Scaling toggle | No | | |
| `mode_settings.direction` | array `[x, y, z]` | Direction vector for mode | No | | Defined by the mode |
| `mode_settings.center` | array `[x, y, z]` | Center point for the gradient | No | | Used as the origin for radial or directional gradients, defined by the mode |


**Example:**
```
"gradients": {
    "nucleus_gradient": {
        "description": "gradient based on distance from the surface of the nucleus mesh",
        "mode": "surface",
        "mode_settings": {
            "object": "nucleus",
            "scale_to_next_surface": false
        },
        "weight_mode": "exponential",
        "weight_mode_settings": {
            "decay_length": 0.1
        }
    }
}
```

### Composition

The composition section defines the hierarchical structure of containers and their contents. It establishes parent-child relationships between objects and specifies which objects are placed within different regions.

| Field Path | Type | Description | Required | Default Value |  Notes |
|------------|------|-------------|----------|-----|-------|
| `id` | string (unique) | Unique identifier for the composition item | Yes | | Must be unique within composition |
| `object` | string | Linked object name | No | | Must exist in `objects` |
| `count` | number (integers >= 0) | Number of objects | Yes | 5 | Falls back to definition in the object section|
| `priority` | number | Packing priority | No | | e.g. -1 |
| `regions.interior` | array | Interior contents of object | No | | |
| `regions.surface` | array | Surface contents of object | No | | Objects placed on the surface |
| `regions.inner-leaflet` | array | Inner leaflet contents | No | | Objects placed on inner leaflet |
| `regions.outer-leaflet` | array | Outer leaflet contents | No | | Objects placed on outer leaflet |

**Example:**
```
"composition": {
    "bounding_area": {
        "regions": {
            "interior": [
                "outer_sphere",
                {
                    "object": "green_sphere",
                    "count": 5
                }
            ]
        }
    },
    "outer_sphere": {
        "object": "large_sphere",
        "count": 1,
        "regions": {
            "interior": [
                "inner_sphere",
                {
                    "object": "red_sphere",
                    "count": 40
                }
            ],
            "surface": [{
                "object": "green_sphere",
                "count": 40
            }]
        }
    },
    "inner_sphere": {
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
```

## Config

The config file controls the packing behavior. It specifies parameters such as packing algorithms, output formats, performance settings, and debugging options that don't affect the biological content but control how the simulation is executed.

| Field Path | Type | Description | Default Value | Notes |
|------------|------|-------------|---------------|-------|
| `clean_grid_cache` | boolean | Clear cached grid before packing | False |  |
| `format` | string | Output format | simularium |  |
| `inner_grid_method` | string | Method used to create the inner grid | trimesh | e.g., `trimesh`, `raytrace` |
| `live_packing` | boolean | Enable real-time packing visualization | False | Not implemented currently |
| `load_from_grid_file` | boolean | Load objects from a grid file | False | |
| `name` | string | Name of the config | default | Used to identify this config run |
| `number_of_packings` | number (>=1) | Number of independent packing replicates | 1 | |
| `open_results_in_browser` | boolean | Open results in browser after run | True |  |
| `ordered_packing` | boolean | Use deterministic packing order | False |  |
| `out` | string | Output directory path | `"out/"` |  |
| `overwrite_place_method` | boolean | Override object-specific place methods | False |  |
| `parallel` | boolean | Enable parallel packing | False | |
| `place_method` | string | Default packing method | spheresSST | e.g., `jitter`, `spheresSST` |
| `randomness_seed` | number | Random seed value | None | Helps reproduce packing runs |
| `save_analyze_result` | boolean | Save packing analysis result | False | Saves additional data and figures from packing. |
| `save_converted_recipe` | boolean | Export converted recipe | False | Save recipe converted from older to newer versions.  |
| `save_gradient_data_as_image` | boolean | Save gradient values as image | False | |
| `save_plot_figures` | boolean | Save analysis figures | |  |
| `show_grid_plot` | boolean | Display grid visualization | False |  |
| `show_progress_bar` | boolean | Show progress bar in terminal | False | |
| `show_sphere_trees` | boolean | Visualize sphere trees | False | |
| `spacing` | number | Override object spacing | None |  |
| `upload_results` | boolean | Upload results to S3 | True | |
| `use_periodicity` | boolean | Enable periodic boundary conditions | False | |
| `version` | number | Config version number | 1.0 | For internal tracking |
| `image_export_options.hollow` | boolean | Export hollow images | False | |
| `image_export_options.projection_axis` | string | Camera position for projection axis | `z` | e.g., `x`, `y`, `z` |
| `image_export_options.voxel_size` | array `[x, y, z]` | Voxel size for image export | | `[1, 1, 1]` | |

**Example:**
```
{
    "name": "example",
    "out": "path/to/output/folder",
    "save_analyze_result": true,
    "show_progress_bar": true,
    "save_plot_figures": false,
    "load_from_grid_file": true,
    "spacing": 2,
    "image_export_options": {
        "hollow": false,
        "voxel_size": [
            1,
            1,
            1
        ],
        "projection_axis": "z"
    },
    "open_results_in_browser": false,
    "upload_results": false
}
```