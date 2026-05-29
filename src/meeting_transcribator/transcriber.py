"""Transcription orchestration: chunk a recording, send each chunk to the
OpenAI transcription endpoint, and stitch the chunk texts into one transcript.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable, Iterable, Protocol

from .audio import chunk_audio

DEFAULT_MODEL = "gpt-4o-transcribe"


class _OpenAIClient(Protocol):
    """The slice of the OpenAI client we depend on (kept narrow for testing)."""

    @property
    def audio(self): ...  # noqa: D102,E704 - structural typing only


def _transcribe_one(client: _OpenAIClient, path: Path, *, model: str, language: str | None) -> str:
    """Transcribe a single chunk file and return its raw text."""
    kwargs = {"model": model, "response_format": "text"}
    if language:
        kwargs["language"] = language
    with open(path, "rb") as fh:
        result = client.audio.transcriptions.create(file=fh, **kwargs)
    # With response_format="text" the SDK returns a plain string; with "json" it
    # returns an object exposing `.text`. Support both defensively.
    return result if isinstance(result, str) else result.text


def transcribe_chunks(
    chunk_paths: Iterable[Path],
    *,
    client: _OpenAIClient,
    model: str = DEFAULT_MODEL,
    language: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> str:
    """Transcribe each chunk in order and join the texts with blank lines."""
    chunk_paths = list(chunk_paths)
    texts: list[str] = []
    for index, chunk in enumerate(chunk_paths, start=1):
        if on_progress:
            on_progress(index, len(chunk_paths))
        texts.append(_transcribe_one(client, chunk, model=model, language=language).strip())
    return "\n\n".join(t for t in texts if t)


def transcribe_file(
    src: str | Path,
    dest: str | Path,
    *,
    client: _OpenAIClient,
    model: str = DEFAULT_MODEL,
    language: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Transcribe ``src`` and write the raw transcript text to ``dest`` (.md)."""
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="transcribe_") as tmp:
        chunks = chunk_audio(src, tmp)
        text = transcribe_chunks(
            chunks, client=client, model=model, language=language, on_progress=on_progress
        )
    dest.write_text(text + "\n", encoding="utf-8")
    return dest
