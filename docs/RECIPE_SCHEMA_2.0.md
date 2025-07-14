# cellPACK Recipe and Config Schema 2.0


## Recipe

The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

### Top-Level Fields

| Field Path | Type | Description | Required | Editable | Default Value | Notes |
|------------|------|-------------|----------|----------|-----|-------|
| `name` | string (unique) | Name of the recipe | Yes | Yes | | If missing, an automatic version number will be appended. |
| `version` | string | Recipe version string | Yes | No | 1.0 | |
| `format_version` | string | Schema format version | No? | No | |  |
| `bounding_box` | array `[[minX, minY, minZ], [maxX, maxY, maxZ]]` | Bounding box of the packing result | Yes | No |  | |
| `grid_file_path` | string | Grid data file path | No | No | | Managed by backend. Local file support may be added in the future. |


### Objects Section


| Field Path | Type | Description | Required | Editable | Default Value | Notes |
|------------|------|-------------|----------|----------|-----|-------|
| `color` | array (RGB 0–1) | RGB color of object | No | Yes | | `[number, number, number]` |
| `type` | string (enum) | Object type | Yes | No | | Accepts a type from `SINGLE_SPHERE`, `MULTI_SPHERE`, `SINGLE_CUBE`, `SINGLE_CYLINDER`, `MULTI_CYLINDER`, `GROW`, `MESH` |
| `inherit` | string | Linked name of the inherited object | No | No | | Defined by the object. Must exist in `objects` |
| `radius` | number | Object radius | No | Yes | 5 |  |
| `jitter_attempts` | number | Max retries for packing | Yes | Yes | 5 | | 
| `max_jitter` | array (0–1 per axis) | Vector with maximum jitter distance in units of grid spacing | No | Yes | [1, 1, 1] | |
| `place_method` | string(enum) | Method used for packing the object | No | Yes | `jitter` | Accepts a method from `jitter`, `spheresSST` |
| `available_regions` | array | Regions where the object can be placed | | No | |e.g. `interior`, `surface`, `outer_leaflet`, `inner_leaflet` |
| `packing_mode` | string(enum) | Packing behavior mode | No | No | `random` | Tied to the recipe. Accepts a packing mode from `random`, `close`, `closePartner`, `randomPartner`, `gradient`, `hexatile`, `squaretile`, `triangletile` |
| `gradient` | string | Linked gradient name | No | Yes | | Must exist in `gradients` |
| `representations.mesh.path` | string | Mesh file path | No | No | | Managed backend |
| `representations.mesh.name` | string | Mesh filename | No | No | | Tied to the object |
| `representations.mesh.format` | string | Mesh file format | No | No | | Tied to the object |
| `representations.mesh.coordinate_system` | string ('left' or 'right') | 'left' or 'right' depending on generating software | No | No | left | |
| `partners.names` | array(string[]) | List of partner object names | No | Yes | | Objects that attract to this one, must exist in `objects`|
| `partners.probability_binding` | number (0–1) | Probability of binding with partners | No | Yes | 0.5 | |
| `partners.positions` | array | Partner relative positions | No | Yes | | Relative positions for partner placement |
| `partners.excluded_names` | array(string[]) | List of excluded partner objects | No | Yes | | Objects that repel from this one |
| `partners.probability_repelled` | number (0–1) | Probability of repulsion from excluded partners | No | Yes | | |
| `partners.weight` | number | Weight factor for partner interactions | No | Yes | 0.2 | Influence strength of partner effects |



### Gradients Section


| Field Path | Type | Description | Required | Editable | Default Value | Notes |
|------------|------|-------------|----------|----------|-----|-------|
| `description` | string | Description of gradient | No | No | | For user clarity |
| `mode` | string(enum) | Gradient method | Yes | No | | Defined by gradient. Accepts a mode from `X`, `Y`, `Z`, `VECTOR`, `RADIAL`, `SURFACE` |
| `pick_mode` | string(enum) | Gradient sampling method | Yes | Yes | | Accepts a pick mode from `MAX`, `MIN`, `RND`, `LINEAR`, `BINARY`, `SUB`, `REG` |
| `weight_mode` | string(enum) | Gradient weighting function | Yes | Yes | | Accepts a weight mode from `LINEAR`, `SQUARE`, `CUBE`, `POWER`, `EXPONENTIAL`|
| `reversed` | boolean | Reverse gradient direction | No | Yes | | |
| `invert` | boolean | Invert gradient values | No | Yes | |  |
| `weight_mode_settings.decay_length` | number | Decay rate parameter | No | Yes | | Controls gradient falloff |
| `mode_settings.object` | string | Reference object | No | No | | Links to a mesh object |
| `mode_settings.scale_to_next_surface` | boolean | Scaling toggle | No | Yes | | |
| `mode_settings.direction` | array `[x, y, z]` | Direction vector for mode | No | No | | Defined by the mode |
| `mode_settings.center` | array `[x, y, z]` | Center point for the gradient | No | No | | Used as the origin for radial or directional gradients, defined by the mode |




