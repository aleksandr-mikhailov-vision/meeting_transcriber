# Meeting Transcribator Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking. TDD, DRY, YAGNI.

**Goal:** A backend Python tool that transcribes `.m4a` (and other audio) recordings to raw-text `.md` files via the OpenAI transcription API.

**Architecture:** A small `uv`-managed package. Audio is normalized to 16 kHz mono and split into size-safe chunks with a bundled ffmpeg (`imageio-ffmpeg`), each chunk is sent to OpenAI's transcription endpoint, and the chunk texts are concatenated into one `.md` per recording. A CLI drives single-file and batch (`--all`) runs; it is the surface Claude calls and humans can use directly.

**Tech Stack:** Python 3.11+, `uv`, `openai` SDK, `imageio-ffmpeg` (bundled ffmpeg binary), `python-dotenv`, `pytest`.

**Design source:** User chat spec (2026-05-29). Defaults: model `gpt-4o-transcribe`; both `recordings/` and `outputs/` gitignored.

---

## Why chunking

OpenAI's audio endpoint rejects uploads over **25 MB**. Corporate meetings routinely exceed that. The tool always pre-processes audio with ffmpeg: downmix to **16 kHz mono** (what the ASR uses internally — no transcription-quality loss) and segment into time-bounded chunks that stay well under the limit. mp3 (libmp3lame, ~32 kbps) is preferred; if that encoder is absent in the bundled ffmpeg, fall back to 16 kHz mono WAV with shorter segments. Both stay under 25 MB.

## File structure

```
meeting_transcribator/
├── pyproject.toml                       # uv project + deps + `transcribe` entry point
├── .gitignore                           # ignores recordings/*, outputs/*, .env, .venv
├── .env.example                         # OPENAI_API_KEY=...
├── README.md                            # human usage
├── CLAUDE.md                            # how Claude should run the tool in this folder
├── recordings/.gitkeep                  # m4a inputs live here (gitignored)
├── outputs/.gitkeep                     # .md transcripts land here (gitignored)
├── src/meeting_transcribator/
│   ├── __init__.py
│   ├── audio.py                         # ffmpeg locate + normalize/chunk
│   ├── transcriber.py                   # per-chunk OpenAI calls + concat + file orchestration
│   └── cli.py                           # argparse CLI, path mapping, --all discovery
└── tests/
    ├── test_cli.py                      # path mapping, --all skip-existing/--overwrite (mocked)
    ├── test_transcriber.py              # chunk-text concatenation + API args (mocked client)
    └── test_audio.py                    # real ffmpeg: synth tone → chunks (skip if no ffmpeg)
```

## Tasks

### Task 1: Project scaffold
- [ ] Create `pyproject.toml` (hatchling build, src layout, deps, `transcribe` script, pytest config).
- [ ] Create `.gitignore`, `.env.example`, `recordings/.gitkeep`, `outputs/.gitkeep`.
- [ ] `uv sync` succeeds and creates `.venv`.

### Task 2: `audio.py` — normalize + chunk (TDD)
- [ ] `get_ffmpeg()` returns the bundled ffmpeg exe path.
- [ ] `chunk_audio(src, workdir)` → list of chunk file paths, each 16 kHz mono, < 25 MB, ordered.
- [ ] Test: synthesize a ~65 s sine via ffmpeg, chunk at 30 s → ≥ 3 ordered chunks, each exists and < 25 MB. Skip if ffmpeg unavailable.

### Task 3: `transcriber.py` — OpenAI + orchestration (TDD)
- [ ] `transcribe_chunks(chunk_paths, *, model, language, client)` calls `client.audio.transcriptions.create` per chunk with `response_format="text"` and joins results with blank lines.
- [ ] `transcribe_file(src, dest, *, model, language, client)` chunks in a temp dir, transcribes, writes raw text to `dest`.
- [ ] Tests with a fake client: correct model/file/format per chunk; texts concatenated in order; `language` forwarded only when set.

### Task 4: `cli.py` — CLI (TDD)
- [ ] `output_path_for(src, recordings_dir, outputs_dir)` maps `recordings/x.m4a` → `outputs/x.md`.
- [ ] `discover(recordings_dir, outputs_dir, overwrite)` lists `*.m4a` lacking a transcript (or all if `--overwrite`).
- [ ] `main(argv)`: args `paths... | --all`, `--model`, `--language`, `--overwrite`; loads `.env`; constructs `OpenAI()`; calls `transcribe_file` for each; prints progress; clear error if `OPENAI_API_KEY` missing.
- [ ] Tests for `output_path_for`, `discover` skip-existing + `--overwrite` (no network).

### Task 5: Docs
- [ ] `README.md`: prerequisites (uv), setup (`.env`), usage (`uv run transcribe ...`, `--all`), how it handles long files, costs note.
- [ ] `CLAUDE.md`: exact commands Claude runs to transcribe one file or the whole `recordings/` folder.

### Task 6: Verify + ship
- [ ] `uv run pytest` green.
- [ ] code-reviewer pass; address findings.
- [ ] `git init`, commit (recordings/outputs ignored), create **private** repo via `gh`, push.
