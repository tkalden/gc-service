# Closet App Backend API

A Python FastAPI backend for the Closet App, providing REST API endpoints for clothing management and image storage.

## Features

- 🚀 **FastAPI** - Modern, fast web framework
- 🗄️ **Supabase Integration** - Database and storage
- 📸 **Image Upload** - Handle clothing item images
- 🔒 **Type Safety** - Pydantic models for validation
- 📚 **Auto Documentation** - Swagger UI included
- 🌐 **CORS Support** - Ready for React Native app

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,exp://192.168.1.100:8081
```

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

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

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
