# Meeting Transcribator

Turn `.m4a` (and other audio) recordings into raw-text `.md` transcripts using the
OpenAI transcription API. Pure backend — a CLI that Claude or a human can run.

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
- An OpenAI API key.

## Setup (once)

```powershell
# 1. Add your API key
copy .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...

# 2. Install dependencies (creates .venv, downloads Python if needed)
uv sync
```

## Usage

Put recordings in `recordings/`, then:

```powershell
# Transcribe one file -> outputs/<name>.md
uv run transcribe recordings/board-meeting.m4a

# Transcribe every recording that doesn't yet have a transcript
uv run transcribe --all

# Re-do everything, choose a cheaper model, hint the language
uv run transcribe --all --overwrite --model gpt-4o-mini-transcribe --language en
```

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `paths...` | — | Specific audio file(s) to transcribe |
| `--all` | off | Transcribe all recordings in `recordings/` (skips ones already done) |
| `--overwrite` | off | Re-transcribe even if a transcript exists |
| `--model` | `gpt-4o-transcribe` | OpenAI model (`gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `whisper-1`) |
| `--language` | auto-detect | ISO-639-1 hint, e.g. `en`, `fr` |
| `--recordings-dir` | `recordings` | Input folder |
| `--outputs-dir` | `outputs` | Output folder |

Defaults for `--model` / `--language` can also be set in `.env`
(`TRANSCRIBE_MODEL`, `TRANSCRIBE_LANGUAGE`).

## Cost & accuracy

`gpt-4o-transcribe` gives the best accuracy (recommended for meetings);
`gpt-4o-mini-transcribe` is cheaper; `whisper-1` is the cheapest, well-proven option.
You pay OpenAI per minute of audio. Files are downsampled to 16 kHz mono before upload —
no impact on transcription quality (the models do this internally anyway).

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
  transcriber.py  per-chunk OpenAI calls + concatenation
  cli.py          command-line interface
tests/          pytest suite
```
