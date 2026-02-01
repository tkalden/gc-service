#!/bin/bash
# Script to reinstall rembg with proper dependencies

echo "🔧 Reinstalling rembg for background removal..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Uninstall rembg first
pip uninstall -y rembg

# Install rembg with specific version
pip install rembg==2.0.50

# Verify installation
python -c "from rembg import remove; print('✅ rembg installed successfully')"

echo "✅ Done! Please restart the backend."


