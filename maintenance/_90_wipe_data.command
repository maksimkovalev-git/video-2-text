#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INBOX_DIR="$PROJECT_DIR/01_inbox"

clear
echo "Local Video to Text — Wipe Data"
echo "==============================="
echo
echo "Содержимое 01_inbox будет перемещено в Корзину:"
echo "$INBOX_DIR"
echo
echo "Код, Python-окружение и кэш модели затронуты не будут."
echo
read -r -p "Введите WIPE для подтверждения: " CONFIRMATION

if [ "$CONFIRMATION" != "WIPE" ]; then
    echo
    echo "Отменено. Ничего не изменено."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 0
fi

if [ ! -d "$INBOX_DIR" ]; then
    echo
    echo "Папка 01_inbox отсутствует. Очищать нечего."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 0
fi

ITEM_COUNT=$(find "$INBOX_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' | wc -l | tr -d ' ')
if [ "$ITEM_COUNT" -eq 0 ]; then
    echo
    echo "Папка 01_inbox уже пуста."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 0
fi

TRASH_DIR="$HOME/.Trash"
TRASH_TARGET="$TRASH_DIR/video-2-text-data-$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$TRASH_DIR" ] || ! mkdir "$TRASH_TARGET"; then
    echo
    echo "Не удалось подготовить папку в Корзине. Данные не изменены."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
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
    echo "Готово. Перемещено объектов: $ITEM_COUNT"
    echo "Данные находятся в Корзине:"
    echo "$TRASH_TARGET"
else
    echo "Некоторые объекты переместить не удалось. Проверьте 01_inbox и Корзину."
fi

echo
read -r -p "Нажмите Enter, чтобы закрыть окно..."
exit "$FAILED"
