#!/bin/bash
# Build Python server binary

set -e

PLATFORM=$(rustc --print host-tuple 2>/dev/null || echo "unknown")
echo "Building VideoGen server for platform: $PLATFORM"

export PATH="$(cd "$(dirname "$0")/.." && pwd)/backend/venv/bin:$PATH"
cd backend

if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    python -m pip install pyinstaller
fi

python build_binary.py
echo "Build complete!"
