#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$PROJECT_DIR/whisper-env"

clear
echo "Local Video to Text — Destroy"
echo "============================="
echo
echo "Будет удалено только Python-окружение:"
echo "$ENV_DIR"
echo
echo "Видео, транскрипты, исходный код и кэш модели затронуты не будут."
echo
read -r -p "Введите DELETE для подтверждения: " CONFIRMATION

if [ "$CONFIRMATION" != "DELETE" ]; then
    echo
    echo "Отменено. Ничего не изменено."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 0
fi

if [ ! -e "$ENV_DIR" ]; then
    echo
    echo "Окружение whisper-env уже отсутствует."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 0
fi

if [ ! -d "$ENV_DIR" ] || [ ! -f "$ENV_DIR/pyvenv.cfg" ]; then
    echo
    echo "Ошибка: цель не похожа на Python-окружение. Она оставлена без изменений."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

TRASH_DIR="$HOME/.Trash"
TRASH_TARGET="$TRASH_DIR/video-2-text-whisper-env-$(date +%Y%m%d-%H%M%S)"

if [ -d "$TRASH_DIR" ] && mv "$ENV_DIR" "$TRASH_TARGET"; then
    echo
    echo "Окружение перемещено в Корзину:"
    echo "$TRASH_TARGET"
    echo "Его можно восстановить до очистки Корзины."
else
    echo
    echo "Не удалось переместить окружение в Корзину. Ничего специально не удалялось."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

echo
read -r -p "Нажмите Enter, чтобы закрыть окно..."
