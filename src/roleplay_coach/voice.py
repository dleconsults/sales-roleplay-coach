"""ElevenLabs voice I/O.

Speaking the buyer persona and transcribing the rep both run through ElevenLabs.
Every call degrades to text mode when no API key is present, so the tool still
runs in CI and on a laptop with no credentials.
"""
from __future__ import annotations

import os
from typing import Optional


class VoiceClient:
    def __init__(self, api_key: Optional[str] = None, model_id: str = "eleven_turbo_v2_5"):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.model_id = model_id
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from elevenlabs.client import ElevenLabs  # imported lazily
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def speak(self, text: str, voice_id: str, out_path: Optional[str] = None) -> Optional[str]:
        """Render buyer dialogue to audio. Returns the file path, or None in text mode."""
        if not self.enabled:
            return None
        client = self._get_client()
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=self.model_id,
            text=text,
            output_format="mp3_44100_128",
        )
        path = out_path or "buyer_turn.mp3"
        with open(path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        return path

    def transcribe(self, audio_path: str) -> str:
        """Transcribe a rep's recorded answer with Scribe."""
        if not self.enabled:
            raise RuntimeError("ELEVENLABS_API_KEY is required to transcribe audio.")
        client = self._get_client()
        with open(audio_path, "rb") as f:
            result = client.speech_to_text.convert(file=f, model_id="scribe_v1")
        return getattr(result, "text", "") or ""
