# Recipe schema v2.0


The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

### Settings
The top-level fields include metadata about the recipe, such as its name, version, and bounding box. It also specifies the file path for grid data.

| Field Path       | Type                                             | Description                        | Default Value                      | Notes                                                                                                                        |
| ---------------- | ------------------------------------------------ | ---------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `name`           | string                                           | Name of the recipe                 |                                    |                                                                                                                              |
| `version`        | string                                           | Recipe version string              | "default"                          | Version of the recipe is appended to the output file name.                                                                   |
| `format_version` | string                                           | Schema format version              | "1.0"                              | Older recipe formats do not have this field. Recipes are automatically migrated to the latest format version before packing. |
| `bounding_box`   | array `[[minX, minY, minZ], [maxX, maxY, maxZ]]` | Bounding box of the packing result | `[[ 0, 0, 0 ], [ 100, 100, 100 ]]` |                                                                                                                              |
| `grid_file_path` | string                                           | File path to read/write grid data  |                                    | If not specified, a grid file is created and stored at the output path.                                                      |

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
    ...[OTHER_SETTINGS],
}
```


### Recipe.objects
This section contains information about the objects to be packed, including their types, colors, sizes, and packing methods. Each object can inherit properties from another object.

| Field Path                               | Type                                    | Description                                                  | Default Value   | Notes                                                                                                                                                    |
| ---------------------------------------- | --------------------------------------- | ------------------------------------------------------------ | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `color`                                  | array (RGB 0–1) `[float, float, float]` | RGB color of object                                          |                 |                                                                                                                                                          |
| `type`                                   | string (enum)                           | Object type                                                  | `single_sphere` | Accepts a type from `"single_sphere"`, `"multi_sphere"`, `"single_cube"`, `"single_cylinder"`, `"multi_cylinder"`, `"grow"`, `mesh`                      |
| `inherit`                                | string                                  | Linked name of the inherited object                          |                 | Defined by the object. Must exist in `objects`                                                                                                           |
| `radius`                                 | number                                  | Object radius                                                |                 |                                                                                                                                                          |
| `jitter_attempts`                        | number                                  | Max retries for packing                                      | 5               |                                                                                                                                                          |
| `max_jitter`                             | array (0–1 per axis)                    | Vector with maximum jitter distance in units of grid spacing | [1, 1, 1]       |                                                                                                                                                          |
| `place_method`                           | string(enum)                            | Method used for packing the object                           | `jitter`        | Accepts a method from `jitter`, `spheresSST`. Can be overwritten by a global config.                                                                     |
| `available_regions`                      | array                                   | Regions where the object can be placed                       |                 | e.g. `interior`, `surface`, `outer_leaflet`, `inner_leaflet`                                                                                             |
| `packing_mode`                           | string(enum)                            | Packing behavior mode                                        | `random`        | Tied to the recipe. Accepts a packing mode from `random`, `close`, `closePartner`, `randomPartner`, `gradient`, `hexatile`, `squaretile`, `triangletile` |
| `gradient`                               | string or list of strings               | Gradient(s) applied to object                                |                 | Must exist in `gradients`                                                                                                                                |
| `representations.mesh.path`              | string                                  | Mesh file path                                               |                 |                                                                                                                                                          |
| `representations.mesh.name`              | string                                  | Mesh file name                                               |                 | Tied to the object                                                                                                                                       |
| `representations.mesh.format`            | string                                  | Mesh file format                                             |                 | Tied to the object                                                                                                                                       |
| `representations.mesh.coordinate_system` | string (`left` or `right`)              | Depends on generating software                               | `left`          |                                                                                                                                                          |
| `partners.names`                         | array(string[])                         | List of partner object names                                 |                 | Objects that attract to this one, must exist in `objects`                                                                                                |
| `partners.probability_binding`           | number (0–1)                            | Probability of binding with partners                         | 0.5             |                                                                                                                                                          |
| `partners.positions`                     | array                                   | Partner relative positions                                   |                 | Relative positions for partner placement                                                                                                                 |
| `partners.excluded_names`                | array(string[])                         | List of excluded partner objects                             |                 | Objects that repel from this one                                                                                                                         |
| `partners.probability_repelled`          | number (0–1)                            | Probability of repulsion from excluded partners              |                 |                                                                                                                                                          |
| `partners.weight`                        | number                                  | Weight factor for partner interactions                       | 0.2             | Influence strength of partner effects                                                                                                                    |

**Example:**
```JSON
...[OTHER_SETTINGS],
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



### Recipe.gradients


| Field Path                            | Type              | Description                                         | Default Value | Notes                                                                                             |
| ------------------------------------- | ----------------- | --------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------- |
| `description`                         | string            | Description of gradient                             |               |                                                                                                   |
| `mode`                                | string(enum)      | Type of gradient                                    | "X"           | Defined by gradient. Accepts a mode from `"x"`, `"y"`, `"z"`, `"vector"`, `"radial"`, `"surface"` |
| `pick_mode`                           | string(enum)      | Gradient sampling method                            | `"linear"`    | Accepts a pick mode from `"max"`, `"min"`, `"rnd"`, `"linear"`, `"binary"`, `"sub"`, `"reg"`      |
| `weight_mode`                         | string(enum)      | Modulates the form of the grid point weight dropoff |               | Accepts a weight mode from `"linear"`, `"square"`, `"cube"`, `"power"`, `"exponential"`           |
| `reversed`                            | boolean           | Reverse gradient direction                          |               |                                                                                                   |
| `invert`                              | boolean           | Invert gradient weights                             |               |                                                                                                   |
| `weight_mode_settings.decay_length`   | number            | Decay rate parameter                                |               | Controls gradient falloff                                                                         |
| `mode_settings.object`                | string            | Reference object for gradient                       |               | Links to a mesh object                                                                            |
| `mode_settings.scale_to_next_surface` | boolean           | Scaling toggle                                      |               |                                                                                                   |
| `mode_settings.direction`             | array `[x, y, z]` | Direction vector for mode                           |               | Defined by the mode                                                                               |
| `mode_settings.center`                | array `[x, y, z]` | Center point for the gradient                       |               | Used as the origin for radial or directional gradients, defined by the mode                       |


**Example:**
```JSON
...[OTHER_SETTINGS],
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

### Recipe.composition

The composition section defines the hierarchical structure of containers and their contents. It establishes parent-child relationships between objects and specifies which objects are placed within different regions.

| Field Path              | Type                   | Description                                | Default Value | Notes                                          |
| ----------------------- | ---------------------- | ------------------------------------------ | ------------- | ---------------------------------------------- |
| `id`                    | string (unique)        | Unique identifier for the composition item |               | Must be unique within composition              |
| `object`                | string                 | Linked object name                         |               | Must exist in `objects`                        |
| `count`                 | number (integers >= 0) | Number of objects                          | 5             | Falls back to definition in the object section |
| `priority`              | number                 | Packing priority                           |               | e.g. -1                                        |
| `regions.interior`      | array                  | Interior contents of object                |               |                                                |
| `regions.surface`       | array                  | Surface contents of object                 |               | Objects placed on the surface                  |
| `regions.inner-leaflet` | array                  | Inner leaflet contents                     |               | Objects placed on inner leaflet                |
| `regions.outer-leaflet` | array                  | Outer leaflet contents                     |               | Objects placed on outer leaflet                |

**Example:**
```JSON
...[OTHER_SETTINGS],
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
