from pathlib import Path

import meeting_transcribator.transcriber as transcriber
from meeting_transcribator.transcriber import transcribe_chunks, transcribe_file


class FakeTranscriptions:
    def __init__(self):
        self.calls = []

    def create(self, *, file, model, response_format, language=None):
        # Record the call and return the chunk filename's stem as fake text so
        # we can assert ordering and arguments deterministically.
        name = Path(file.name).stem
        self.calls.append({"name": name, "model": model, "fmt": response_format, "lang": language})
        return f"text-{name}"


class FakeAudio:
    def __init__(self):
        self.transcriptions = FakeTranscriptions()


class FakeClient:
    def __init__(self):
        self.audio = FakeAudio()


def test_transcribe_chunks_joins_in_order(tmp_path):
    chunks = []
    for i in range(3):
        p = tmp_path / f"chunk_{i:04d}.mp3"
        p.write_bytes(b"x")
        chunks.append(p)
    client = FakeClient()

    text = transcribe_chunks(chunks, client=client, model="gpt-4o-transcribe", language="en")

    assert text == "text-chunk_0000\n\ntext-chunk_0001\n\ntext-chunk_0002"
    assert [c["model"] for c in client.audio.transcriptions.calls] == ["gpt-4o-transcribe"] * 3
    assert all(c["fmt"] == "text" for c in client.audio.transcriptions.calls)
    assert all(c["lang"] == "en" for c in client.audio.transcriptions.calls)


def test_language_omitted_when_none(tmp_path):
    p = tmp_path / "chunk_0000.mp3"
    p.write_bytes(b"x")
    client = FakeClient()

    transcribe_chunks([p], client=client, model="whisper-1", language=None)

    assert client.audio.transcriptions.calls[0]["lang"] is None


def test_transcribe_file_writes_md(tmp_path, monkeypatch):
    # Avoid touching ffmpeg: pretend chunking produced two chunk files.
    def fake_chunk_audio(src, workdir):
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
    client = FakeClient()

    result = transcribe_file(src, dest, client=client, model="gpt-4o-transcribe")

    assert result == dest
    assert dest.read_text(encoding="utf-8") == "text-chunk_0000\n\ntext-chunk_0001\n"
