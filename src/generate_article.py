#!/usr/bin/env python3
"""Generate local articles and summaries from transcript chunks with MLX."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_DIR / "llm" / "config.yaml"
PROMPTS_DIR = PROJECT_DIR / "llm" / "prompts"


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
        stamp = datetime.now().astimezone().strftime("article_%Y%m%d-%H%M%S")
        path = logs_dir / f"{stamp}-{os.getpid()}.log"
        log_file = path.open("a", encoding="utf-8", buffering=1)
    except OSError as exc:
        print(f"Warning: could not create article log: {exc}", file=sys.stderr)
        return None
    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate local articles from transcript JSONL chunks with MLX.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", nargs="?", type=Path, default=PROJECT_DIR / "01_inbox",
        help="chunks JSONL file or directory",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace notes, article, and summary")
    return parser.parse_args()


def load_config() -> dict[str, Any]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    required = {
        "model", "temperature", "top_p", "max_tokens", "chunk_notes_tokens",
        "consolidation_tokens", "summary_tokens", "max_input_chars",
    }
    if not isinstance(config, dict) or required - config.keys():
        missing = required - config.keys() if isinstance(config, dict) else required
        raise ValueError(f"invalid LLM config; missing: {', '.join(sorted(missing))}")
    return config


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def collect_sources(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(
        input_path.rglob("*.chunks.jsonl"),
        key=lambda path: str(path.relative_to(input_path)).lower(),
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not all(key in row for key in ("id", "start", "end", "text")):
            raise ValueError(f"missing fields on line {number}")
        rows.append(row)
    return rows


def output_paths(source: Path) -> tuple[Path, Path, Path]:
    name = source.name.removesuffix(".chunks.jsonl")
    return (
        source.with_name(f"{name}.notes.jsonl"),
        source.with_name(f"{name}.article.md"),
        source.with_name(f"{name}.summary.md"),
    )


def format_time(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clean_response(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text.startswith("```markdown") and text.endswith("```"):
        text = text[len("```markdown"):-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    return text


def make_generator(model: Any, tokenizer: Any, config: dict[str, Any]) -> Callable[[str, int], str]:
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

    sampler = make_sampler(temp=float(config["temperature"]), top_p=float(config["top_p"]))

    def run(prompt_text: str, max_tokens: int) -> str:
        messages = [{"role": "user", "content": prompt_text}]
        try:
            prompt = tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, enable_thinking=False,
            )
        except TypeError:
            prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        response = generate(
            model, tokenizer, prompt=prompt, max_tokens=max_tokens,
            sampler=sampler, verbose=False,
        )
        return clean_response(response)

    return run


def load_existing_notes(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    notes: dict[str, dict[str, Any]] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not all(key in row for key in ("id", "start", "end", "notes")):
            raise ValueError(f"invalid cached notes on line {number}")
        notes[str(row["id"])] = row
    return notes


def append_note(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")


def group_by_size(texts: list[str], max_chars: int) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    size = 0
    for text in texts:
        if current and size + len(text) > max_chars:
            groups.append(current)
            current = []
            size = 0
        current.append(text)
        size += len(text)
    if current:
        groups.append(current)
    return groups


def reduce_notes(
    notes: list[str], generate_text: Callable[[str, int], str],
    prompt: str, max_chars: int, max_tokens: int,
) -> list[str]:
    round_number = 0
    current = notes
    while sum(len(text) for text in current) > max_chars or len(current) > 1:
        groups = group_by_size(current, max_chars)
        if len(groups) == 1 and len(current) == 1:
            break
        round_number += 1
        print(f"Consolidation round {round_number}: {len(current)} items -> {len(groups)} groups")
        reduced = []
        for number, group in enumerate(groups, start=1):
            print(f"  Generating group {number}/{len(groups)}...")
            reduced.append(generate_text(f"{prompt}\n\nSOURCE NOTES:\n\n" + "\n\n".join(group), max_tokens))
        if len(reduced) >= len(current) and len(reduced) > 1:
            # Force progress when every source item already fills a whole group.
            paired = ["\n\n".join(reduced[i:i + 2]) for i in range(0, len(reduced), 2)]
            current = paired
        else:
            current = reduced
    return current


def process_source(
    source: Path, generate_text: Callable[[str, int], str],
    config: dict[str, Any], prompts: dict[str, str], overwrite: bool,
) -> str:
    notes_path, article_path, summary_path = output_paths(source)
    if article_path.exists() and summary_path.exists() and not overwrite:
        return "skipped"

    chunks = read_jsonl(source)
    if not chunks:
        raise ValueError("no chunks found")
    if overwrite:
        notes_path.write_text("", encoding="utf-8")
        existing: dict[str, dict[str, Any]] = {}
    else:
        existing = load_existing_notes(notes_path)

    notes: list[str] = []
    for number, chunk in enumerate(chunks, start=1):
        chunk_id = str(chunk["id"])
        if chunk_id in existing:
            note = existing[chunk_id]["notes"]
            print(f"  Notes {number}/{len(chunks)}: cached")
        else:
            print(f"  Notes {number}/{len(chunks)}: generating...")
            time_range = f"{format_time(float(chunk['start']))}–{format_time(float(chunk['end']))}"
            request = (
                f"{prompts['chunk']}\n\nSOURCE TIME RANGE: {time_range}\n\n"
                f"TRANSCRIPT:\n{chunk['text']}"
            )
            note = generate_text(request, int(config["chunk_notes_tokens"]))
            append_note(notes_path, {
                "id": chunk_id, "start": chunk["start"], "end": chunk["end"], "notes": note,
            })
        notes.append(note)

    consolidated = reduce_notes(
        notes, generate_text, prompts["consolidate"],
        int(config["max_input_chars"]), int(config["consolidation_tokens"]),
    )
    source_material = "\n\n".join(consolidated)
    print("  Generating article...")
    article = generate_text(
        f"{prompts['article']}\n\nSOURCE NOTES:\n\n{source_material}",
        int(config["max_tokens"]),
    )
    article_path.write_text(f"# {source.name.removesuffix('.chunks.jsonl')}\n\n{article}\n", encoding="utf-8")

    print("  Generating summary...")
    summary = generate_text(
        f"{prompts['summary']}\n\nARTICLE:\n\n{article}",
        int(config["summary_tokens"]),
    )
    summary_path.write_text(
        f"# {source.name.removesuffix('.chunks.jsonl')} — Summary\n\n{summary}\n",
        encoding="utf-8",
    )
    return "processed"


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

    try:
        config = load_config()
        prompts = {name: load_prompt(name) for name in ("chunk", "consolidate", "article", "summary")}
        sources = collect_sources(input_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    jobs = [source for source in sources if args.overwrite or not all(path.exists() for path in output_paths(source)[1:])]
    if not jobs:
        print("Nothing new to generate.")
        return 0

    print(f"Started: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Files to generate: {len(jobs)}")
    print(f"Loading local model: {config['model']}")
    try:
        from mlx_lm import load

        model, tokenizer = load(config["model"])
        generate_text = make_generator(model, tokenizer, config)
    except Exception as exc:
        print(f"Error: could not load local model: {exc}", file=sys.stderr)
        print("Run maintenance/_10_setup_llm.command first.", file=sys.stderr)
        return 1

    processed = failed = 0
    for number, source in enumerate(jobs, start=1):
        file_started = time.monotonic()
        print(f"\n[{number}/{len(jobs)}] {source.name}")
        try:
            result = process_source(source, generate_text, config, prompts, args.overwrite)
            processed += result == "processed"
        except KeyboardInterrupt:
            print("\nCancelled. Generated notes remain available for the next run.", file=sys.stderr)
            return 130
        except Exception as exc:
            failed += 1
            print(f"Error: {source.name}: {exc}", file=sys.stderr)
        finally:
            print(f"File time: {time.monotonic() - file_started:.1f}s")

    print(f"\nDone. Processed: {processed}; failed: {failed}; total: {time.monotonic() - started:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
