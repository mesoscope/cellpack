# cellPACK Recipe and Config Schema 2.0


## Recipe

The recipe JSON file defines the specification for a cellPACK packing, including the ingredients to be packed, their spatial relationships, and composition hierarchy.

### Top-Level Fields

| Field Path | Type | Description | Required | Editable | Editing Method | User Visible | Default Value | Notes |
|------------|------|-------------|----------|------------|----------------|-------|-----|-------|
| `name` | string | Name of the recipe | | Yes | Text input | yes | |Required, must be unique. If missing, an automatic version number will be appended. |
| `version` | string | Recipe version string | | No |  | no | |Auto-generated |
| `format_version` | string | Schema format version | | No |  | no | |  |
| `bounding_box` | array | Bounding box of the packing result | | No? | Array input / 3D | no | |[minX, minY, minZ], [maxX, maxY, maxZ] |
| `grid_file_path` | string | Grid data file path | | No |  | yes | | Managed by backend. Local file support may be added in the future. |


### Objects Section


| Field Path | Type | Description | Required | Editable | Editing Method | Default Value | Notes |
|------------|------|-------------|----------|------------|----------------|-----|-------|
| `color` | array | RGB color of object | | Yes | Color picker | | Values between 0–1 |
| `type` | string | Object type | | No |  | | Defined by the object |
| `inherit` | string | Linked name of the inherited object | | No | | | Defined by the object. Must exist in `objects` |
| `radius` | number | Object radius | | Yes | Slider / Numeric input | |  |
| `jitter_attempts` | number | Max retries for packing | | Yes? | Numeric input | | | 
| `max_jitter` | array | Vector with maximum jitter distance in units of grid spacing | | Yes? | Array input | | Values between 0–1 per axis |
| `place_method` | string | Method used for packing the object | | Yes | Dropdown | | e.g. `jitter` |
| `available_regions` | array | Regions where the object can be placed | | No for now? | Multi-select or checklist | |e.g. `interior`, `surface`, `outer_leaflet`, `inner_leaflet` |
| `packing_mode` | string | Packing behavior mode | | No? |  | | Tied to the recipe  |
| `gradient` | string | Linked gradient name | | Yes | Dropdown | | Must exist in `gradients` |
| `representations.mesh.path` | string | Mesh file path | | No |  | | Managed backend |
| `representations.mesh.name` | string | Mesh filename | | No |  | | Tied to the object |
| `representations.mesh.format` | string | Mesh file format | | No |  | | Tied to the object |
| `representations.mesh.coordinate_system` | string | 'left' or 'right' depending on generating software | | No |  | | Tied to the object |
| `partners.names` | array | List of partner object names | | Yes | Multi-select or text array |  | Objects that attract to this one, must exist in `objects`|
| `partners.probability_binding` | number | Probability of binding with partners | | Yes | Slider / Numeric input |  | Values between 0–1 |
| `partners.positions` | array | Partner relative positions | | Yes? | Array input |  | Relative positions for partner placement |
| `partners.excluded_names` | array | List of excluded partner objects | | Yes | Multi-select or text array |  | Objects that repel from this one |
| `partners.probability_repelled` | number | Probability of repulsion from excluded partners | | Yes | Slider / Numeric input |  | Values between 0–1 |
| `partners.weight` | number | Weight factor for partner interactions | | Yes | Slider / Numeric input |  | Influence strength of partner effects |


### Gradients Section


| Field Path | Type | Description | Required | Editable | Editing Method | Default Value | Notes |
|------------|------|-------------|----------|------------|----------------|-----|-------|
| `description` | string | Description of gradient | | No for now | | | For user clarity |
| `mode` | string | Gradient method | | No? |  | | Defined by gradient |
| `pick_mode` | string | Gradient sampling method | | Yes | Dropdown | | e.g., `rnd` |
| `weight_mode` | string | Gradient weighting function | | Yes | Dropdown | | e.g., `linear`, `cube` |
| `reversed` | boolean | Reverse gradient direction | | Yes | Toggle | | Boolean |
| `invert` | boolean | Invert gradient values | | Yes? | Toggle |  | |
| `weight_mode_settings.decay_length` | number | Decay rate parameter | | Yes | Slider / Numeric input| | Controls gradient falloff |
| `mode_settings.object` | string | Reference object | | No |  | | Links to a mesh object |
| `mode_settings.scale_to_next_surface` | boolean | Scaling toggle | | Yes? | Toggle | | |
| `mode_settings.direction` | array | Direction vector for mode | | No |  | | Format: `[x, y, z]`. Defined by the mode |
| `mode_settings.center` | array | Center point for the gradient | | No | | | Format: `[x, y, z]`. Used as the origin for radial or directional gradients, defined by the mode |


