#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INBOX_DIR="$PROJECT_DIR/01_inbox"

clear
echo "Local Video to Text — Wipe Data"
echo "==============================="
echo
echo "The contents of 01_inbox will be moved to Trash:"
echo "$INBOX_DIR"
echo
echo "The source code, Python environment, and model cache will not be affected."
echo
read -r -p "Type WIPE to confirm: " CONFIRMATION

if [ "$CONFIRMATION" != "WIPE" ]; then
    echo
    echo "Cancelled. Nothing was changed."
    read -r -p "Press Enter to close this window..."
    exit 0
fi

if [ ! -d "$INBOX_DIR" ]; then
    echo
    echo "The 01_inbox folder does not exist. Nothing to clean."
    read -r -p "Press Enter to close this window..."
    exit 0
fi

ITEM_COUNT=$(find "$INBOX_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' | wc -l | tr -d ' ')
if [ "$ITEM_COUNT" -eq 0 ]; then
    echo
    echo "The 01_inbox folder is already empty."
    read -r -p "Press Enter to close this window..."
    exit 0
fi

TRASH_DIR="$HOME/.Trash"
TRASH_TARGET="$TRASH_DIR/video-2-text-data-$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$TRASH_DIR" ] || ! mkdir "$TRASH_TARGET"; then
    echo
    echo "Could not create a destination in Trash. No data was changed."
    read -r -p "Press Enter to close this window..."
    exit 1
fi

FAILED=0
while IFS= read -r -d '' ITEM; do
    if ! mv "$ITEM" "$TRASH_TARGET/"; then
        FAILED=1
    fi
done < <(find "$INBOX_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -print0)

echo
if [ "$FAILED" -eq 0 ]; then
    echo "Done. Items moved: $ITEM_COUNT"
    echo "The data is in Trash:"
    echo "$TRASH_TARGET"
else
    echo "Some items could not be moved. Check 01_inbox and Trash."
fi

echo
read -r -p "Press Enter to close this window..."
exit "$FAILED"
