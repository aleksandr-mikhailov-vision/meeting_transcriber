"""Audio preparation: locate a bundled ffmpeg, normalize to 16 kHz mono, and
split a recording into chunks that stay under the OpenAI 25 MB upload limit.

The OpenAI transcription endpoint rejects uploads over 25 MB and downsamples to
16 kHz mono internally anyway, so we always downmix and re-encode. We prefer a
small mp3 (libmp3lame); if that encoder is missing from the bundled ffmpeg we
fall back to 16 kHz mono WAV with shorter segments. Both stay well under 25 MB.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

# Safety margin below OpenAI's hard 25 MB (= 25 * 1024 * 1024) limit.
MAX_CHUNK_BYTES = 24 * 1024 * 1024

# Header-only containers ffmpeg can emit as a tiny trailing segment (see below).
# Anything at/under this is treated as empty and skipped. A real chunk holding
# even a fraction of a second of speech is comfortably larger.
_MIN_CHUNK_BYTES = 1024

# Fallback segment length when the caller doesn't specify one. Two ceilings apply
# per chunk: the 25 MB byte cap above AND the model's behaviour on long audio —
# gpt-4o-transcribe silently TRUNCATES its output on long chunks, so the OpenAI
# provider asks for short chunks (see providers.py `chunk_seconds`). These module
# defaults are only used when max_seconds is None. Keep them well under ~1500 s.
# mp3 @ 16 kHz mono 32 kbps ≈ 240 KB/min, so 15 min ≈ 3.6 MB. WAV pcm_s16le @
# 16 kHz mono ≈ 1.92 MB/min, so 10 min ≈ 19.2 MB (under the byte limit, with margin).
_MP3_SEGMENT_SECONDS = 900
_WAV_SEGMENT_SECONDS = 600


@lru_cache(maxsize=1)
def get_ffmpeg() -> str:
    """Return the path to the ffmpeg executable bundled with imageio-ffmpeg."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


@lru_cache(maxsize=1)
def _has_mp3_encoder() -> bool:
    """True if the bundled ffmpeg can encode mp3 (libmp3lame)."""
    try:
        out = subprocess.run(
            [get_ffmpeg(), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return "libmp3lame" in out


def _run_ffmpeg(args: list[str]) -> None:
    """Run ffmpeg with the given args, raising a clear error on failure."""
    proc = subprocess.run(
        [get_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )


def chunk_audio(
    src: str | Path, workdir: str | Path, *, max_seconds: int | None = None
) -> list[Path]:
    """Normalize ``src`` to 16 kHz mono and split it into ordered chunks in
    ``workdir``. Returns the chunk paths sorted by index (chronological order).

    ``max_seconds`` sets the per-chunk length (callers pass the provider/model's
    safe value); when None, a codec-appropriate default is used. Each chunk is a
    complete, decodable audio file under ``MAX_CHUNK_BYTES``.
    """
    src = Path(src)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        raise FileNotFoundError(f"Audio file not found: {src}")

    if _has_mp3_encoder():
        ext, codec, default_seg = "mp3", ["-c:a", "libmp3lame", "-b:a", "32k"], _MP3_SEGMENT_SECONDS
    else:
        ext, codec, default_seg = "wav", ["-c:a", "pcm_s16le"], _WAV_SEGMENT_SECONDS
    seg = max_seconds if max_seconds else default_seg

    pattern = workdir / f"chunk_%04d.{ext}"
    _run_ffmpeg(
        [
            "-i", str(src),
            "-ac", "1",          # mono
            "-ar", "16000",      # 16 kHz
            "-vn",               # drop any video/cover-art stream
            *codec,
            "-f", "segment",
            "-segment_time", str(seg),
            "-reset_timestamps", "1",
            str(pattern),
        ]
    )

    chunks = sorted(workdir.glob(f"chunk_*.{ext}"))
    if not chunks:
        raise RuntimeError(f"ffmpeg produced no chunks for {src}")

    # The segment muxer can append a tiny empty trailing chunk when the duration
    # is an exact multiple of the segment length. Drop near-empty chunks so we
    # don't pay for empty transcription requests; keep the largest if all are
    # tiny (a genuinely near-silent recording) so we still attempt one.
    sized = [c for c in chunks if c.stat().st_size > _MIN_CHUNK_BYTES]
    chunks = sized or [max(chunks, key=lambda c: c.stat().st_size)]

    oversized = [c for c in chunks if c.stat().st_size > MAX_CHUNK_BYTES]
    if oversized:
        names = ", ".join(c.name for c in oversized)
        raise RuntimeError(
            f"Chunk(s) exceeded the {MAX_CHUNK_BYTES} byte limit: {names}. "
            "This is unexpected; please report the recording's length/format."
        )
    return chunks
