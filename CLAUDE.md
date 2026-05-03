# gc-service — GC Closet Manager Backend

FastAPI backend. Supabase (auth + Postgres + Storage), Replicate (VTO), rembg (bg removal), TensorFlow (clothing classifier).

## Run locally

```bash
python3 -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

- Docs: http://127.0.0.1:8000/docs
- Must bind `0.0.0.0` — iOS simulator reaches backend via Mac's LAN IP, not localhost.

## Run tests

```bash
pip install -r requirements-dev.txt
pytest tests/integration/ -v
```

Tests use real Supabase. Skip (not fail) automatically if Supabase is unreachable.
Test user: `alice.smith@gmail.com` / `password123`

## Key env vars (.env)

| Var | Purpose |
|-----|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role JWT — bypasses RLS, backend only |
| `SECRET_KEY` | JWT signing (64-byte hex) |
| `REPLICATE_API_TOKEN` | Virtual try-on via IDM-VTON |
| `ALLOWED_ORIGINS` | CORS — add Railway URL once deployed |

## Project structure

```
main.py
app/api/v1/
  auth/router.py       # POST /auth/login|register|logout|refresh|me
  clothes/router.py    # CRUD /clothes — all endpoints require auth + owner check
  outfits/router.py    # CRUD /outfits
  upload/router.py     # POST /upload/smart-upload-async (bg removal + classify)
  avatar/router.py     # GET /avatar, POST /avatar/try-on, GET /avatar/try-on/status/{job_id}
  images/router.py     # GET /images/{path} — proxies Supabase Storage
app/services/
  auth_service.py           # Supabase Auth wrapper
  database_service.py       # All DB queries (clothing, outfits, avatars, tryon)
  storage_service.py        # Supabase Storage upload/delete
  avatar_service.py         # Orchestrates VTO; MediaPipe pose detection (broken, non-blocking)
  replicate_service.py      # Replicate IDM-VTON at 15 steps (~15-30s)
  background_removal.py     # rembg (u2net_human_seg model)
  clothing_classifier.py    # TensorFlow category classifier
  enhanced_clothing_classifier.py  # Adds season detection
  outfit_service.py         # Outfit create/delete with image cleanup
  title_generator.py        # Auto-generates clothing item titles
app/core/security.py        # JWT validation middleware
app/middleware/middleware.py # get_current_user_id dependency
config/settings.py          # Pydantic Settings (@lru_cache)
```

## Auth flow

1. `POST /auth/login` → Supabase `sign_in_with_password` → returns Supabase JWT
2. All protected routes: `Authorization: Bearer <token>`
3. `middleware.py` calls `AuthService.verify_token()` → hits Supabase on every request
4. Access token: 30min. Refresh: 7 days.

## Virtual try-on — async job pattern

```
POST /avatar/try-on  →  {job_id, status: "processing"}   # returns immediately
BackgroundTask runs perform_virtual_try_on → Replicate → stores result in _jobs dict
GET /avatar/try-on/status/{job_id}  →  {status: "completed"|"processing"|"failed"}
```

In-memory `_jobs` dict in `avatar/router.py`. Lost on restart — acceptable for now.

## Image upload pipeline

`POST /upload/smart-upload-async` accepts `{"image_base64": "..."}` (JSON, not multipart).
Runs rembg + TensorFlow in parallel via ThreadPoolExecutor. Returns processed image + category + season.

## Database tables

| Table | Notes |
|-------|-------|
| `clothing_items` | user_id, name, category, seasons (JSONB), image_path |
| `outfits` | user_id, clothing_item_ids (JSONB), outfit_date required |
| `avatars` | user_id, original/processed image paths, pose_keypoints |
| `tryon_results` | avatar_id, clothing_item_id, result_image_path |

All queries use service role key → **RLS is bypassed**. Ownership enforced in application layer.
`GET/PUT/DELETE /clothes/{id}` filter by `user_id` — fixed IDOR bug.

## Storage buckets

| Bucket | Contents |
|--------|----------|
| `clothing-image` | User clothing photos |
| `profile-picture` | Profile avatars |
| `digital-twin` | Avatar + try-on result images |

## Railway deployment

Config ready: `railway.toml` + `nixpacks.toml`.

```bash
railway up --service clodrobe
```

Set these env vars in Railway dashboard (everything from .env except EXPO_PUBLIC_* vars).
After deploy, add Railway URL to `ALLOWED_ORIGINS`.

## CI

`.github/workflows/ci.yml` — runs `pytest tests/integration/` on every push.
Requires GitHub Secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`.
Replicate is mocked in tests.

## Known issues

- **MediaPipe**: `module 'mediapipe' has no attribute 'solutions'` on startup. Avatar pose detection unavailable. VTO still works via Replicate.
- **venv broken**: was built at old path. Use system Python: `python3 -m uvicorn ...`
- **Supabase free tier**: pauses after 7 days inactivity. Keep-alive cron in `.github/workflows/keep-supabase-alive.yml` pings every 3 days.
