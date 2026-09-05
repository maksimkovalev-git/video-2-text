#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$PROJECT_DIR/llm-env"
REQUIREMENTS="$PROJECT_DIR/requirements-llm.txt"
CONFIG="$PROJECT_DIR/llm/config.yaml"

clear
echo "Local Video to Text — LLM Setup"
echo "==============================="
echo

if [ "$(uname -m)" != "arm64" ]; then
    echo "Error: this MLX setup requires an Apple Silicon Mac."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 was not found."
    echo "Install Python 3 and run _10_setup_llm.command again."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ ! -f "$REQUIREMENTS" ] || [ ! -f "$CONFIG" ]; then
    echo "Error: requirements-llm.txt or llm/config.yaml was not found."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ -d "$ENV_DIR" ] && [ ! -f "$ENV_DIR/pyvenv.cfg" ]; then
    echo "Error: llm-env exists but does not look like a Python environment."
    echo "It was left unchanged."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ ! -d "$ENV_DIR" ]; then
    echo "Creating the local LLM environment..."
    if ! python3 -m venv "$ENV_DIR"; then
        echo "Failed to create the environment."
        read -r -p "Press Enter to close this window..."
        exit 1
    fi
else
    echo "The llm-env environment already exists; updating dependencies."
fi

PYTHON="$ENV_DIR/bin/python"

echo "Installing MLX dependencies..."
if ! "$PYTHON" -m pip install --upgrade pip; then
    echo "Failed to update pip. Check your internet connection."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if ! "$PYTHON" -m pip install -r "$REQUIREMENTS"; then
    echo "Failed to install MLX dependencies. Check your internet connection."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

MODEL=$("$PYTHON" - "$CONFIG" <<'PY'
import sys
from pathlib import Path
import yaml

config = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(config["model"])
PY
)

if [ -z "$MODEL" ]; then
    echo "Error: no model is configured in llm/config.yaml."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

echo
echo "Downloading and verifying model: $MODEL"
echo "The first download is approximately 8.3 GB."
if ! "$PYTHON" - "$MODEL" <<'PY'
import sys
from mlx_lm import load

model_name = sys.argv[1]
load(model_name)
print(f"Model is ready: {model_name}")
PY
then
    echo "Failed to download or load the model."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

echo
echo "Local LLM setup complete."
echo "No GUI, account, or background server is required."
echo
read -r -p "Press Enter to close this window..."
