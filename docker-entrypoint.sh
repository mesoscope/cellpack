#!/bin/bash -e

# if [ -z "$recipe" ]; then
#     echo "Required recipe parameter is missing, please include recipe in Docker run script, ie: -e r=path/to/recipe"
#     exit 
# fi

# if [ -z "$config" ]; then
#     echo "Required config parameter is missing, please include packing config in Docker run script, ie: -e c=path/to/config"
#     exit 
# fi

cd /cellpack
# pack -r ${recipe} -c ${config}
pack -r examples/recipes/v2/one_sphere.json -c examples/packing-configs/run.json