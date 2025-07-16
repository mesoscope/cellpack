# cellPACK Recipe and Config Schema

Version: 2.0


## Recipe

The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

markdown
# cellPACK Recipe and Config Schema 2.0


## Recipe

The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

### Top-Level Fields

| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `name` | string (unique) | Name of the recipe | Yes | | If missing, an automatic version number will be appended. |
| `version` | string | Recipe version string | Yes | 1.0 | |
| `format_version` | string | Schema format version | No? | |  |
| `bounding_box` | array `[[minX, minY, minZ], [maxX, maxY, maxZ]]` | Bounding box of the packing result | Yes |  | |
| `grid_file_path` | string | Grid data file path | No | | Managed by backend |


### Objects Section


| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `color` | array (RGB 0–1) | RGB color of object | No | | `[number, number, number]` |
| `type` | string (enum) | Object type | Yes | `single_sphere` | Accepts a type from `"single_sphere"`, `"multi_sphere"`, `"single_cube"`, `"single_cylinder"`, `"multi_cylinder"`, `"grow"`, `mesh` |
| `inherit` | string | Linked name of the inherited object | No | | Defined by the object. Must exist in `objects` |
| `radius` | number | Object radius | No | 5 |  |
| `jitter_attempts` | number | Max retries for packing | Yes | 5 | | 
| `max_jitter` | array (0–1 per axis) | Vector with maximum jitter distance in units of grid spacing | No | [1, 1, 1] | |
| `place_method` | string(enum) | Method used for packing the object | No | `jitter` | Accepts a method from `jitter`, `spheresSST` |
| `available_regions` | array | Regions where the object can be placed | | |e.g. `interior`, `surface`, `outer_leaflet`, `inner_leaflet` |
| `packing_mode` | string(enum) | Packing behavior mode | No | `random` | Tied to the recipe. Accepts a packing mode from `random`, `close`, `closePartner`, `randomPartner`, `gradient`, `hexatile`, `squaretile`, `triangletile` |
| `gradient` | string | Linked gradient name | No | | Must exist in `gradients` |
| `representations.mesh.path` | string | Mesh file path | No | | Managed backend |
| `representations.mesh.name` | string | Mesh filename | No | | Tied to the object |
| `representations.mesh.format` | string | Mesh file format | No | | Tied to the object |
| `representations.mesh.coordinate_system` | string (`left` or `right`) | Depend on generating software | No | `left` | |
| `partners.names` | array(string[]) | List of partner object names | No | | Objects that attract to this one, must exist in `objects`|
| `partners.probability_binding` | number (0–1) | Probability of binding with partners | No | 0.5 | |
| `partners.positions` | array | Partner relative positions | No | | Relative positions for partner placement |
| `partners.excluded_names` | array(string[]) | List of excluded partner objects | No | | Objects that repel from this one |
| `partners.probability_repelled` | number (0–1) | Probability of repulsion from excluded partners | No | | |
| `partners.weight` | number | Weight factor for partner interactions | No | 0.2 | Influence strength of partner effects |



### Gradients Section


| Field Path | Type | Description | Required | Default Value | Notes |
|------------|------|-------------|----------|-----|-------|
| `description` | string | Description of gradient | No | | For user clarity |
| `mode` | string(enum) | Gradient method | Yes | | Defined by gradient. Accepts a mode from `"x"`, `"y"`, `"z"`, `"vector"`, `"radial"`, `"surface"` |
| `pick_mode` | string(enum) | Gradient sampling method | Yes | | Accepts a pick mode from `"max"`, `"min"`, `"rnd"`, `"linear"`, `"binary"`, `"sub"`, `"reg"` |
| `weight_mode` | string(enum) | Gradient weighting function | Yes | | Accepts a weight mode from `"linear"`, `"square"`, `"cube"`, `"power"`, `"exponential"` |
| `reversed` | boolean | Reverse gradient direction | No | | |
| `invert` | boolean | Invert gradient values | No | |  |
| `weight_mode_settings.decay_length` | number | Decay rate parameter | No | | Controls gradient falloff |
| `mode_settings.object` | string | Reference object | No | | Links to a mesh object |
| `mode_settings.scale_to_next_surface` | boolean | Scaling toggle | No | | |
| `mode_settings.direction` | array `[x, y, z]` | Direction vector for mode | No | | Defined by the mode |
| `mode_settings.center` | array `[x, y, z]` | Center point for the gradient | No | | Used as the origin for radial or directional gradients, defined by the mode |




