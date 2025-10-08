# Config Schema

The config file controls the packing behavior. It specifies parameters such as packing algorithms, output formats, performance settings, and debugging options that don't affect the biological content but control how the simulation is executed.

| Field Path                             | Type              | Description                              | Default Value | Notes                                               |
| -------------------------------------- | ----------------- | ---------------------------------------- | ------------- | --------------------------------------------------- |
| `clean_grid_cache`                     | boolean           | Clear cached grid before packing         | False         |                                                     |
| `format`                               | string            | Output format                            | simularium    |                                                     |
| `inner_grid_method`                    | string            | Method used to create the inner grid     | trimesh       | e.g., `trimesh`, `raytrace`                         |
| `live_packing`                         | boolean           | Enable real-time packing visualization   | False         | Not implemented currently                           |
| `load_from_grid_file`                  | boolean           | Load objects from a grid file            | False         |                                                     |
| `name`                                 | string            | Name of the config                       | default       | Used to identify this config run                    |
| `number_of_packings`                   | number (>=1)      | Number of independent packing replicates | 1             |                                                     |
| `open_results_in_browser`              | boolean           | Open results in browser after run        | True          |                                                     |
| `ordered_packing`                      | boolean           | Use deterministic packing order          | False         |                                                     |
| `out`                                  | string            | Output directory path                    | `"out/"`      |                                                     |
| `overwrite_place_method`               | boolean           | Override object-specific place methods   | False         |                                                     |
| `parallel`                             | boolean           | Enable parallel packing                  | False         |                                                     |
| `place_method`                         | string            | Default packing method                   | spheresSST    | e.g., `jitter`, `spheresSST`                        |
| `randomness_seed`                      | number            | Random seed value                        | None          | Helps reproduce packing runs                        |
| `save_analyze_result`                  | boolean           | Save packing analysis result             | False         | Saves additional data and figures from packing.     |
| `save_converted_recipe`                | boolean           | Export converted recipe                  | False         | Save recipe converted from older to newer versions. |
| `save_gradient_data_as_image`          | boolean           | Save gradient values as image            | False         |                                                     |
| `save_plot_figures`                    | boolean           | Save analysis figures                    |               |                                                     |
| `show_grid_plot`                       | boolean           | Display grid visualization               | False         |                                                     |
| `show_progress_bar`                    | boolean           | Show progress bar in terminal            | False         |                                                     |
| `show_sphere_trees`                    | boolean           | Visualize sphere trees                   | False         |                                                     |
| `spacing`                              | number            | Override object spacing                  | None          |                                                     |
| `upload_results`                       | boolean           | Upload results to S3                     | False          |                                                     |
| `use_periodicity`                      | boolean           | Enable periodic boundary conditions      | False         |                                                     |
| `version`                              | number            | Config version number                    | 1.0           | For internal tracking                               |
| `image_export_options.hollow`          | boolean           | Export hollow images                     | False         |                                                     |
| `image_export_options.projection_axis` | string            | Camera position for projection axis      | `z`           | e.g., `x`, `y`, `z`                                 |
| `image_export_options.voxel_size`      | array `[x, y, z]` | Voxel size for image export              |               | `[1, 1, 1]`                                         |  |

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