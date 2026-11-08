#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Create a Python 3.11+ virtual environment and install requirements.txt first. See README.md.'
  exit 1
fi
exec .venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
