#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/llm-env/bin/python"

clear
echo "Local Article Generation"
echo "========================"
echo

if [ ! -x "$PYTHON" ]; then
    echo "Error: the llm-env Python environment was not found."
    echo "Run maintenance/_10_setup_llm.command first."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
"$PYTHON" src/generate_article.py
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
    echo "Article generation completed."
else
    echo "Article generation failed (exit code $STATUS)."
fi
echo
read -r -p "Press Enter to close this window..."
exit "$STATUS"
