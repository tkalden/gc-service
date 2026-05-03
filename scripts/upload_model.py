#!/usr/bin/env python3
"""Upload clothes_classifier_model.h5 to Supabase Storage."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BUCKET = "models"
MODEL_FILE = Path(__file__).parent.parent / "models" / "clothes_classifier_model.h5"

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

# Create bucket if it doesn't exist
try:
    supabase.storage.create_bucket(BUCKET, options={"public": False})
    print(f"Created bucket: {BUCKET}")
except Exception:
    print(f"Bucket '{BUCKET}' already exists")

print(f"Uploading {MODEL_FILE} ({MODEL_FILE.stat().st_size / 1024 / 1024:.1f} MB)...")

with open(MODEL_FILE, "rb") as f:
    supabase.storage.from_(BUCKET).upload(
        "clothes_classifier_model.h5",
        f,
        file_options={"content-type": "application/octet-stream", "upsert": "true"},
    )

url = f"{os.environ['SUPABASE_URL']}/storage/v1/object/{BUCKET}/clothes_classifier_model.h5"
print(f"\nDone. Set this as MODEL_DOWNLOAD_URL in Railway:\n{url}")
