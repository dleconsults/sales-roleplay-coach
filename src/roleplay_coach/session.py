"""Runs a roleplay session: buyer speaks, rep answers, transcript gets scored."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import yaml

from .models import Transcript, Turn
from .voice import VoiceClient


def load_persona(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class RoleplaySession:
    def __init__(self, persona: Dict, voice: Optional[VoiceClient] = None, audio_dir: str = "."):
        self.persona = persona
        self.voice = voice or VoiceClient()
        self.audio_dir = audio_dir
        self.transcript = Transcript(persona_id=persona["id"])

    def buyer_lines(self) -> List[str]:
        """The buyer script: an opener, then each objection in order."""
        return [self.persona["opening_line"].strip()] + list(self.persona.get("objections", []))

    def say(self, text: str, index: int) -> Optional[str]:
        """Speak a buyer line. Returns an audio path when voice is enabled."""
        path = None
        if self.voice.enabled:
            path = self.voice.speak(
                text,
                voice_id=self.persona["voice_id"],
                out_path=f"{self.audio_dir}/buyer_{self.persona['id']}_{index}.mp3",
            )
        self.transcript.turns.append(Turn("buyer", text))
        return path

    def rep_says(self, text: str) -> None:
        self.transcript.turns.append(Turn("rep", text))

    def rep_audio(self, audio_path: str) -> str:
        text = self.voice.transcribe(audio_path)
        self.rep_says(text)
        return text

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.transcript.to_dict(), f, indent=2)
