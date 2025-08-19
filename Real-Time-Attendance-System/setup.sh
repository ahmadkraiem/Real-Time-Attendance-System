#!/usr/bin/env bash
set -e

# Create venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# Install prebuilt dlib wheel first (Python 3.8, Windows wheel may also work via emulation on WSL not guaranteed)
pip install wheels/dlib-19.22.99-cp38-cp38-win_amd64.whl || true

# Install remaining deps
if [ -f requirements-py38.txt ]; then
  pip install -r requirements-py38.txt
else
  pip install -r requirements.txt
fi

echo "✅ Setup complete. Activate with: source .venv/bin/activate"
