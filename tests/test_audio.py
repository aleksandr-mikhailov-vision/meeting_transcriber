"""Integration test for the real chunking path. Synthesizes a tone with the
bundled ffmpeg, so it runs only when imageio-ffmpeg is installed."""

import subprocess

import pytest

from meeting_transcribator.audio import MAX_CHUNK_BYTES, chunk_audio, get_ffmpeg


def _ffmpeg_available() -> bool:
    try:
        get_ffmpeg()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ffmpeg_available(), reason="bundled ffmpeg not installed")


def _make_tone(path, seconds):
    subprocess.run(
        [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
            str(path),
        ],
        check=True,
    )


def test_chunk_audio_splits_long_recording(tmp_path):
    src = tmp_path / "tone.m4a"
    _make_tone(src, seconds=65)

    # 30 s segments so a 65 s tone yields multiple chunks regardless of codec.
    chunks = chunk_audio(src, tmp_path / "work", max_seconds=30)

    assert len(chunks) >= 2, "65 s at 30 s segments should produce multiple chunks"
    assert chunks == sorted(chunks), "chunks must be in chronological order"
    for c in chunks:
        assert c.is_file()
        assert 0 < c.stat().st_size <= MAX_CHUNK_BYTES


def test_chunk_audio_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        chunk_audio(tmp_path / "nope.m4a", tmp_path / "work")
