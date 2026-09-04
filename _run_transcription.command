#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/whisper-env/bin/python"

clear
echo "Local Video to Text"
echo "==================="
echo

if [ ! -x "$PYTHON" ]; then
    echo "Ошибка: не найдено Python-окружение whisper-env."
    echo "Ожидаемый путь: $PYTHON"
    echo
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

cd "$PROJECT_DIR" || exit 1
"$PYTHON" src/transcribe.py --profile normal
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
    echo "Обработка завершена."
else
    echo "Обработка завершилась с ошибкой (код $STATUS)."
fi
echo
read -r -p "Нажмите Enter, чтобы закрыть окно..."
exit "$STATUS"
