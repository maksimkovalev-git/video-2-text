#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${1:-$PROJECT_DIR/01_inbox}"
OUTPUT_DIR="${2:-$PROJECT_DIR/10_output}"

clear
echo "Transfer Results"
echo "================"
echo
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo

if [ ! -d "$SOURCE_DIR" ]; then
    echo "No source folder found. Nothing to transfer."
    echo
    read -r -p "Press Enter to close this window..."
    exit 0
fi

if ! command -v rsync >/dev/null 2>&1; then
    echo "Error: rsync was not found."
    echo
    read -r -p "Press Enter to close this window..."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

if rsync -a --prune-empty-dirs \
    --include='*/' \
    --include='*.txt' \
    --include='*.readable.md' \
    --include='*.chunks.jsonl' \
    --include='*.notes.jsonl' \
    --include='*.article.md' \
    --include='*.summary.md' \
    --exclude='*' \
    "$SOURCE_DIR/" "$OUTPUT_DIR/"; then
    ITEM_COUNT=$(find "$OUTPUT_DIR" -type f ! -name '.gitkeep' | wc -l | tr -d ' ')
    echo "Transfer complete. Result files in 10_output: $ITEM_COUNT"
else
    STATUS=$?
    echo "Transfer failed (exit code $STATUS)."
    echo
    read -r -p "Press Enter to close this window..."
    exit "$STATUS"
fi

echo
read -r -p "Press Enter to close this window..."
