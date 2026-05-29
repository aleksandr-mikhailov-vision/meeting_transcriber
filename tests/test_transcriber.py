from pathlib import Path

import meeting_transcribator.transcriber as transcriber
from meeting_transcribator.transcriber import transcribe_chunks, transcribe_file


class FakeProvider:
    """Records calls and returns deterministic text derived from the filename."""

    name = "fake"
    default_model = "fake-model"
    env_key = "FAKE_KEY"
    chunk_seconds = 300

    def __init__(self):
        self.calls = []

    def transcribe(self, path: Path, *, model, language):
        self.calls.append({"name": path.stem, "model": model, "language": language})
        return f"text-{path.stem}"


def test_transcribe_chunks_joins_in_order(tmp_path):
    chunks = []
    for i in range(3):
        p = tmp_path / f"chunk_{i:04d}.mp3"
        p.write_bytes(b"x")
        chunks.append(p)
    provider = FakeProvider()

    text = transcribe_chunks(chunks, provider=provider, model="m", language="en")

    assert text == "text-chunk_0000\n\ntext-chunk_0001\n\ntext-chunk_0002"
    assert [c["name"] for c in provider.calls] == ["chunk_0000", "chunk_0001", "chunk_0002"]
    assert all(c["model"] == "m" and c["language"] == "en" for c in provider.calls)


def test_transcribe_file_writes_md(tmp_path, monkeypatch):
    seen = {}

    def fake_chunk_audio(src, workdir, *, max_seconds=None):
        seen["max_seconds"] = max_seconds
        out = []
        for i in range(2):
            c = Path(workdir) / f"chunk_{i:04d}.mp3"
            c.write_bytes(b"x")
            out.append(c)
        return out

    monkeypatch.setattr(transcriber, "chunk_audio", fake_chunk_audio)

    src = tmp_path / "rec.m4a"
    src.write_bytes(b"x")
    dest = tmp_path / "out" / "rec.md"
    provider = FakeProvider()

    result = transcribe_file(src, dest, provider=provider, model="fake-model")

    assert result == dest
    assert dest.read_text(encoding="utf-8") == "text-chunk_0000\n\ntext-chunk_0001\n"
    # Falls back to the provider's chunk_seconds when not given explicitly.
    assert seen["max_seconds"] == 300


def test_transcribe_file_chunk_seconds_override(tmp_path, monkeypatch):
    seen = {}

    def fake_chunk_audio(src, workdir, *, max_seconds=None):
        seen["max_seconds"] = max_seconds
        c = Path(workdir) / "chunk_0000.mp3"
        c.write_bytes(b"x")
        return [c]

    monkeypatch.setattr(transcriber, "chunk_audio", fake_chunk_audio)
    src = tmp_path / "rec.m4a"
    src.write_bytes(b"x")
    transcribe_file(src, tmp_path / "o.md", provider=FakeProvider(), model="m", chunk_seconds=120)
    assert seen["max_seconds"] == 120
