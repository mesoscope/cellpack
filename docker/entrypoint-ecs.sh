#!/bin/bash -e

if [ -z "$local" ]; then
    export REMOTE_RUN="True";
fi

cd /cellpack
python docker/server.py
