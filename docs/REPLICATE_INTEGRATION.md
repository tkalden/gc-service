# Virtual Try-On with Replicate API

## Overview

The gc-service now integrates with Replicate's API to provide high-quality, AI-powered virtual try-on functionality. This replaces the previous local model implementation and provides faster, more realistic results.

## Features

- **High-Quality Results**: Uses the IDM-VTON model for realistic virtual try-on
- **Fast Processing**: Cloud-based processing eliminates local compute requirements
- **Automatic Fallback**: Falls back to basic overlay if Replicate is unavailable
- **Category Support**: Supports tops, bottoms, dresses, and more

## Setup

### 1. Install Dependencies

The `replicate` library has been added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add your Replicate API token to your `.env` file:

```bash
# Replicate API Configuration
REPLICATE_API_TOKEN=your-replicate-api-token-here
REPLICATE_TRYON_MODEL=cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4
```

To get your API token:
1. Sign up at [replicate.com](https://replicate.com)
2. Go to your account settings
3. Copy your API token
4. Add it to your `.env` file

### 3. Restart the Server

If the server is running, it should automatically reload. Otherwise, start it with:

```bash
./startbackend.sh
```

## API Usage

### Virtual Try-On Endpoint

**Endpoint**: `POST /api/v1/avatar/try-on`

**Request Body**:
```json
{
  "clothing_id": "uuid-of-clothing-item",
  "avatar_id": "uuid-of-avatar" // optional
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "image_base64": "base64-encoded-image-data",
    "confidence": 0.95,
    "method": "replicate_idm_vton",
    "processing_time": 5.2
  },
  "message": "Try-on preview generated successfully"
}
```

## How It Works

1. **Image Retrieval**: The service downloads the user's avatar and selected clothing item
2. **Replicate API Call**: Images are sent to Replicate's IDM-VTON model
3. **Result Processing**: The generated image is converted to base64 and returned
4. **Fallback**: If Replicate is unavailable, the service uses a basic overlay method

## Service Architecture

### ReplicateService (`app/services/replicate_service.py`)

The main service class that handles:
- API token management
- Image format conversion (PIL → data URL)
- API calls to Replicate
- Result processing and error handling

### AvatarService Integration

The `AvatarService` has been updated to:
1. Check if Replicate is available
2. Attempt to use Replicate for virtual try-on
3. Fall back to basic overlay if needed

## Model Information

**Model**: IDM-VTON (Improved Diffusion Models for Virtual Try-On)
- **Version**: `cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4`
- **Categories**: upper_body, lower_body, dresses
- **Processing Time**: ~5-10 seconds per image

## Configuration Options

You can customize the model behavior by modifying the parameters in `replicate_service.py`:

```python
replicate_result = await replicate_service.create_virtual_tryon(
    person_image=avatar_image,
    garment_image=clothing_image,
    category=category,
    num_inference_steps=30,  # More steps = higher quality, slower
    guidance_scale=2.0       # Higher = more faithful to garment
)
```

## Monitoring and Logging

The service logs all operations:
- `🚀 Using Replicate API for virtual try-on` - Replicate is being used
- `✅ Replicate virtual try-on successful` - Operation completed
- `Replicate service not available - using basic overlay` - Fallback mode

Check logs for debugging:
```bash
tail -f logs/app.log
```

## Cost Considerations

Replicate charges per API call. Monitor your usage at [replicate.com/account](https://replicate.com/account).

Typical costs:
- IDM-VTON: ~$0.01-0.05 per generation
- Consider implementing rate limiting for production use

## Troubleshooting

### "Replicate service not available"
- Check that `REPLICATE_API_TOKEN` is set in `.env`
- Verify the replicate library is installed: `pip list | grep replicate`

### "Replicate API error"
- Check your API token is valid
- Verify you have credits in your Replicate account
- Check the logs for detailed error messages

### Slow Response Times
- Replicate API calls take 5-10 seconds
- Consider implementing a queue system for production
- Show loading states in your UI

## Future Enhancements

- [ ] Support for multiple model versions
- [ ] Caching of results to reduce API calls
- [ ] Batch processing for multiple try-ons
- [ ] Custom model fine-tuning
- [ ] Real-time status updates via WebSocket

## Migration from gc-ui

The virtual try-on functionality has been moved from the gc-ui frontend to the gc-service backend:

**Before** (gc-ui):
- Frontend called Replicate directly
- API token exposed in client

**After** (gc-service):
- Backend handles all Replicate calls
- API token secured on server
- Frontend receives processed results

This improves security and allows for better rate limiting and caching.
