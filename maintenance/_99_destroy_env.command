#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$PROJECT_DIR/whisper-env"

clear
echo "Local Video to Text — Destroy"
echo "============================="
echo
echo "Only this Python environment will be moved to Trash:"
echo "$ENV_DIR"
echo
echo "Videos, transcripts, source code, and the model cache will not be affected."
echo
read -r -p "Type DELETE to confirm: " CONFIRMATION

if [ "$CONFIRMATION" != "DELETE" ]; then
    echo
    echo "Cancelled. Nothing was changed."
    read -r -p "Press Enter to close this window..."
    exit 0
fi

if [ ! -e "$ENV_DIR" ]; then
    echo
    echo "The whisper-env environment is already absent."
    read -r -p "Press Enter to close this window..."
    exit 0
fi

if [ ! -d "$ENV_DIR" ] || [ ! -f "$ENV_DIR/pyvenv.cfg" ]; then
    echo
    echo "Error: the target does not look like a Python environment. It was left unchanged."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

TRASH_DIR="$HOME/.Trash"
TRASH_TARGET="$TRASH_DIR/video-2-text-whisper-env-$(date +%Y%m%d-%H%M%S)"

if [ -d "$TRASH_DIR" ] && mv "$ENV_DIR" "$TRASH_TARGET"; then
    echo
    echo "The environment was moved to Trash:"
    echo "$TRASH_TARGET"
    echo "It can be restored until Trash is emptied."
else
    echo
    echo "Could not move the environment to Trash. Nothing was deliberately deleted."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

echo
read -r -p "Press Enter to close this window..."
