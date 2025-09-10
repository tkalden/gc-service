# GhogumCloset Backend - Virtual Try-On API

A secure Python FastAPI backend for the GhogumCloset app, providing advanced virtual try-on capabilities with neural network-powered clothing simulation.

## Features

- 🚀 **FastAPI** - Modern, fast web framework with async support
- 🧠 **AI-Powered VTO** - SwayamInSync ViTON neural networks for realistic virtual try-on
- 👤 **Avatar Processing** - MediaPipe pose estimation and body segmentation
- 🗄️ **Supabase Integration** - Secure database and storage with RLS
- 📸 **Advanced Image Processing** - Background removal, cloth segmentation, pose detection
- 🔒 **Security First** - Environment-based configuration, no hardcoded secrets
- 📚 **Auto Documentation** - Swagger UI included
- 🌐 **CORS Support** - Ready for React Native app
- ⚡ **High Performance** - Supports 1000+ concurrent users

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

**⚠️ SECURITY NOTICE: Never commit sensitive credentials to git!**

Create a `.env` file in the backend directory:

```bash
# Copy the example file
cp env.example .env
```

Then edit `.env` with your actual values:

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration (comma-separated list)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:8082
```

#### Getting Your Supabase Keys:

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings > API
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **Service role key** → `SUPABASE_SERVICE_KEY` (⚠️ Keep this secret!)

#### Security Checklist:

- [ ] Never commit `.env` files to git
- [ ] Use different keys for development/production
- [ ] Regularly rotate API keys
- [ ] Use service role keys only on server-side
- [ ] Enable Row Level Security (RLS) in Supabase

### 3. Run the Server

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Virtual Try-On (VTO)

- `POST /api/avatar/upload` - Upload and process avatar image
- `POST /api/avatar/virtual-tryon` - Generate virtual try-on result
- `GET /api/avatar/{user_id}` - Get user's avatar data
- `GET /api/tryon-results/{user_id}` - Get try-on history

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/reset-password` - Password reset

### Clothing Items

- `GET /api/clothes` - Get all clothing items
- `GET /api/clothes/{id}` - Get specific clothing item
- `POST /api/clothes` - Create new clothing item
- `PUT /api/clothes/{id}` - Update clothing item
- `DELETE /api/clothes/{id}` - Delete clothing item

### Image Upload

- `POST /api/upload` - Upload single image
- `POST /api/upload/multiple` - Upload multiple images
- `POST /api/clothes/{id}/image` - Upload image for specific item

### Utility

- `GET /api/clothes/category/{category}` - Get items by category
- `GET /api/clothes/season/{season}` - Get items by season
- `GET /health` - Health check

## Data Models

### ClothingItem

```json
{
  "id": "uuid",
  "name": "T-Shirt",
  "category": "tops",
  "seasons": ["spring", "summer"],
  "image_path": "user-clothes/image.jpg",
  "is_user_added": true,
  "added_date": "2025-01-01T00:00:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "metadata": {}
}
```

### Categories

- `tops`
- `bottoms`
- `shoes`
- `accessories`
- `dresses`
- `outerwear`

### Seasons

- `spring`
- `summer`
- `fall`
- `winter`

## Example Usage

### Create a clothing item

```bash
curl -X POST "http://localhost:8000/api/clothes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue Jeans",
    "category": "bottoms",
    "seasons": ["spring", "summer", "fall"],
    "is_user_added": true
  }'
```

### Upload an image

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@image.jpg" \
  -F "folder=user-clothes"
```

### Get all clothes

```bash
curl "http://localhost:8000/api/clothes"
```

## Development

### Project Structure

```
backend/
├── main.py          # FastAPI application
├── models.py        # Pydantic models
├── database.py      # Database operations
├── storage.py       # Storage operations
├── config.py        # Configuration
├── requirements.txt # Dependencies
└── README.md        # This file
```

### Adding New Features

1. **Models**: Add new Pydantic models in `models.py`
2. **Database**: Add database operations in `database.py`
3. **Endpoints**: Add new routes in `main.py`
4. **Storage**: Add storage operations in `storage.py`

### Testing

The API includes automatic OpenAPI documentation at `/docs` where you can test all endpoints interactively.

## Deployment

### Local Development

```bash
python main.py
```

### Production

For production deployment, ensure security best practices:

```bash
# Set production environment variables
export DEBUG=False
export SUPABASE_URL=https://your-prod-project.supabase.co
export SUPABASE_SERVICE_KEY=your-prod-service-key

# Run with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Production Security Checklist:

- [ ] Use production Supabase instance with separate credentials
- [ ] Set `DEBUG=False` in production
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable HTTPS only
- [ ] Restrict CORS origins to your domain
- [ ] Set up proper monitoring and logging
- [ ] Use environment-specific configuration
- [ ] Regularly update dependencies for security patches

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Integration with React Native App

The backend is designed to replace the direct Supabase client calls in your React Native app. Update your app to call these API endpoints instead of directly accessing Supabase.

### Example Integration

```javascript
// Instead of direct Supabase calls
const response = await fetch('http://localhost:8000/api/clothes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'T-Shirt',
    category: 'tops',
    seasons: ['spring', 'summer'],
    is_user_added: true
  })
});
```
