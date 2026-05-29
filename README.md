# Meeting Transcribator

Turn `.m4a` (and other audio) recordings into raw-text `.md` transcripts using
either the **OpenAI** or **Mistral (Voxtral)** transcription API. Pure backend — a
CLI that Claude or a human can run.

- **In:** audio files in `recordings/`
- **Out:** one `.md` per recording in `outputs/` (raw transcript text, nothing else)
- Long meetings are handled automatically: audio is downmixed to 16 kHz mono and
  split into chunks under OpenAI's 25 MB limit, transcribed, then stitched together.
- **Privacy:** both `recordings/` and `outputs/` are gitignored — recordings and
  transcripts never get committed.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (already installed on this machine). It manages
  Python and all dependencies — including a **bundled ffmpeg** (`imageio-ffmpeg`), so
  you do **not** need Python or ffmpeg installed system-wide.
- An API key for whichever provider you use: an **OpenAI** key, a **Mistral** key, or both.

## Setup (once)

```powershell
# 1. Add your API key(s)
copy .env.example .env
# then edit .env: set OPENAI_API_KEY=sk-... and/or MISTRAL_API_KEY=...

# 2. Install dependencies (creates .venv, downloads Python if needed)
uv sync
```

## Usage

Put recordings in `recordings/`, then:

```powershell
# Transcribe one file -> outputs/<name>.md (OpenAI, the default provider)
uv run transcribe recordings/board-meeting.m4a

# Transcribe every recording that doesn't yet have a transcript
uv run transcribe --all

# Use Mistral (Voxtral) instead
uv run transcribe --all --provider mistral

# Re-do everything, choose a specific model, hint the language
uv run transcribe --all --overwrite --model gpt-4o-mini-transcribe --language en
```

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `paths...` | — | Specific audio file(s) to transcribe |
| `--all` | off | Transcribe all recordings in `recordings/` (skips ones already done) |
| `--overwrite` | off | Re-transcribe even if a transcript exists |
| `--provider` | `openai` | `openai` or `mistral` |
| `--model` | provider default | Model override (see below) |
| `--language` | auto-detect | ISO-639-1 hint, e.g. `en`, `fr` |
| `--chunk-seconds` | provider-specific | Per-chunk audio length (advanced; see below) |
| `--recordings-dir` | `recordings` | Input folder |
| `--outputs-dir` | `outputs` | Output folder |

> **Why chunk length is provider-specific:** `gpt-4o-transcribe` silently truncates
> its output on long audio, so the OpenAI provider defaults to short (5-minute)
> chunks to keep every request under that cap. Mistral Voxtral handles long audio
> without truncating, so it uses 15-minute chunks (fewer requests). Override with
> `--chunk-seconds` if needed.

Defaults can also be set in `.env` (`TRANSCRIBE_PROVIDER`, `TRANSCRIBE_MODEL`,
`TRANSCRIBE_LANGUAGE`).

**Default model per provider:**

| Provider | Default model | Key | Other models you can pass |
|----------|---------------|-----|---------------------------|
| `openai` | `gpt-4o-transcribe` | `OPENAI_API_KEY` | `gpt-4o-mini-transcribe`, `whisper-1` |
| `mistral` | `voxtral-mini-latest` | `MISTRAL_API_KEY` | other Voxtral variants |

## Cost & accuracy

OpenAI's `gpt-4o-transcribe` gives the best accuracy (recommended for meetings);
`gpt-4o-mini-transcribe` is cheaper; `whisper-1` is the cheapest, well-proven option.
Mistral's `voxtral-mini-latest` (Voxtral) is a strong alternative and can handle very
long recordings. You pay the provider per minute of audio. Files are downsampled to
16 kHz mono before upload — no impact on transcription quality (the models do this
internally anyway).

## Development

```powershell
uv run pytest
```

## Project layout

```
recordings/   audio inputs (gitignored)
outputs/      .md transcripts (gitignored)
src/meeting_transcribator/
  audio.py        ffmpeg locate + normalize/chunk
  providers.py    OpenAI / Mistral provider implementations
  transcriber.py  per-chunk transcription + concatenation
  cli.py          command-line interface
tests/          pytest suite
```
