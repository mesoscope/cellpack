#!/bin/bash -e

if [ -z "$local" ]; then
    export REMOTE_RUN="True";
fi

cd /cellpack
python server.py
