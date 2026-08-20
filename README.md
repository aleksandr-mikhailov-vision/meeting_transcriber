# Meeting Transcribator

Turns audio recordings of meetings into plain-text transcripts. You drop audio files
into a folder, run one command, and get one `.md` file per recording containing the
raw transcript: no summaries, no formatting, just what was said.

It works on long recordings (hours), and handles English, French and other languages
via the OpenAI or Mistral transcription APIs.

**In:** audio files (`.m4a`, `.mp3`, `.wav`, `.mp4`, ...) placed in `recordings/`
**Out:** one `.md` transcript per file in `outputs/`

Your recordings and transcripts stay on your machine: both folders are gitignored, so
they are never committed or shared.

## Setup (once, about 5 minutes)

**1. Install `uv`.** It handles Python, all dependencies and audio processing for you,
so there is nothing else to install.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # macOS / Linux
```

On Windows, run `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` instead.

**2. Get an API key.** You need an account with one of the two providers, and you pay
them per minute of audio transcribed.

- OpenAI (best accuracy, use for English and most languages): create a key at
  [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
- Mistral (use for mostly-French audio): create a key at
  [console.mistral.ai](https://console.mistral.ai/).

One key is enough. Get both if you record in both English and French.

**3. Put the key in a file named `.env`.**

```bash
cp .env.example .env
```

Then open `.env` in any text editor and paste your key after the `=` sign:

```
OPENAI_API_KEY=sk-...
MISTRAL_API_KEY=...
```

**4. Install the project.**

```bash
uv sync
```

## Use it

Copy your recordings into the `recordings/` folder, then run:

```bash
# Transcribe everything that doesn't have a transcript yet
uv run transcribe --all

# Or just one file
uv run transcribe recordings/board-meeting.m4a

# For mostly-French audio, use Mistral
uv run transcribe --all --provider mistral
```

Transcripts appear in `outputs/`, named after the recording. Files that already have a
transcript are skipped, so you can safely re-run `--all` after adding new recordings.

Long recordings take a while, because the audio is split into chunks and sent to the
API one by one. Leave the command running until it prints the output path.

## Useful options

| Flag | What it does |
|------|--------------|
| `--all` | Transcribe every recording in `recordings/` that isn't done yet |
| `--overwrite` | Redo files that already have a transcript |
| `--provider mistral` | Use Mistral instead of OpenAI (better for French) |
| `--language fr` | Tell it the meeting language (`en`, `fr`, ...), improves accuracy |
| `--model whisper-1` | Use a cheaper model (see below) |

Run `uv run transcribe --help` for the full list.

**Models:** the default is OpenAI's `gpt-4o-transcribe`, the most accurate option for
meetings. `gpt-4o-mini-transcribe` and `whisper-1` cost less. Mistral defaults to
`voxtral-mini-latest`.

## If something goes wrong

- **"OPENAI_API_KEY is not set"**. The `.env` file is missing, sits in the wrong
  folder, or the key line is empty. It must sit next to this README.
- **A command isn't found**. `uv` isn't installed or isn't on your PATH; reopen your
  terminal after installing it.
- **Anything else fails oddly**. Run `uv sync` again to repair the installation.

## For developers

```bash
uv run pytest
```

The package lives in `src/meeting_transcribator/`: `audio.py` (normalise and split
audio), `providers.py` (OpenAI / Mistral API calls), `transcriber.py` (transcribe and
stitch chunks), `cli.py` (the `transcribe` command).
