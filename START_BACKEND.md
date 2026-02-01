# How to Start the Backend Server

## Quick Start

```bash
cd /Users/tenzinkalden/Desktop/projects/gc-service
python3 main.py
```

Or if you have a startup script:
```bash
./startbackend.sh
```

## Verify Backend is Running

After starting, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup
```

## Test Backend is Accessible

In another terminal, test:
```bash
curl http://192.168.1.175:8000/health
```

You should get a JSON response like:
```json
{"status": "healthy", "version": "1.0.0", "environment": "development"}
```

## Important Notes

1. **Keep the backend terminal open** - Don't close it while testing
2. **Check CORS settings** - Make sure your IP is allowed in CORS
3. **Check firewall** - Make sure port 8000 isn't blocked
4. **Same network** - Your phone and computer must be on the same WiFi

## Troubleshooting

If backend won't start:
1. Check if port 8000 is already in use: `lsof -ti:8000`
2. Check if .env file exists with required variables
3. Check Python version: `python3 --version` (should be 3.9+)
4. Install dependencies: `pip install -r requirements.txt`


