from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Turn:
    speaker: str          # "buyer" or "rep"
    text: str

    def to_dict(self) -> Dict[str, str]:
        return {"speaker": self.speaker, "text": self.text}


@dataclass
class Transcript:
    persona_id: str
    turns: List[Turn] = field(default_factory=list)

    @property
    def rep_text(self) -> str:
        return " ".join(t.text for t in self.turns if t.speaker == "rep")

    def to_dict(self) -> Dict[str, Any]:
        return {"persona_id": self.persona_id, "turns": [t.to_dict() for t in self.turns]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transcript":
        return cls(
            persona_id=data["persona_id"],
            turns=[Turn(**t) for t in data["turns"]],
        )


@dataclass
class CriterionScore:
    criterion_id: str
    label: str
    score: int            # 0-3
    evidence: str         # quote from the rep, or "" when not observed


@dataclass
class Scorecard:
    persona_id: str
    rubric_id: str
    scores: List[CriterionScore]

    @property
    def total(self) -> int:
        return sum(s.score for s in self.scores)

    @property
    def max_total(self) -> int:
        return 3 * len(self.scores)

    @property
    def percent(self) -> float:
        return 0.0 if not self.scores else round(100 * self.total / self.max_total, 1)
