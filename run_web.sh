#!/bin/bash
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