# gc-service — GC Closet Manager Backend

FastAPI backend for the GC Closet app. Handles auth, clothing CRUD, image processing, and virtual try-on.

**Stack:** Supabase (auth + Postgres + Storage) · Replicate IDM-VTON · rembg · TensorFlow

---

## Local development

```bash
python3 -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

- Swagger UI: http://127.0.0.1:8000/docs
- Must bind `0.0.0.0` — iOS simulator connects via Mac's LAN IP, not localhost.

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role JWT — bypasses RLS, never expose client-side |
| `SECRET_KEY` | JWT signing key (64-byte hex) |
| `REPLICATE_API_TOKEN` | Virtual try-on via IDM-VTON |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins — add Railway URL after deploy |

## Deployment (Railway)

Config is in `railway.toml` and `nixpacks.toml`.

```bash
railway up --service gc-service
```

Set all env vars above in the Railway dashboard. After deploy, add the Railway URL to `ALLOWED_ORIGINS`.

## API endpoints

### Auth — `/api/v1/auth/`
| Method | Path | Description |
|---|---|---|
| POST | `/register` | Create account |
| POST | `/login` | Returns Supabase JWT |
| POST | `/logout` | Invalidate session |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Current user info |

All protected routes require `Authorization: Bearer <token>`.

### Clothing — `/api/v1/clothes/`
| Method | Path | Description |
|---|---|---|
| GET | `/` | List user's clothing items |
| POST | `/` | Create item |
| GET | `/{id}` | Get item (owner only) |
| PUT | `/{id}` | Update item (owner only) |
| DELETE | `/{id}` | Delete item + image (owner only) |

### Outfits — `/api/v1/outfits/`
| Method | Path | Description |
|---|---|---|
| GET | `/` | List user's outfits |
| POST | `/` | Create outfit (`outfit_date` required) |
| GET | `/{id}` | Get outfit |
| PUT | `/{id}` | Update outfit |
| DELETE | `/{id}` | Delete outfit |

### Upload — `/api/v1/upload/`
| Method | Path | Description |
|---|---|---|
| POST | `/smart-upload-async` | Upload image → bg removal + classify. Body: `{"image_base64": "..."}` |

### Avatar — `/api/v1/avatar/`
| Method | Path | Description |
|---|---|---|
| POST | `/upload` | Upload avatar photo |
| GET | `/` | Get user's avatar |
| POST | `/try-on` | Start async try-on job → returns `{job_id}` |
| GET | `/try-on/status/{job_id}` | Poll job status: `processing` · `completed` · `failed` |

### Images — `/api/v1/images/`
| Method | Path | Description |
|---|---|---|
| GET | `/{path}` | Proxy image from Supabase Storage |

## Image upload pipeline

`POST /upload/smart-upload-async` runs rembg background removal and TensorFlow clothing classification in parallel, then returns the processed image, category, and detected season.

## Virtual try-on

Try-on is async — Replicate calls take 15-30s:

```
POST /avatar/try-on  →  {job_id, status: "processing"}
  (background task calls Replicate IDM-VTON at 15 steps)
GET /avatar/try-on/status/{job_id}  →  {status, result_url}
```

Job state is in-memory and lost on restart — acceptable for now.

## Database

| Table | Key columns |
|---|---|
| `clothing_items` | `user_id`, `name`, `category`, `seasons` (JSONB), `image_path` |
| `outfits` | `user_id`, `clothing_item_ids` (JSONB), `outfit_date` |
| `avatars` | `user_id`, `original_image_path`, `processed_image_path` |
| `tryon_results` | `avatar_id`, `clothing_item_id`, `result_image_path` |

All queries use the service role key (RLS bypassed). Ownership is enforced at the application layer.

## Storage buckets

| Bucket | Contents |
|---|---|
| `clothing-image` | User clothing photos |
| `profile-picture` | Avatar photos |
| `digital-twin` | Try-on result images |

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/integration/ -v
```

Tests hit real Supabase and skip automatically if unreachable. Test account: `alice.smith@gmail.com` / `password123`.

CI runs on every push via `.github/workflows/ci.yml`. Requires GitHub Secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SECRET_KEY`.

## Known issues

- **MediaPipe** — `module 'mediapipe' has no attribute 'solutions'` on startup. Pose detection is unavailable but VTO still works via Replicate.
