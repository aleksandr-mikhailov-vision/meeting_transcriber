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
- Provider defaults to OpenAI (`gpt-4o-transcribe`). For Mistral, add `--provider mistral`
  (default model `voxtral-mini-latest`). Pick provider based on what the user asks for
  or which key is configured.
- Use `--model ...` for a cheaper/specific model (`gpt-4o-mini-transcribe`, `whisper-1`,
  other Voxtral variants). Use `--language en` (or `fr`, etc.) if the user tells you the
  meeting language.
- Output is the raw transcript only — no summaries or formatting added (by design).
- Chunk length is provider-specific (OpenAI uses short 5-min chunks because
  `gpt-4o-transcribe` truncates long audio; Mistral uses 15-min chunks). Override
  with `--chunk-seconds` only if you have a reason to.

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