### Composition

The composition section defines the hierarchical structure of containers and their contents. It establishes parent-child relationships between objects and specifies which objects are placed within different cellular regions.

| Field Path | Type | Description | Required | Editable | Editing Method | Default Value |  Notes |
|------------|------|-------------|----------|------------|----------------|-----|-------|
| `id` | string | Unique identifier for the composition item | | Yes | Text input | | Must be unique within composition |
| `object` | string | Linked object name | | No |  | | Must exist in `objects` |
| `count` | number | Number of objects | | Yes | Numeric input | | Integers >= 0. Range? Validation depending on the object type? e.g. `nucleus`|
| `priority` | number | Packing priority | | No | Numeric input | | e.g. -1 |
| `regions.interior` | array | Interior contents of object | | No for now | List editor | | Validation? e.g. `peroxisome` can't be placed inside `nucleus` |
| `regions.surface` | array | Surface contents of object | | No for now | List editor | | Objects placed on the surface |
| `regions.inner-leaflet` | array | Inner leaflet contents | | No for now | List editor | | Objects placed on inner leaflet |
| `regions.outer-leaflet` | array | Outer leaflet contents | | No for now | List editor | | Objects placed on outer leaflet |


## Config

The config file controls the packing behavior. It specifies parameters such as packing algorithms, output formats, performance settings, and debugging options that don't affect the biological content but control how the simulation is executed.

| Field Path | Type | Description | Required | Editable | Editing Method | Default Value | Notes |
|------------|------|-------------|----------|----------|----------------|---------------|-------|
| `clean_grid_cache` | boolean | Clear cached grid before packing | |  | Toggle | False |  |
| `format` | string | Output format | |  |  | simularium |  |
| `inner_grid_method` | string | Method used to create the inner grid | |  | Dropdown | trimesh | e.g., `trimesh`, `raytrace` |
| `live_packing` | boolean | Enable real-time packing visualization | |  | Toggle | False |  |
| `load_from_grid_file` | boolean | Load objects from a grid file | |  | Toggle | False | |
| `name` | string | Name of the config | |  | Text input | default | Used to identify this config run |
| `number_of_packings` | number | Number of independent packing runs | |  | Numeric input | 1 | >=1 |
| `open_results_in_browser` | boolean | Open results in browser after run | |  | Toggle | True |  |
| `ordered_packing` | boolean | Use deterministic packing order | |  | Toggle | False |  |
| `out` | string | Output directory path | |  | Text input | out/ |  |
| `overwrite_place_method` | boolean | Override object-specific place methods | |  | Toggle | False |  |
| `parallel` | boolean | Enable parallel packing | |  | Toggle | False | |
| `place_method` | string | Default packing method | |  | Dropdown | spheresSST | e.g., `jitter`, `spheresSST` |
| `randomness_seed` | number | Random seed value | |  | Numeric input | None |  |
| `save_analyze_result` | boolean | Save packing analysis result | |  | Toggle | False |  |
| `save_converted_recipe` | boolean | Export converted recipe | |  | Toggle | False | Save recipe that converted from v1 to v2  |
| `save_gradient_data_as_image` | boolean | Save gradient values as image | |  | Toggle | False | |
| `save_plot_figures` | boolean | Save analysis figures | |  | Toggle |  |  |
| `show_grid_plot` | boolean | Display grid visualization | |  | Toggle | False |  |
| `show_progress_bar` | boolean | Show progress bar in terminal | |  | Toggle | False | |
| `show_sphere_trees` | boolean | Visualize sphere trees | |  | Toggle | False | |
| `spacing` | number | Override object spacing | |  | Numeric input / null | None |  |
| `upload_results` | boolean | Upload results to S3 | |  | Toggle | True | |
| `use_periodicity` | boolean | Enable periodic boundary conditions | |  | Toggle | False | |
| `version` | number | Config version number | |  | Numeric input | 1.0 | For internal tracking |
| `image_export_options.hollow` | boolean | Export hollow images | |  | Toggle |  | |
| `image_export_options.projection_axis` | string | Image projection axis | |  | Dropdown |  | e.g., `x`, `y`, `z` |
| `image_export_options.voxel_size` | array | Voxel size for image export | |  | Array input |  | Format: `[x, y, z]` |