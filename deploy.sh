#!/bin/bash
set -e

# Ensure we are in the repository root
cd "$(dirname "$0")"

# Create Python virtual environment if missing
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# Activate virtualenv and install dependencies
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verify app runs
python -m src.search

echo "Deployment environment is ready. Run the server with: uvicorn server:app --host 0.0.0.0 --port 8000"
