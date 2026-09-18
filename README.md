# Sales Roleplay Coach

A command line tool that runs sales roleplays against a voiced buyer persona, then scores
the conversation against a rubric and writes a coaching card a manager can actually use.

Buyer personas are spoken with [ElevenLabs](https://elevenlabs.io) text to speech. Rep
answers can be typed or recorded and transcribed with ElevenLabs Scribe. Scoring runs
either deterministically or through an LLM.

## Why it exists

Most sales enablement measures attendance. People show up to training, the training gets
marked complete, and nobody can say whether behavior changed. Roleplay is the one place
you can watch behavior directly, and it usually dies in calendars because it needs two
people and a manager with time.

This makes roleplay cheap enough to run weekly and scored the same way every time:

1. The rubric lives in version control, so the standard is explicit and its changes are visible.
2. Every rep faces the same persona, the same objections, in the same order.
3. The output is a coaching card ranked weakest first, not a completion checkmark.
4. Running it again after coaching gives you a before and after on the same scale.

## Install

```bash
git clone https://github.com/dleconsults/sales-roleplay-coach
cd sales-roleplay-coach
pip install -r requirements.txt
cp .env.example .env    # add your keys
```

Keys are optional. With none set, buyer lines print as text and scoring uses the
deterministic scorer, so the whole loop still runs.

| Variable | What it enables |
| --- | --- |
| `ELEVENLABS_API_KEY` | Buyer personas speak, and rep audio can be transcribed |
| `LLM_API_KEY` | Judgment-based scoring with `--scorer llm` |

## Use

Run a roleplay:

```bash
export PYTHONPATH=src
python -m roleplay_coach.cli run --persona personas/skeptical_broker.yaml --out transcript.json
```

Score it:

```bash
python -m roleplay_coach.cli score --transcript transcript.json --out coaching_card.md
python -m roleplay_coach.cli score --transcript transcript.json --scorer llm   # needs LLM_API_KEY
```

Score the included sample without running anything:

```bash
python -m roleplay_coach.cli score --transcript examples/sample_transcript.json
```

See [`examples/sample_coaching_card.md`](examples/sample_coaching_card.md) for the output.

## Personas and rubrics

Both are plain YAML, which is the point. Enablement teams change what "good" means every
quarter, and that change should be reviewable.

A persona defines who the rep is talking to, which voice speaks it, and the objections
that come in order:

```yaml
id: skeptical_broker
name: Dana Whitfield
role: Managing Broker, 40-agent residential brokerage
voice_id: "21m00Tcm4TlvDq8ikWAM"
opening_line: I've got about ten minutes...
objections:
  - We already pay for two tools that claim to do this.
```

A rubric defines the behaviors worth scoring:

```yaml
criteria:
  - id: quantified_pain
    label: Quantified the cost of the current state
    look_for: ["how many", "how much", "how often"]
```

`look_for` is used by the keyword scorer and ignored by the LLM scorer, which reads the
label and judges the transcript.

## Layout

```
personas/     buyer personas (YAML)
rubrics/      scoring rubrics (YAML)
src/roleplay_coach/
  voice.py    ElevenLabs TTS and Scribe, degrades to text mode without a key
  session.py  runs the roleplay, builds the transcript
  scoring.py  keyword and LLM scorers, coaching card rendering
  cli.py      run / score commands
examples/     sample transcript and the card it produces
tests/        no keys required
```

## Tests

```bash
python -m pytest tests -q
```

## Where I'd take it next

- Track scores per rep over time so coaching shows up as a trend rather than a snapshot
- ElevenLabs Agents for a buyer that responds to what the rep actually says, instead of a fixed objection order
- Rubric variants by segment and by stage, since discovery for an SMB and an enterprise deal are not the same skill
- A team view that rolls scores up by manager, which is where the coaching conversation actually happens

## License

MIT