### Composition

The composition section defines the hierarchical structure of containers and their contents. It establishes parent-child relationships between objects and specifies which objects are placed within different cellular regions.

| Field Path | Type | Description | Required | Default Value |  Notes |
|------------|------|-------------|----------|-----|-------|
| `id` | string (unique) | Unique identifier for the composition item | Yes | | Must be unique within composition |
| `object` | string | Linked object name | No | | Must exist in `objects` |
| `count` | number (integers >= 0) | Number of objects | No | 5? | Range? Validation depending on the object type? e.g. `nucleus`|
| `priority` | number | Packing priority | No | | e.g. -1 |
| `regions.interior` | array | Interior contents of object | No | | Validation? e.g. `peroxisome` can't be placed inside `nucleus` |
| `regions.surface` | array | Surface contents of object | No | | Objects placed on the surface |
| `regions.inner-leaflet` | array | Inner leaflet contents | No | | Objects placed on inner leaflet |
| `regions.outer-leaflet` | array | Outer leaflet contents | No | | Objects placed on outer leaflet |






## Config

The config file controls the packing behavior. It specifies parameters such as packing algorithms, output formats, performance settings, and debugging options that don't affect the biological content but control how the simulation is executed.

| Field Path | Type | Description | Default Value | Notes |
|------------|------|-------------|---------------|-------|
| `clean_grid_cache` | boolean | Clear cached grid before packing | False |  |
| `format` | string | Output format | simularium |  |
| `inner_grid_method` | string | Method used to create the inner grid | trimesh | e.g., `trimesh`, `raytrace` |
| `live_packing` | boolean | Enable real-time packing visualization | False |  |
| `load_from_grid_file` | boolean | Load objects from a grid file | False | |
| `name` | string | Name of the config | default | Used to identify this config run |
| `number_of_packings` | number (>=1) | Number of independent packing runs | 1 | |
| `open_results_in_browser` | boolean | Open results in browser after run | True |  |
| `ordered_packing` | boolean | Use deterministic packing order | False |  |
| `out` | string | Output directory path | out/ |  |
| `overwrite_place_method` | boolean | Override object-specific place methods | False |  |
| `parallel` | boolean | Enable parallel packing | False | |
| `place_method` | string | Default packing method | spheresSST | e.g., `jitter`, `spheresSST` |
| `randomness_seed` | number | Random seed value | None |  |
| `save_analyze_result` | boolean | Save packing analysis result | False |  |
| `save_converted_recipe` | boolean | Export converted recipe | False | Save recipe that converted from v1 to v2  |
| `save_gradient_data_as_image` | boolean | Save gradient values as image | False | |
| `save_plot_figures` | boolean | Save analysis figures | |  |
| `show_grid_plot` | boolean | Display grid visualization | False |  |
| `show_progress_bar` | boolean | Show progress bar in terminal | False | |
| `show_sphere_trees` | boolean | Visualize sphere trees | False | |
| `spacing` | number | Override object spacing | None |  |
| `upload_results` | boolean | Upload results to S3 | True | |
| `use_periodicity` | boolean | Enable periodic boundary conditions | False | |
| `version` | number | Config version number | 1.0 | For internal tracking |
| `image_export_options.hollow` | boolean | Export hollow images | | |
| `image_export_options.projection_axis` | string | Image projection axis | | e.g., `x`, `y`, `z` |
| `image_export_options.voxel_size` | array `[x, y, z]` | Voxel size for image export | | |