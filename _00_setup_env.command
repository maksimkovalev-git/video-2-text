#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_DIR="$PROJECT_DIR/whisper-env"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

clear
echo "Local Video to Text — Setup"
echo "==========================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "Ошибка: Python 3 не найден."
    echo "Установите Python 3 и запустите Setup.command ещё раз."
    echo
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

if [ ! -f "$REQUIREMENTS" ]; then
    echo "Ошибка: не найден файл requirements.txt"
    echo
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

if [ -d "$ENV_DIR" ] && [ ! -f "$ENV_DIR/pyvenv.cfg" ]; then
    echo "Ошибка: папка whisper-env существует, но не похожа на Python-окружение."
    echo "Она оставлена без изменений."
    echo
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

if [ ! -d "$ENV_DIR" ]; then
    echo "Создаю локальное Python-окружение..."
    if ! python3 -m venv "$ENV_DIR"; then
        echo "Ошибка при создании окружения."
        read -r -p "Нажмите Enter, чтобы закрыть окно..."
        exit 1
    fi
else
    echo "Окружение whisper-env уже существует — обновляю зависимости."
fi

echo "Устанавливаю зависимости..."
if ! "$ENV_DIR/bin/python" -m pip install --upgrade pip; then
    echo "Ошибка при обновлении pip. Проверьте подключение к интернету."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

if ! "$ENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS"; then
    echo "Ошибка при установке зависимостей. Проверьте подключение к интернету."
    read -r -p "Нажмите Enter, чтобы закрыть окно..."
    exit 1
fi

echo
echo "Готово. Теперь можно запускать Run Transcription.command"
echo "Модель large-v3 загрузится при первой транскрибации."
echo
read -r -p "Нажмите Enter, чтобы закрыть окно..."
