"""Transcription orchestration: chunk a recording, send each chunk to the
selected provider, and stitch the chunk texts into one transcript.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable, Iterable

from .audio import chunk_audio
from .providers import Provider


def transcribe_chunks(
    chunk_paths: Iterable[Path],
    *,
    provider: Provider,
    model: str,
    language: str | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> str:
    """Transcribe each chunk in order and join the texts with blank lines."""
    chunk_paths = list(chunk_paths)
    texts: list[str] = []
    for index, chunk in enumerate(chunk_paths, start=1):
        if on_progress:
            on_progress(index, len(chunk_paths))
        texts.append(provider.transcribe(chunk, model=model, language=language).strip())
    return "\n\n".join(t for t in texts if t)


def transcribe_file(
    src: str | Path,
    dest: str | Path,
    *,
    provider: Provider,
    model: str,
    language: str | None = None,
    chunk_seconds: int | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Transcribe ``src`` and write the raw transcript text to ``dest`` (.md).

    ``chunk_seconds`` overrides the per-chunk audio length; when None the
    provider's own ``chunk_seconds`` is used.
    """
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    seconds = chunk_seconds or getattr(provider, "chunk_seconds", None)
    with tempfile.TemporaryDirectory(prefix="transcribe_") as tmp:
        chunks = chunk_audio(src, tmp, max_seconds=seconds)
        text = transcribe_chunks(
            chunks, provider=provider, model=model, language=language, on_progress=on_progress
        )
    dest.write_text(text + "\n", encoding="utf-8")
    return dest
