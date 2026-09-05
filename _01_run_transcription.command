#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/whisper-env/bin/python"

clear
echo "Local Video to Text"
echo "==================="
echo

if [ ! -x "$PYTHON" ]; then
    echo "Error: the whisper-env Python environment was not found."
    echo "Expected path: $PYTHON"
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
"$PYTHON" src/transcribe.py --profile normal
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
    echo "Processing completed."
else
    echo "Processing failed (exit code $STATUS)."
fi
echo
read -r -p "Press Enter to close this window..."
exit "$STATUS"