### Composition

The composition section defines the hierarchical structure of containers and their contents. It establishes parent-child relationships between objects and specifies which objects are placed within different cellular regions.

| Field Path | Type | Description | Required | Editable | Default Value |  Notes |
|------------|------|-------------|----------|----------|-----|-------|
| `id` | string (unique) | Unique identifier for the composition item | Yes | Yes | | Must be unique within composition |
| `object` | string | Linked object name | No | No | | Must exist in `objects` |
| `count` | number (integers >= 0) | Number of objects | No | Yes | 5? | Range? Validation depending on the object type? e.g. `nucleus`|
| `priority` | number | Packing priority | No | No | | e.g. -1 |
| `regions.interior` | array | Interior contents of object | No | No | | Validation? e.g. `peroxisome` can't be placed inside `nucleus` |
| `regions.surface` | array | Surface contents of object | No | No | | Objects placed on the surface |
| `regions.inner-leaflet` | array | Inner leaflet contents | No | No | | Objects placed on inner leaflet |
| `regions.outer-leaflet` | array | Outer leaflet contents | No | No | | Objects placed on outer leaflet |






## Config

The config file controls the packing behavior. It specifies parameters such as packing algorithms, output formats, performance settings, and debugging options that don't affect the biological content but control how the simulation is executed.

| Field Path | Type | Description | Required | Editable | Default Value | Notes |
|------------|------|-------------|----------|----------|---------------|-------|
| `clean_grid_cache` | boolean | Clear cached grid before packing | | Yes | False |  |
| `format` | string | Output format | | No | simularium |  |
| `inner_grid_method` | string | Method used to create the inner grid | | Yes | trimesh | e.g., `trimesh`, `raytrace` |
| `live_packing` | boolean | Enable real-time packing visualization | | Yes | False |  |
| `load_from_grid_file` | boolean | Load objects from a grid file | | Yes | False | |
| `name` | string | Name of the config | | Yes | default | Used to identify this config run |
| `number_of_packings` | number (>=1) | Number of independent packing runs | | Yes | 1 | |
| `open_results_in_browser` | boolean | Open results in browser after run | | Yes | True |  |
| `ordered_packing` | boolean | Use deterministic packing order | | Yes | False |  |
| `out` | string | Output directory path | | Yes | out/ |  |
| `overwrite_place_method` | boolean | Override object-specific place methods | | Yes | False |  |
| `parallel` | boolean | Enable parallel packing | | Yes | False | |
| `place_method` | string | Default packing method | | Yes | spheresSST | e.g., `jitter`, `spheresSST` |
| `randomness_seed` | number | Random seed value | | Yes | None |  |
| `save_analyze_result` | boolean | Save packing analysis result | | Yes | False |  |
| `save_converted_recipe` | boolean | Export converted recipe | | Yes | False | Save recipe that converted from v1 to v2  |
| `save_gradient_data_as_image` | boolean | Save gradient values as image | | Yes | False | |
| `save_plot_figures` | boolean | Save analysis figures | | Yes | |  |
| `show_grid_plot` | boolean | Display grid visualization | | Yes | False |  |
| `show_progress_bar` | boolean | Show progress bar in terminal | | Yes | False | |
| `show_sphere_trees` | boolean | Visualize sphere trees | | Yes | False | |
| `spacing` | number | Override object spacing | | Yes | None |  |
| `upload_results` | boolean | Upload results to S3 | | Yes | True | |
| `use_periodicity` | boolean | Enable periodic boundary conditions | | Yes | False | |
| `version` | number | Config version number | | Yes | 1.0 | For internal tracking |
| `image_export_options.hollow` | boolean | Export hollow images | | Yes | | |
| `image_export_options.projection_axis` | string | Image projection axis | | Yes | | e.g., `x`, `y`, `z` |
| `image_export_options.voxel_size` | array `[x, y, z]` | Voxel size for image export | | Yes | | |RetryClaude can make mistakes. Please double-check responses.