# Local Video to Text

Local batch transcription powered by `faster-whisper` (`large-v3`, English by default).

## Quick start

1. Run `maintenance/_00_setup_env.command`.
2. Put audio and video files in `01_inbox`. Nested folders are supported.
3. Run `_01_run_transcription.command` (uses the `normal` profile).

Each transcript is saved next to its source file with the same base name:

```text
01_inbox/project/meeting.mp4
01_inbox/project/meeting.txt
```

If the matching TXT already exists, the source file is skipped. The model is loaded only once for the entire batch.
The terminal shows start/end times, elapsed time, estimated time remaining, and total batch duration.
Every run is also recorded in a timestamped `logs/*.log` file. Logs stay local and are ignored by Git.

## Process transcripts

Run `_10_process_transcripts.command` after transcription. It recursively converts each raw timecoded TXT into:

- `meeting.readable.md` — readable timecoded paragraphs;
- `meeting.chunks.jsonl` — overlapping chunks with source metadata for a knowledge base.

Raw TXT files are never modified. Existing processed outputs are skipped. The process is local, deterministic, and does not use an LLM.

## Local LLM

Run `maintenance/_10_setup_llm.command` to create a separate `llm-env`, install Apple MLX, download the configured model, and verify that it loads. The setup is console-based and requires no GUI, account, or background server.

The default model is `mlx-community/Qwen3-14B-4bit` (approximately 8.3 GB). Its settings are stored in `llm/config.yaml`. Models are downloaded once and then loaded from the local Hugging Face cache.

## Generate articles

After post-processing, run `_20_generate_article.command`. It uses the local MLX model to recursively convert every `*.chunks.jsonl` into:

- `meeting.notes.jsonl` — resumable source notes with timestamps;
- `meeting.article.md` — a coherent article with source time ranges;
- `meeting.summary.md` — a concise overview.

Existing articles are skipped. If generation is interrupted, completed notes are reused on the next run. Raw transcripts and chunks are never modified. Prompts are stored in `llm/prompts/` and all processing stays local.

## Transfer results

Run `_30_transfer_results.command` to copy all available result artifacts from `01_inbox` to `10_output` while preserving the nested folder structure. It copies raw TXT, readable Markdown, chunks, notes, articles, and summaries—but not media or logs.

Missing artifact types are expected and are not treated as errors. Existing destination files are updated; source files are never moved or deleted. The contents of `10_output` stay local and are ignored by Git.

## Maintenance commands

- `maintenance/_90_wipe_data.command` moves the contents of `01_inbox` to Trash after you enter `WIPE`.
- `maintenance/_99_destroy_env.command` moves `whisper-env` to Trash after you enter `DELETE`.

Neither command removes the source code or the external model cache.

## Profiles

| Profile | Model | Use case |
|---|---|---|
| `quality` | `large-v3` | Best accuracy, slowest |
| `normal` | `large-v3` | Balanced processing; used by `_01_run_transcription.command` |
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
