# cellPACK Client Site

The cellPACK client site allows users to edit example recipes, run packings, and visualize results in the browser. 

* Production site: https://cellpack.allencell.org/
* GitHub repository: https://github.com/AllenCell/cellpack-client

### Publishing Recipes to Client Site
To add new example recipes to the client site, the recipe and its associated metadata must be uploaded to Firebase.

1. Set up access to the staging Firebase account, following [these instructions](https://github.com/mesoscope/cellpack/blob/main/docs/REMOTE_DATABASES.md#firebase-firestore)
2. Determine which recipe fields should be editable in the client, and create a JSON file specifying these editable fields following the schema outlined in [this example](https://github.com/mesoscope/cellpack/blob/0f140859824086d73edab008ff381b5e5717db8b/examples/client-data/example_editable_fields.json)
3. Follow cellPACK installation requirements [in README](https://github.com/mesoscope/cellpack?tab=readme-ov-file#installation)
4. Run the following script to upload necessary files to Firebase: `python cellpack/bin/upload_to_client.py -r <path_to_recipe_file> -c <path_to_config_file> -f <path_to_editable_fields_file> -n "Name of Recipe"`
