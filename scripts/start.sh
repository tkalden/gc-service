#!/bin/bash
set -e

MODEL_PATH="models/clothes_classifier_model.h5"

if [ "${DOWNLOAD_MODEL:-false}" = "true" ] && [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading clothing classifier model..."
    mkdir -p models
    curl -fL \
        "https://github.com/tkalden/gc-service/releases/download/v1.0-models/clothes_classifier_model.h5" \
        -o "$MODEL_PATH"
    echo "Model downloaded ($(du -h $MODEL_PATH | cut -f1))"
fi

PORT="${PORT:-8000}"
UVICORN_LOG_LEVEL="${UVICORN_LOG_LEVEL:-info}"

# Flush logs immediately (helps Railway capture lines before a crash)
export PYTHONUNBUFFERED=1

echo "Starting uvicorn on 0.0.0.0:${PORT} log_level=${UVICORN_LOG_LEVEL}"
exec /opt/venv/bin/uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --log-level "${UVICORN_LOG_LEVEL}" \
  --access-log \
  --no-use-colors \
  --proxy-headers
