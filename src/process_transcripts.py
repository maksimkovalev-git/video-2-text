#!/usr/bin/env python3
"""Create readable Markdown and retrieval chunks from raw transcripts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
TIMECODE_RE = re.compile(r"^\[(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\]\s*(.+)$")


class Tee:
    def __init__(self, terminal: Any, log_file: Any) -> None:
        self.terminal = terminal
        self.log_file = log_file

    def write(self, text: str) -> int:
        written = self.terminal.write(text)
        self.log_file.write(text)
        return written

    def flush(self) -> None:
        self.terminal.flush()
        self.log_file.flush()

    def isatty(self) -> bool:
        return self.terminal.isatty()


def setup_log() -> Path | None:
    try:
        logs_dir = PROJECT_DIR / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime("process_%Y%m%d-%H%M%S")
        path = logs_dir / f"{stamp}-{os.getpid()}.log"
        log_file = path.open("a", encoding="utf-8", buffering=1)
    except OSError as exc:
        print(f"Warning: could not create processing log: {exc}", file=sys.stderr)
        return None
    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert raw timecoded transcripts to readable Markdown and JSONL chunks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=PROJECT_DIR / "01_inbox",
        help="raw transcript file or directory",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace existing processed files")
    parser.add_argument("--max-seconds", type=float, default=75, help="target maximum block duration")
    parser.add_argument("--max-chars", type=int, default=1800, help="target maximum block length")
    parser.add_argument("--pause-seconds", type=float, default=3, help="start a block after this pause")
    return parser.parse_args()


def format_time(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_transcript(path: Path) -> tuple[list[dict[str, Any]], int]:
    segments: list[dict[str, Any]] = []
    ignored = 0
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = TIMECODE_RE.match(line)
        if not match:
            ignored += 1
            continue
        start, end, text = match.groups()
        segments.append({"start": float(start), "end": float(end), "text": text.strip()})
    return segments, ignored


def make_blocks(
    segments: list[dict[str, Any]], max_seconds: float, max_chars: int, pause_seconds: float,
) -> list[list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for segment in segments:
        split = bool(current) and (
            segment["start"] - current[-1]["end"] > pause_seconds
            or segment["end"] - current[0]["start"] > max_seconds
            or current_chars + len(segment["text"]) + 1 > max_chars
        )
        if split:
            blocks.append(current)
            current = []
            current_chars = 0
        current.append(segment)
        current_chars += len(segment["text"]) + 1
    if current:
        blocks.append(current)
    return blocks


def output_paths(source: Path) -> tuple[Path, Path]:
    return source.with_suffix(".readable.md"), source.with_suffix(".chunks.jsonl")


def write_readable(path: Path, source: Path, blocks: list[list[dict[str, Any]]]) -> None:
    lines = [f"# {source.stem}", "", f"Source: `{source.name}`", ""]
    for block in blocks:
        lines.extend([
            f"## {format_time(block[0]['start'])}–{format_time(block[-1]['end'])}",
            "",
            " ".join(segment["text"] for segment in block),
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_chunks(
    path: Path, source: Path, input_root: Path, blocks: list[list[dict[str, Any]]],
) -> None:
    try:
        source_name = str(source.relative_to(input_root))
    except ValueError:
        source_name = source.name
    with path.open("w", encoding="utf-8") as file:
        previous_last: dict[str, Any] | None = None
        for number, block in enumerate(blocks, start=1):
            chunk_segments = ([previous_last] if previous_last else []) + block
            payload = {
                "id": f"{source.stem}-{number:04d}",
                "source": source_name,
                "start": chunk_segments[0]["start"],
                "end": chunk_segments[-1]["end"],
                "text": " ".join(segment["text"] for segment in chunk_segments),
            }
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
            previous_last = block[-1]


def collect_transcripts(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob("*.txt"), key=lambda path: str(path.relative_to(input_path)).lower())


def main() -> int:
    args = parse_args()
    log_path = setup_log()
    if log_path:
        print(f"Log: {log_path}")
    started = time.monotonic()
    input_path = args.input.expanduser().resolve()
    if not input_path.exists():
        print(f"Error: input does not exist: {input_path}", file=sys.stderr)
        return 2
    if args.max_seconds <= 0 or args.max_chars <= 0 or args.pause_seconds < 0:
        print("Error: processing limits must be positive.", file=sys.stderr)
        return 2

    sources = collect_transcripts(input_path)
    print(f"Processing started: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Transcripts found: {len(sources)}")
    processed = skipped = failed = 0
    input_root = input_path if input_path.is_dir() else input_path.parent

    for number, source in enumerate(sources, start=1):
        readable_path, chunks_path = output_paths(source)
        if not args.overwrite and (readable_path.exists() or chunks_path.exists()):
            print(f"[{number}/{len(sources)}] Skip: {source.name} (processed output exists)")
            skipped += 1
            continue
        try:
            segments, ignored = parse_transcript(source)
            if not segments:
                print(f"[{number}/{len(sources)}] Skip: {source.name} (no timecoded segments)")
                skipped += 1
                continue
            blocks = make_blocks(segments, args.max_seconds, args.max_chars, args.pause_seconds)
            write_readable(readable_path, source, blocks)
            write_chunks(chunks_path, source, input_root, blocks)
            print(
                f"[{number}/{len(sources)}] Processed: {source.name} | "
                f"segments {len(segments)} | blocks {len(blocks)} | ignored lines {ignored}"
            )
            processed += 1
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"[{number}/{len(sources)}] Error: {source.name}: {exc}", file=sys.stderr)
            failed += 1

    elapsed = format_time(time.monotonic() - started)
    print(f"Done. Processed: {processed}; skipped: {skipped}; failed: {failed}; total: {elapsed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
