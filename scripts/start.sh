#!/bin/bash
set -e

MODEL_PATH="models/clothes_classifier_model.h5"

if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading clothing classifier model..."
    mkdir -p models
    curl -fL \
        "https://github.com/tkalden/gc-service/releases/download/v1.0-models/clothes_classifier_model.h5" \
        -o "$MODEL_PATH"
    echo "Model downloaded ($(du -h $MODEL_PATH | cut -f1))"
fi

exec /opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT
