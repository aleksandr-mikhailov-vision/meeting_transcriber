# CLAUDE.md — operating notes for this repo

This is a backend tool that transcribes audio recordings to raw-text `.md` files via
the OpenAI or Mistral (Voxtral) API. You (Claude) are the primary driver: a human tells
you what to transcribe, and you run the command.

## How to transcribe

Recordings live in `recordings/`; transcripts are written to `outputs/<name>.md`.

```powershell
# A specific file the user names
uv run transcribe recordings/<file>.m4a

# Everything not yet transcribed (the usual batch ask)
uv run transcribe --all
```

- `--all` skips recordings that already have a transcript. Add `--overwrite` to redo them.
- **Provider rule:** mostly-French audio → Mistral (`--provider mistral`, Voxtral);
  English or any other language → OpenAI (`--provider openai`, the default
  `gpt-4o-transcribe`). This mirrors the VS Code buttons below. Override if the user
  says otherwise or only one key is configured.
- Use `--model ...` for a cheaper/specific model (`gpt-4o-mini-transcribe`, `whisper-1`,
  other Voxtral variants). Use `--language en` (or `fr`, etc.) if the user tells you the
  meeting language.
- Output is the raw transcript only — no summaries or formatting added (by design).
- Chunk length is provider-specific (OpenAI uses short 5-min chunks because
  `gpt-4o-transcribe` truncates long audio; Mistral uses 15-min chunks). Override
  with `--chunk-seconds` only if you have a reason to.

## Transcribe from VS Code (manual, no Claude)

For running it yourself: drop a file into `recordings/`, then click a status-bar button.
Two buttons (from `.vscode/`), matching the provider rule above:

- **🎙 FR → Mistral** — `uv run transcribe --all --provider mistral --language fr`
- **🎙 EN/other → OpenAI** — `uv run transcribe --all --provider openai` (auto-detect)

Both transcribe every not-yet-done file in `recordings/` and write to `outputs/`; progress
shows in the integrated terminal. The buttons need the `spencerwmiles.vscode-task-buttons`
extension (VS Code prompts to install it via `.vscode/extensions.json`). Without the
extension the same two tasks are reachable from **Terminal → Run Task**. To re-do an
existing transcript, add `--overwrite` (ask Claude, or run the task manually).

## Setup / troubleshooting

- Dependencies and Python are managed by `uv`. If a command fails with a missing
  package, run `uv sync` first.
- Requires the selected provider's key in `.env` (`OPENAI_API_KEY` or `MISTRAL_API_KEY`;
  see `.env.example`). If it's missing the CLI exits with a clear message — ask the user
  to add the key to `.env`.
- ffmpeg is bundled via `imageio-ffmpeg`; nothing to install system-wide.
- Run the tests with `uv run pytest`.

## Privacy — do not commit recordings or transcripts

`recordings/` and `outputs/` are gitignored on purpose (corporate meeting content).
Never force-add files from those folders, and never paste transcript contents into
commits, PRs, or anywhere external.

## Internal structure

- `src/meeting_transcribator/` — the package: `audio.py` (ffmpeg locate + normalize/chunk),
  `providers.py` (OpenAI/Mistral), `transcriber.py` (chunk → transcribe → stitch),
  `cli.py` (the `transcribe` command).
- `tests/` — pytest suite (`uv run pytest`).
- `recordings/` — audio inputs (gitignored). `outputs/` — `.md` transcripts (gitignored).
- `.vscode/` — the transcribe buttons (tasks + button config + extension recommendation).
- `.claude/` — Claude Code settings and skills. The `sync-template` skill re-syncs this
  repo's structure/conventions with the canonical `example-project` template; this project
  deliberately keeps only a lean subset of it (see the skill for what it omits and why).
- `docs/ai_execution_plans/` — plans written for/by Claude.
