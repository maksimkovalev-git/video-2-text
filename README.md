# Local Video to Text

Локальная пакетная транскрибация через `faster-whisper` (`large-v3`, язык — английский).

## Быстрый старт

1. На новом Mac запустите `_00_setup_env.command`.
2. Положите аудио и видео в `01_inbox` — вложенные папки поддерживаются.
3. Запустите `Run Transcription.command`.

TXT сохраняется рядом с исходником и с тем же именем:

```text
01_inbox/project/meeting.mp4
01_inbox/project/meeting.txt
```

Если такой TXT уже существует, исходный файл пропускается. Модель загружается один раз на всю пачку.

## Служебные команды

- `_90_wipe_data.command` — после ввода `WIPE` переносит содержимое `01_inbox` в Корзину.
- `_99_destroy_env.command` — после ввода `DELETE` переносит `whisper-env` в Корзину.

Код и внешний кэш модели эти команды не удаляют.

## Дополнительный запуск

```bash
source whisper-env/bin/activate
python transcribe.py --help
```

Полезные варианты:

```bash
# Строго офлайн, если модель уже скачана
python transcribe.py --offline

# Автоопределение языка
python transcribe.py --language auto

# Результаты отдельно от видео; вложенная структура сохранится
python transcribe.py --output-dir transcripts
```

Видео и транскрипты никуда не загружаются. Интернет требуется для установки зависимостей и первого скачивания модели.
