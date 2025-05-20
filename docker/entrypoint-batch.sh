#!/bin/bash -e

if [ -z "$recipe" ]; then
    echo "Required recipe parameter is missing, please include recipe in Docker run script, ie: -e recipe=path/to/recipe"
    exit;
else
    echo "recipe passed in: '$recipe'"
fi

cd /cellpack

if [ -z "$config" ]; then
    echo "Config parameter not included, using default value"
    pack -r $recipe -d
    exit;
else
    echo "config passed in: '$config'"
fi

pack -r $recipe -c $config -d
