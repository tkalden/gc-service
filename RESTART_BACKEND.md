# How to Restart Backend with MediaPipe

## The Issue
MediaPipe is installed in the venv, but the running backend server was started before MediaPipe was installed, so it doesn't have access to it.

## Solution: Restart the Backend

### Step 1: Stop the Current Backend
In the terminal where `./startbackend.sh` is running:
- Press `Ctrl+C` to stop the server

### Step 2: Restart the Backend
```bash
cd /Users/tenzinkalden/Desktop/projects/gc-service
./startbackend.sh
```

### Step 3: Verify MediaPipe is Loaded
After restarting, look for these messages in the backend logs:
```
MediaPipe library loaded successfully
OpenCV library loaded successfully
```

If you see these messages, MediaPipe is working!

### Step 4: Test Avatar Upload
Try uploading an avatar again in the app. The error should be gone.

## Alternative: Check if Backend is Using Venv

If restarting doesn't work, verify the backend is using the venv:

```bash
# Check which Python the backend is using
ps aux | grep uvicorn | grep -v grep

# The path should include 'venv' if using virtual environment
```

## Quick Test Command

To verify MediaPipe is accessible from the venv:
```bash
cd /Users/tenzinkalden/Desktop/projects/gc-service
./venv/bin/python3 -c "import mediapipe; print('✅ MediaPipe works!')"
```


