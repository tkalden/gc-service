# AI Models Directory

This directory contains all AI/ML related models and utilities for the Closet App. These are optional dependencies that can be disabled for deployment to reduce bundle size and avoid compatibility issues.

## Contents

### Core AI Models
- `network.py` - Neural network architecture definitions
- `viton_exact_models.py` - Virtual try-on model implementations
- `viton_exact.py` - Virtual try-on processing pipeline
- `pose_estimation.py` - Pose detection and estimation
- `datasets.py` - Dataset handling utilities

### Neural Networks
- `networks/` - Directory containing neural network implementations
  - `u2net.py` - U2Net model for background removal

### Model Checkpoints
- `checkpoints/` - Directory containing pre-trained model weights
  - `alias_final.pth` - Alias model checkpoint
  - `gmm_final.pth` - GMM model checkpoint  
  - `seg_final.pth` - Segmentation model checkpoint

### Utilities
- `utils.py` - AI-specific utility functions (moved from app/utils/)

## Dependencies

These models require the following optional dependencies:
- `torch` - PyTorch framework
- `torchvision` - Computer vision utilities
- `opencv-python` - OpenCV for image processing
- `mediapipe` - Google's MediaPipe for pose detection
- `rembg` - Background removal
- `scikit-image` - Image processing algorithms

## Deployment Notes

For production deployment (especially on serverless platforms like Vercel), these AI models are typically disabled due to:

1. **Large bundle size** - PyTorch and related libraries are very large
2. **Memory requirements** - AI models require significant RAM
3. **Build timeouts** - Installation can exceed deployment time limits
4. **Compatibility issues** - Some platforms don't support all dependencies

The main application services (avatar_service.py, background_removal.py) are designed to gracefully handle missing AI dependencies and fall back to simpler implementations.
