"""Transcription providers. Each provider knows its default model, the env var
that holds its API key, and how to turn one audio chunk into text. The chunking
pipeline in ``audio.py`` is provider-agnostic and feeds whichever is selected.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class Provider(Protocol):
    name: str
    default_model: str
    env_key: str

    def transcribe(self, path: Path, *, model: str, language: str | None) -> str:
        """Transcribe a single audio chunk and return its raw text."""
        ...


class OpenAIProvider:
    name = "openai"
    default_model = "gpt-4o-transcribe"
    env_key = "OPENAI_API_KEY"

    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self._client = client

    def transcribe(self, path: Path, *, model: str, language: str | None) -> str:
        kwargs = {"model": model, "response_format": "text"}
        if language:
            kwargs["language"] = language
        with open(path, "rb") as fh:
            result = self._client.audio.transcriptions.create(file=fh, **kwargs)
        # response_format="text" returns a plain str; "json" returns an object with .text.
        return result if isinstance(result, str) else result.text


class MistralProvider:
    name = "mistral"
    # Voxtral. Override with --model for other Voxtral variants.
    default_model = "voxtral-mini-latest"
    env_key = "MISTRAL_API_KEY"

    def __init__(self, client=None):
        if client is None:
            from mistralai.client import Mistral

            client = Mistral(api_key=os.environ[self.env_key])
        self._client = client

    def transcribe(self, path: Path, *, model: str, language: str | None) -> str:
        kwargs = {"model": model, "file": {"content": None, "file_name": path.name}}
        if language:
            kwargs["language"] = language
        with open(path, "rb") as fh:
            kwargs["file"]["content"] = fh
            result = self._client.audio.transcriptions.complete(**kwargs)
        return result.text


# Registry keyed by --provider value. New providers slot in here.
PROVIDERS: dict[str, type] = {
    OpenAIProvider.name: OpenAIProvider,
    MistralProvider.name: MistralProvider,
}
