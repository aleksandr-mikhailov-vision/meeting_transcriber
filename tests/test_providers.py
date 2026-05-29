"""Each provider must call its SDK with the right arguments and return text.
The underlying SDK clients are faked, so no network or API key is needed."""

from types import SimpleNamespace

from meeting_transcribator.providers import PROVIDERS, MistralProvider, OpenAIProvider


class _RecordingMethod:
    def __init__(self, ret):
        self.ret = ret
        self.kwargs = None

    def __call__(self, **kwargs):
        # Snapshot kwargs; the file handle is consumed before the call returns.
        snap = dict(kwargs)
        if isinstance(snap.get("file"), dict):
            snap["file"] = dict(snap["file"])
        self.kwargs = snap
        return self.ret


def _client_with(method_name, ret):
    method = _RecordingMethod(ret)
    transcriptions = SimpleNamespace(**{method_name: method})
    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=transcriptions))
    return client, method


def test_registry_has_both_providers():
    assert set(PROVIDERS) == {"openai", "mistral"}
    assert PROVIDERS["openai"].default_model == "gpt-4o-transcribe"
    assert PROVIDERS["mistral"].default_model == "voxtral-mini-latest"


def test_openai_provider_calls_create_with_text_format(tmp_path):
    audio = tmp_path / "chunk_0000.mp3"
    audio.write_bytes(b"x")
    client, method = _client_with("create", "OPENAI_TRANSCRIPT")

    provider = OpenAIProvider(client=client)
    out = provider.transcribe(audio, model="gpt-4o-transcribe", language="en")

    assert out == "OPENAI_TRANSCRIPT"
    assert method.kwargs["model"] == "gpt-4o-transcribe"
    assert method.kwargs["response_format"] == "text"
    assert method.kwargs["language"] == "en"
    assert "file" in method.kwargs


def test_openai_provider_omits_language_when_none(tmp_path):
    audio = tmp_path / "chunk_0000.mp3"
    audio.write_bytes(b"x")
    client, method = _client_with("create", "T")

    OpenAIProvider(client=client).transcribe(audio, model="whisper-1", language=None)

    assert "language" not in method.kwargs


def test_mistral_provider_calls_complete_and_reads_text(tmp_path):
    audio = tmp_path / "chunk_0000.mp3"
    audio.write_bytes(b"x")
    client, method = _client_with("complete", SimpleNamespace(text="MISTRAL_TRANSCRIPT"))

    provider = MistralProvider(client=client)
    out = provider.transcribe(audio, model="voxtral-mini-latest", language="fr")

    assert out == "MISTRAL_TRANSCRIPT"
    assert method.kwargs["model"] == "voxtral-mini-latest"
    assert method.kwargs["file"]["file_name"] == "chunk_0000.mp3"
    assert "content" in method.kwargs["file"]
    assert method.kwargs["language"] == "fr"


def test_mistral_provider_omits_language_when_none(tmp_path):
    audio = tmp_path / "chunk_0000.mp3"
    audio.write_bytes(b"x")
    client, method = _client_with("complete", SimpleNamespace(text="T"))

    MistralProvider(client=client).transcribe(audio, model="voxtral-mini-latest", language=None)

    assert "language" not in method.kwargs
