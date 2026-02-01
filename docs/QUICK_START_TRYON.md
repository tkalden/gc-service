# Quick Start Guide: Virtual Try-On API

## Setup (One-time)

### 1. Get Replicate API Token

```bash
# Visit https://replicate.com and sign up
# Go to https://replicate.com/account
# Copy your API token
```

### 2. Configure Environment

Add to your `.env` file:

```bash
REPLICATE_API_TOKEN=r8_your_token_here
```

### 3. Restart Server (if running)

The server should auto-reload, but if not:

```bash
# Stop the server (Ctrl+C)
# Start again
./startbackend.sh
```

## Usage

### Test the Service

```bash
python test_replicate.py
```

Expected output:
```
============================================================
Testing Replicate Virtual Try-On Service
============================================================

📊 Service Status:
  Available: True
  API Token Set: True
  Model Version: cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4
  Library Installed: True

✅ Replicate service is available!
```

### API Endpoint

**POST** `/api/v1/avatar/try-on`

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "clothing_id": "uuid-of-clothing-item",
  "avatar_id": "uuid-of-avatar"  // optional, uses user's default if not provided
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "confidence": 0.95,
    "method": "replicate_idm_vton",
    "processing_time": 5.2
  },
  "message": "Try-on preview generated successfully"
}
```

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/api/v1/avatar/try-on" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clothing_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### Example JavaScript (React Native)

```javascript
const tryOnClothing = async (clothingId) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/avatar/try-on', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        clothing_id: clothingId,
      }),
    });

    const result = await response.json();
    
    if (result.success) {
      // Display the base64 image
      const imageUri = `data:image/png;base64,${result.data.image_base64}`;
      console.log('Try-on successful!', result.data.method);
      return imageUri;
    }
  } catch (error) {
    console.error('Try-on failed:', error);
  }
};
```

## Behavior

### With Replicate Configured ✅
1. Attempts to use Replicate API
2. Returns high-quality AI-generated try-on
3. Processing time: ~5-10 seconds
4. Logs: `🚀 Using Replicate API for virtual try-on`

### Without Replicate Configured ⚠️
1. Falls back to basic overlay
2. Returns simple clothing overlay
3. Processing time: ~1-2 seconds
4. Logs: `Replicate service not available - using basic overlay`

## Troubleshooting

### "Replicate service not available"

**Check 1: Is the library installed?**
```bash
pip list | grep replicate
# Should show: replicate (1.0.7 or higher)
```

**Check 2: Is the API token set?**
```bash
# Run test script
python test_replicate.py
# Check output for "API Token Set: True"
```

**Check 3: Is the token valid?**
```bash
# Test with replicate CLI
pip install replicate
export REPLICATE_API_TOKEN=your_token
replicate run stability-ai/sdxl --help
```

### "Replicate API error"

**Possible causes:**
1. Invalid API token
2. Insufficient credits in Replicate account
3. Rate limit exceeded
4. Network connectivity issues

**Solutions:**
1. Verify token at https://replicate.com/account
2. Check credits at https://replicate.com/account/billing
3. Wait and retry
4. Check internet connection

### Slow Response Times

**Expected behavior:**
- Replicate API: 5-10 seconds
- Basic overlay: 1-2 seconds

**Tips:**
1. Show loading indicator in UI
2. Consider implementing a queue for multiple requests
3. Cache results for repeated try-ons

## Monitoring

### Check Logs

```bash
# Real-time logs
tail -f logs/app.log

# Search for try-on events
grep "virtual try-on" logs/app.log

# Check for errors
grep "ERROR" logs/app.log | grep "try-on"
```

### Key Log Messages

| Message | Meaning |
|---------|---------|
| `🚀 Using Replicate API for virtual try-on` | Replicate is being used |
| `✅ Replicate virtual try-on successful` | Operation completed successfully |
| `Replicate service not available` | Using fallback mode |
| `Replicate API error` | API call failed |

## Cost Tracking

### Replicate Pricing
- IDM-VTON: ~$0.01-0.05 per generation
- Check usage: https://replicate.com/account/billing

### Estimate Monthly Costs

| Try-ons/month | Estimated Cost |
|---------------|----------------|
| 100 | $1-5 |
| 1,000 | $10-50 |
| 10,000 | $100-500 |

### Optimization Tips

1. **Cache Results**: Store try-on results to avoid repeated API calls
2. **Rate Limiting**: Limit requests per user
3. **Batch Processing**: Process multiple try-ons together
4. **Fallback Strategy**: Use basic overlay for preview, Replicate for final

## Next Steps

1. ✅ Configure Replicate API token
2. ✅ Test the service
3. 🔄 Update frontend to use backend API
4. 📊 Monitor usage and costs
5. 🚀 Deploy to production

## Support

- **Documentation**: [docs/REPLICATE_INTEGRATION.md](REPLICATE_INTEGRATION.md)
- **Migration Guide**: [docs/MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)
- **Replicate Docs**: https://replicate.com/docs
- **Model Info**: https://replicate.com/cuuupid/idm-vton

## FAQ

**Q: Do I need Replicate to use the app?**
A: No, the app will work without Replicate using basic overlay. Replicate provides higher quality results.

**Q: Can I use a different model?**
A: Yes, set `REPLICATE_TRYON_MODEL` in `.env` to any compatible model.

**Q: How do I reduce costs?**
A: Implement caching, rate limiting, and use fallback for previews.

**Q: Is my API token secure?**
A: Yes, it's stored server-side and never exposed to clients.

**Q: What happens if Replicate is down?**
A: The service automatically falls back to basic overlay.
