# Local Video to Text

Local batch transcription powered by `faster-whisper` (`large-v3`, English by default).

## Quick start

1. Run `maintenance/_00_setup_env.command`.
2. Put audio and video files in `01_inbox`. Nested folders are supported.
3. Run `_run_transcription.command` (uses the `normal` profile).

Each transcript is saved next to its source file with the same base name:

```text
01_inbox/project/meeting.mp4
01_inbox/project/meeting.txt
```

If the matching TXT already exists, the source file is skipped. The model is loaded only once for the entire batch.
The terminal shows start/end times, elapsed time, estimated time remaining, and total batch duration.
Every run is also recorded in a timestamped `logs/*.log` file. Logs stay local and are ignored by Git.

## Maintenance commands

- `maintenance/_90_wipe_data.command` moves the contents of `01_inbox` to Trash after you enter `WIPE`.
- `maintenance/_99_destroy_env.command` moves `whisper-env` to Trash after you enter `DELETE`.

Neither command removes the source code or the external model cache.

## Profiles

| Profile | Model | Use case |
|---|---|---|
| `quality` | `large-v3` | Best accuracy, slowest |
| `normal` | `large-v3` | Balanced processing; used by `_run_transcription.command` |
| `fast` | `turbo` | Fastest, with some accuracy trade-off |

Profile settings live in `profiles/*.yaml`. Add another YAML file to create a profile without changing the Python code. Models are downloaded on first use: `quality` and `normal` share `large-v3`, while `fast` uses a separate `turbo` model.

```bash
python src/transcribe.py --profile normal
python src/transcribe.py --profile fast
```

## Command-line options

```bash
source whisper-env/bin/activate
python src/transcribe.py --help
```

Useful examples:

```bash
# Work strictly offline with an already downloaded model
python src/transcribe.py --offline

# Detect the spoken language automatically
python src/transcribe.py --language auto

# Store transcripts separately while preserving the folder structure
python src/transcribe.py --output-dir transcripts
```

Audio, video, and transcripts are processed locally and are not uploaded to third-party services. An internet connection is required to install dependencies and download the model for the first time.
