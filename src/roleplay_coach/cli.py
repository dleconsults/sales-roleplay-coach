"""Command line entry point.

  roleplay run      - live roleplay in the terminal, buyer voiced by ElevenLabs
  roleplay score    - score a saved transcript and write a coaching card
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .models import Transcript
from .scoring import KeywordScorer, LLMScorer, coaching_card, load_rubric
from .session import RoleplaySession, load_persona
from .voice import VoiceClient


def cmd_run(args: argparse.Namespace) -> int:
    persona = load_persona(args.persona)
    voice = VoiceClient()
    session = RoleplaySession(persona, voice, audio_dir=args.audio_dir)

    if not voice.enabled:
        print("[text mode] No ELEVENLABS_API_KEY found, so buyer lines print instead of speaking.\n")

    print(f"Roleplay: {persona['name']}, {persona['role']}")
    print(f"Temperament: {persona['temperament']}\n")

    for i, line in enumerate(session.buyer_lines()):
        audio = session.say(line, i)
        print(f"{persona['name'].upper()}: {line}")
        if audio:
            print(f"   (audio: {audio})")
        try:
            answer = input("YOU: ").strip()
        except EOFError:
            answer = ""
        if not answer:
            print("\nEnding session early.\n")
            break
        session.rep_says(answer)
        print()

    session.save(args.out)
    print(f"Transcript saved to {args.out}")
    print(f"Next: roleplay score --transcript {args.out} --rubric {args.rubric}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    with open(args.transcript, "r", encoding="utf-8") as f:
        transcript = Transcript.from_dict(json.load(f))
    rubric = load_rubric(args.rubric)

    scorer = LLMScorer() if args.scorer == "llm" else KeywordScorer()
    if args.scorer == "llm" and not scorer.enabled:
        print("No LLM_API_KEY found, falling back to the keyword scorer.", file=sys.stderr)
        scorer = KeywordScorer()

    card = scorer.score(transcript, rubric)
    persona_name = transcript.persona_id.replace("_", " ").title()
    markdown = coaching_card(card, persona_name)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(markdown + "\n")
    print(markdown)
    print(f"\nCoaching card written to {args.out} (scorer: {scorer.name})")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="roleplay", description="Sales roleplay and scoring on ElevenLabs voices.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a roleplay session")
    run.add_argument("--persona", default="personas/skeptical_broker.yaml")
    run.add_argument("--rubric", default="rubrics/discovery.yaml")
    run.add_argument("--out", default="transcript.json")
    run.add_argument("--audio-dir", default=".")
    run.set_defaults(func=cmd_run)

    score = sub.add_parser("score", help="score a saved transcript")
    score.add_argument("--transcript", default="transcript.json")
    score.add_argument("--rubric", default="rubrics/discovery.yaml")
    score.add_argument("--out", default="coaching_card.md")
    score.add_argument("--scorer", choices=["keyword", "llm"], default="keyword")
    score.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
