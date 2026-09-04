#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$PROJECT_DIR/whisper-env"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

clear
echo "Local Video to Text — Setup"
echo "==========================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 was not found."
    echo "Install Python 3 and run _00_setup_env.command again."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ ! -f "$REQUIREMENTS" ]; then
    echo "Error: requirements.txt was not found."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ -d "$ENV_DIR" ] && [ ! -f "$ENV_DIR/pyvenv.cfg" ]; then
    echo "Error: whisper-env exists but does not look like a Python environment."
    echo "It was left unchanged."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if [ ! -d "$ENV_DIR" ]; then
    echo "Creating the local Python environment..."
    if ! python3 -m venv "$ENV_DIR"; then
        echo "Failed to create the environment."
        read -r -p "Press Enter to close this window..."
        exit 1
    fi
else
    echo "The whisper-env environment already exists; updating dependencies."
fi

echo "Installing dependencies..."
if ! "$ENV_DIR/bin/python" -m pip install --upgrade pip; then
    echo "Failed to update pip. Check your internet connection."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

if ! "$ENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS"; then
    echo "Failed to install dependencies. Check your internet connection."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

echo
echo "Setup complete. You can now run _run_transcription.command."
echo "The selected model will be downloaded on first use."
echo
read -r -p "Press Enter to close this window..."
