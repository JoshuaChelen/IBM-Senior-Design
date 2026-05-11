#!/bin/bash
# AI-Generated Code — Claude Sonnet 4.6 (Anthropic, claude.ai)
# Reviewed and tested by the development team.
#
# run_web.sh
# Launches the Performance Stress Testing web UI on Mac/Linux.
# Run this from the project root (IBM-Senior-Design/).
# The server will be available at http://localhost:8030
#
# Prerequisites:
#   - Python 3.10 (https://www.python.org/downloads/release/python-31011/)
#   - Poetry    (https://python-poetry.org/docs/#installation)
#   - Ollama    (https://ollama.ai/) running in the background
#
# First time setup (run once):
#   cd nlip/nlip_web
#   poetry install
#   poetry add ollama jsonschema "numpy==1.26.4" "pandas==2.2.3" matplotlib "scipy==1.13.1"
#   ollama create nlip-sys-desc -f model/NLIP-sys-desc.Modelfile
#   ollama create nlip-follow-up -f model/NLIP-follow-up.Modelfile

set -e

cd "$(dirname "$0")"

if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed."
    echo "Install it from https://python-poetry.org/docs/#installation"
    exit 1
fi

cd nlip/nlip_web

echo "Installing/updating dependencies with Poetry..."
poetry install

echo "Starting NLIP stress testing web app..."
poetry run python nlip_web/stress_test_chat.py