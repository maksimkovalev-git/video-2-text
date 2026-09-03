#!/usr/bin/env python3
"""Transcribe audio/video locally with faster-whisper."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


SUPPORTED_FORMATS = ("txt", "srt", "vtt", "json")
SUPPORTED_MEDIA = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local audio/video transcription with faster-whisper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", nargs="?", type=Path,
        default=Path(__file__).resolve().parent.parent / "01_inbox",
        help="input file or inbox directory")
    parser.add_argument("--model", default="large-v3", help="Whisper model name or local model path")
    parser.add_argument(
        "--language",
        default="en",
        help="language code (en, ru, ...) or 'auto' for detection",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=SUPPORTED_FORMATS,
        help="output format; repeat for several formats (default: txt)",
    )
    parser.add_argument("--output-dir", type=Path, help="directory for output files")
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--compute-type", default="auto", help="auto, int8, float16, ...")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true", help="disable silence filtering")
    parser.add_argument("--no-timestamps", action="store_true", help="omit timestamps in TXT")
    parser.add_argument("--offline", action="store_true", help="use only an already cached/local model")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")
    return parser.parse_args()


def timestamp(seconds: float, separator: str = ",") -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"


def output_paths(source: Path, output_dir: Path, formats: list[str]) -> dict[str, Path]:
    return {fmt: output_dir / f"{source.stem}.{fmt}" for fmt in formats}


def write_outputs(
    paths: dict[str, Path],
    segments: list[dict[str, Any]],
    metadata: dict[str, Any],
    no_timestamps: bool,
) -> None:
    if "txt" in paths:
        with paths["txt"].open("w", encoding="utf-8") as file:
            for item in segments:
                prefix = "" if no_timestamps else f"[{item['start']:.1f} - {item['end']:.1f}] "
                file.write(f"{prefix}{item['text']}\n")

    if "srt" in paths:
        with paths["srt"].open("w", encoding="utf-8") as file:
            for number, item in enumerate(segments, start=1):
                file.write(
                    f"{number}\n{timestamp(item['start'])} --> {timestamp(item['end'])}\n"
                    f"{item['text']}\n\n"
                )

    if "vtt" in paths:
        with paths["vtt"].open("w", encoding="utf-8") as file:
            file.write("WEBVTT\n\n")
            for item in segments:
                file.write(
                    f"{timestamp(item['start'], '.')} --> {timestamp(item['end'], '.')}\n"
                    f"{item['text']}\n\n"
                )

    if "json" in paths:
        payload = {**metadata, "segments": segments}
        paths["json"].write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def collect_sources(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(
        (path for path in input_path.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_MEDIA),
        key=lambda path: str(path.relative_to(input_path)).lower(),
    )


def main() -> int:
    args = parse_args()
    input_path = args.input.expanduser().resolve()

    if not input_path.exists():
        print(f"Error: input file or directory does not exist: {input_path}", file=sys.stderr)
        return 2
    if not input_path.is_file() and not input_path.is_dir():
        print(f"Error: unsupported input: {input_path}", file=sys.stderr)
        return 2
    if args.beam_size < 1:
        print("Error: --beam-size must be at least 1", file=sys.stderr)
        return 2

    formats = list(dict.fromkeys(args.formats or ["txt"]))
    sources = collect_sources(input_path)
    if not sources:
        print(f"Nothing to transcribe in: {input_path}")
        return 0

    jobs: list[tuple[Path, dict[str, Path]]] = []
    for source in sources:
        if args.output_dir and input_path.is_dir():
            relative_parent = source.parent.relative_to(input_path)
            output_dir = args.output_dir.expanduser().resolve() / relative_parent
        else:
            output_dir = (args.output_dir or source.parent).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = output_paths(source, output_dir, formats)
        txt_marker = output_dir / f"{source.stem}.txt"
        if not args.overwrite and (txt_marker.exists() or any(path.exists() for path in paths.values())):
            print(f"Skip: {source.name} (text already exists)")
            continue
        jobs.append((source, paths))

    if not jobs:
        print("Nothing new to transcribe.")
        return 0

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    try:
        from faster_whisper import WhisperModel

        print(f"Files to transcribe: {len(jobs)}")
        print(f"Loading model: {args.model}{' (offline)' if args.offline else ''}")
        model = WhisperModel(
            args.model,
            device=args.device,
            compute_type=args.compute_type,
            local_files_only=args.offline,
        )
        failures = 0
        for number, (source, paths) in enumerate(jobs, start=1):
            try:
                print(f"\n[{number}/{len(jobs)}] Transcribing: {source.name}")
                segment_stream, info = model.transcribe(
                    str(source),
                    language=None if args.language.lower() == "auto" else args.language,
                    vad_filter=not args.no_vad,
                    beam_size=args.beam_size,
                )
                items: list[dict[str, Any]] = []
                duration = float(info.duration or 0)
                for segment in segment_stream:
                    text = segment.text.strip()
                    if not text:
                        continue
                    items.append({"start": segment.start, "end": segment.end, "text": text})
                    progress = min(100.0, segment.end / duration * 100) if duration else 0
                    print(f"\rProgress: {progress:5.1f}%  {timestamp(segment.end, '.')} ", end="", flush=True)
                print()
                metadata = {
                    "source": source.name, "model": args.model, "language": info.language,
                    "language_probability": info.language_probability, "duration_seconds": duration,
                }
                write_outputs(paths, items, metadata, args.no_timestamps)
                for path in paths.values():
                    print(f"Saved: {path}")
            except Exception as exc:
                failures += 1
                print(f"Error: failed to transcribe {source.name}: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nCancelled. No output was written.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: transcription failed: {exc}", file=sys.stderr)
        if args.offline:
            print("Hint: check that the selected model is already cached locally.", file=sys.stderr)
        return 1

    print(f"\nDone. Successful: {len(jobs) - failures}; failed: {failures}.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
