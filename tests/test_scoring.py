import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from roleplay_coach.models import Transcript          # noqa: E402
from roleplay_coach.scoring import (                   # noqa: E402
    KeywordScorer, coaching_card, load_rubric,
)

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def _transcript():
    with open(os.path.join(ROOT, "examples", "sample_transcript.json")) as f:
        return Transcript.from_dict(json.load(f))


def test_scores_every_criterion():
    rubric = load_rubric(os.path.join(ROOT, "rubrics", "discovery.yaml"))
    card = KeywordScorer().score(_transcript(), rubric)
    assert len(card.scores) == len(rubric["criteria"])
    assert all(0 <= s.score <= 3 for s in card.scores)


def test_strong_transcript_beats_empty_one():
    rubric = load_rubric(os.path.join(ROOT, "rubrics", "discovery.yaml"))
    good = KeywordScorer().score(_transcript(), rubric)
    empty = KeywordScorer().score(Transcript(persona_id="skeptical_broker"), rubric)
    assert good.total > empty.total
    assert empty.total == 0


def test_card_lists_weakest_first():
    rubric = load_rubric(os.path.join(ROOT, "rubrics", "discovery.yaml"))
    card = KeywordScorer().score(_transcript(), rubric)
    md = coaching_card(card, "Skeptical Broker")
    assert "Work on this first" in md
    assert md.startswith("# Coaching card")
