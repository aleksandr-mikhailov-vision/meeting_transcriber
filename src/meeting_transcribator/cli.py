"""Command-line interface for the Meeting Transcribator.

Usage examples:
    transcribe recordings/standup.m4a
    transcribe --all
    transcribe --all --provider mistral --language en
    transcribe --all --overwrite --model gpt-4o-mini-transcribe
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .providers import PROVIDERS
from .transcriber import transcribe_file

# Audio extensions providers accept (we normalize via ffmpeg regardless).
AUDIO_EXTS = {".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".wav", ".webm", ".flac", ".ogg", ".oga"}

DEFAULT_PROVIDER = "openai"

DEFAULT_RECORDINGS = Path("recordings")
DEFAULT_OUTPUTS = Path("outputs")


def output_path_for(src: str | Path, recordings_dir: Path, outputs_dir: Path) -> Path:
    """Map an input recording to its transcript path under ``outputs_dir``.

    Files inside ``recordings_dir`` mirror their relative sub-path; files from
    anywhere else map to ``outputs_dir/<stem>.md`` by name.
    """
    src = Path(src)
    try:
        rel = src.resolve().relative_to(recordings_dir.resolve())
        return (outputs_dir / rel).with_suffix(".md")
    except ValueError:
        return (outputs_dir / src.name).with_suffix(".md")


def discover(recordings_dir: Path, outputs_dir: Path, *, overwrite: bool) -> list[Path]:
    """Return recordings in ``recordings_dir`` that still need a transcript
    (or all of them when ``overwrite`` is set), sorted by name."""
    found = sorted(
        p for p in recordings_dir.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )
    if overwrite:
        return found
    return [p for p in found if not output_path_for(p, recordings_dir, outputs_dir).exists()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Transcribe audio recordings to raw-text .md files via OpenAI or Mistral.",
    )
    parser.add_argument("paths", nargs="*", help="Specific audio file(s) to transcribe.")
    parser.add_argument(
        "--all", action="store_true", help="Transcribe every recording in the recordings folder."
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Re-transcribe even if a transcript already exists."
    )
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        default=os.environ.get("TRANSCRIBE_PROVIDER", DEFAULT_PROVIDER),
        help=f"Transcription provider (default: {DEFAULT_PROVIDER}).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("TRANSCRIBE_MODEL"),
        help="Transcription model. Default depends on provider "
        f"({', '.join(f'{n}={c.default_model}' for n, c in sorted(PROVIDERS.items()))}).",
    )
    parser.add_argument(
        "--language",
        default=os.environ.get("TRANSCRIBE_LANGUAGE"),
        help="ISO-639-1 language hint (e.g. en, fr). Optional; improves accuracy.",
    )
    parser.add_argument(
        "--recordings-dir", type=Path, default=DEFAULT_RECORDINGS, help="Input folder (default: recordings)."
    )
    parser.add_argument(
        "--outputs-dir", type=Path, default=DEFAULT_OUTPUTS, help="Output folder (default: outputs)."
    )
    return parser


def _disambiguate(dest: Path, used: set[Path]) -> Path:
    """Return a transcript path not already claimed this run, appending -2, -3,
    ... so two inputs sharing a basename don't silently overwrite each other."""
    if dest not in used:
        return dest
    n = 2
    while dest.with_stem(f"{dest.stem}-{n}") in used:
        n += 1
    return dest.with_stem(f"{dest.stem}-{n}")


def _make_provider(name: str):
    """Construct the selected provider, failing clearly if its key is missing."""
    cls = PROVIDERS[name]
    if not os.environ.get(cls.env_key):
        print(
            f"ERROR: {cls.env_key} is not set. Copy .env.example to .env and add your key,\n"
            f"       or set the {cls.env_key} environment variable.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return cls()


def main(argv: list[str] | None = None) -> int:
    from dotenv import find_dotenv, load_dotenv

    # Find .env from the current working directory (where recordings/ live),
    # not relative to this source file. No-op if there's no .env.
    load_dotenv(find_dotenv(usecwd=True))
    args = _build_parser().parse_args(argv)

    if args.all:
        targets = discover(args.recordings_dir, args.outputs_dir, overwrite=args.overwrite)
    else:
        targets = [Path(p) for p in args.paths]

    if not targets:
        if args.all:
            print("Nothing to do: no new recordings found (use --overwrite to redo existing).")
            return 0
        print("ERROR: provide audio file path(s) or use --all.", file=sys.stderr)
        return 2

    provider = _make_provider(args.provider)
    model = args.model or provider.default_model
    print(f"Provider: {provider.name}  Model: {model}")

    failures = 0
    used: set[Path] = set()
    for i, src in enumerate(targets, start=1):
        dest = output_path_for(src, args.recordings_dir, args.outputs_dir)
        unique = _disambiguate(dest, used)
        if unique != dest:
            print(f"    note: '{dest.name}' already used this run; writing to '{unique.name}'")
        dest = unique
        used.add(dest)
        print(f"[{i}/{len(targets)}] {src} -> {dest}")
        try:
            transcribe_file(
                src,
                dest,
                provider=provider,
                model=model,
                language=args.language,
                on_progress=lambda c, total: print(f"    chunk {c}/{total}...", flush=True),
            )
            print(f"    done: {dest}")
        except Exception as exc:  # noqa: BLE001 - surface per-file errors, keep going
            failures += 1
            print(f"    FAILED: {exc}", file=sys.stderr)

    if failures:
        print(f"\nCompleted with {failures} failure(s).", file=sys.stderr)
        return 1
    print(f"\nAll {len(targets)} recording(s) transcribed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
