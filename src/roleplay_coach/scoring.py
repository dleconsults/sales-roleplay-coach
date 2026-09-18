"""Scores a transcript against a rubric.

Two scorers, same interface:

  KeywordScorer  - deterministic, no API key, used for tests and offline demos
  LLMScorer      - sends the transcript and rubric to an LLM for judgment

The point of the rubric file is that the standard lives in version control.
When the standard changes, the diff shows what changed and when.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

import yaml

from .models import CriterionScore, Scorecard, Transcript


def load_rubric(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _first_sentence_containing(text: str, needle: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if needle.lower() in sentence.lower():
            return sentence.strip()
    return ""


class KeywordScorer:
    """Deterministic baseline. Counts rubric cues in the rep's turns."""

    name = "keyword"

    def score(self, transcript: Transcript, rubric: Dict) -> Scorecard:
        rep_text = transcript.rep_text
        scores: List[CriterionScore] = []
        for crit in rubric["criteria"]:
            hits = [k for k in crit.get("look_for", []) if k.lower() in rep_text.lower()]
            score = min(3, len(hits) + (1 if hits else 0))
            evidence = _first_sentence_containing(rep_text, hits[0]) if hits else ""
            scores.append(
                CriterionScore(
                    criterion_id=crit["id"],
                    label=crit["label"],
                    score=score,
                    evidence=evidence,
                )
            )
        return Scorecard(transcript.persona_id, rubric["id"], scores)


class LLMScorer:
    """Judgment-based scoring. Works with any OpenAI-compatible chat endpoint."""

    name = "llm"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini",
                 base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _prompt(self, transcript: Transcript, rubric: Dict) -> str:
        criteria = "\n".join(f"- {c['id']}: {c['label']}" for c in rubric["criteria"])
        convo = "\n".join(f"{t.speaker.upper()}: {t.text}" for t in transcript.turns)
        return (
            "Score this sales roleplay against the rubric. For each criterion return a score "
            "from 0 to 3 (0 not observed, 1 attempted, 2 competent, 3 strong) and a short "
            "verbatim quote from the REP as evidence. Return JSON only, shaped as "
            '{"scores": [{"criterion_id": "...", "score": 0, "evidence": "..."}]}.\n\n'
            f"RUBRIC:\n{criteria}\n\nTRANSCRIPT:\n{convo}"
        )

    def score(self, transcript: Transcript, rubric: Dict) -> Scorecard:
        if not self.enabled:
            raise RuntimeError("LLM_API_KEY is required for LLMScorer. Use KeywordScorer instead.")
        import urllib.request

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": self._prompt(transcript, rubric)}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
        content = json.loads(body["choices"][0]["message"]["content"])
        labels = {c["id"]: c["label"] for c in rubric["criteria"]}
        scores = [
            CriterionScore(
                criterion_id=s["criterion_id"],
                label=labels.get(s["criterion_id"], s["criterion_id"]),
                score=int(s["score"]),
                evidence=s.get("evidence", ""),
            )
            for s in content["scores"]
        ]
        return Scorecard(transcript.persona_id, rubric["id"], scores)


def coaching_card(card: Scorecard, persona_name: str) -> str:
    """Render a scorecard as the markdown a manager would actually coach from."""
    lines = [
        f"# Coaching card: {persona_name} roleplay",
        "",
        f"**Score:** {card.total}/{card.max_total} ({card.percent}%)",
        "",
        "| Criterion | Score | Evidence |",
        "| --- | --- | --- |",
    ]
    for s in sorted(card.scores, key=lambda x: x.score):
        evidence = s.evidence.replace("|", "/") if s.evidence else "_not observed_"
        lines.append(f"| {s.label} | {s.score}/3 | {evidence} |")

    weakest = sorted(card.scores, key=lambda x: x.score)[:2]
    lines += ["", "## Work on this first", ""]
    for s in weakest:
        lines.append(f"- **{s.label}** ({s.score}/3)")
    lines += ["", "## Run it back", "", "Re-run the same persona after coaching and compare the scores."]
    return "\n".join(lines)
