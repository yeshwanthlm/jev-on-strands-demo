# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "typesafe-sdk>=0.7.2,<0.8",
# ]
# ///
"""
Jev basics --- the three question types, one at a time (single-file demo)
=========================================================================

The "hello world" for Jev. No agent, no Strands. Just the model.

Jev is a "System One" model: instead of generating text, you send it a *state*
(the thing to judge) plus *typed questions*, and it returns typed answers with
probabilities --- in one parallel call. This demo walks the three question types
on the same state, then combines their answers with plain Python.

    Choice  -> pick one option from a fixed set   (.choice, .confidence, .probabilities)
    Score   -> rate on an ordered scale           (.score, .confidence, .legend)
    Noul    -> is this statement true?            (.noul, a probability 0..1)

The point to take away: every answer is typed and constrained to what you asked
for. There is no prose to parse, and nothing comes back off-schema. Your code
reads .choice / .score / .noul directly and decides what to do.

Run it with uv (no manual install --- deps are declared inline above, and
--env-file loads TYPESAFE_API_KEY from .env):

    uv run --env-file .env demos/jev_basics/main.py

Optimized for readability, not production robustness.
"""

from __future__ import annotations

import os

# --- Jev: the TypeSafe classifier client ------------------------------------
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient


# ---------------------------------------------------------------------------
# 0. Config / secrets
# ---------------------------------------------------------------------------
# TYPESAFE_API_KEY comes from the environment. Run via
# `uv run --env-file .env ...` and uv loads it from the .env file for you.
jev = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])


# ---------------------------------------------------------------------------
# 1. One state, shared by every question below
# ---------------------------------------------------------------------------
# The "state" is whatever you want Jev to judge. Here it's a single support
# message. Every question in this demo looks at this same text.
STATE = (
    "I've been trying to connect my Stripe account for three days and the "
    "integration keeps failing. I'm losing sales. Please help ASAP."
)


# ---------------------------------------------------------------------------
# 2. Choice --- pick one option from a fixed set
# ---------------------------------------------------------------------------
# Use Choice when the answer is one of a known list with no order between them:
# routing, classification, language detection. Jev can only ever return one of
# the options you supply --- it cannot go off-schema.
def demo_choice() -> str:
    answer = jev.system_one(
        state=STATE,
        questions={
            "department": Choice(
                instructions="Which team should handle this message",
                criteria={
                    "billing": "Payments, invoices, or subscription issues",
                    "technical": "Bugs or integration problems",
                    "sales": "Pricing or account questions",
                },
            ),
        },
    ).answers["department"]

    print("\n[Choice] which department?")
    print(f"    choice       : {answer.choice}")
    print(f"    confidence   : {answer.confidence:.2f}")
    print(f"    probabilities: {answer.probabilities}")
    return answer.choice


# ---------------------------------------------------------------------------
# 3. Score --- rate on an ordered scale
# ---------------------------------------------------------------------------
# Use Score when the answer sits on a spectrum you can describe level by level:
# severity, frustration, completeness. Give 2..10 levels, lowest first. The score
# can land BETWEEN levels --- treat it as a rank, not a measurement.
def demo_score() -> float:
    answer = jev.system_one(
        state=STATE,
        questions={
            "frustration": Score(
                instructions="How frustrated does the customer sound",
                criteria=[
                    "Calm, just stating facts",
                    "Frustrated but civil",
                    "Very angry, strong language",
                ],
            ),
        },
    ).answers["frustration"]

    print("\n[Score] how frustrated?")
    print(f"    score      : {answer.score:.2f}   (0=calm .. 2=very angry)")
    print(f"    confidence : {answer.confidence:.2f}")
    print(f"    legend     : {answer.legend}")
    return answer.score


# ---------------------------------------------------------------------------
# 4. Noul --- is this statement true?
# ---------------------------------------------------------------------------
# Use Noul for a clean yes/no where the probability itself is the signal. Phrase
# the statement so a HIGH value means "yes". Noul has no separate confidence ---
# distance from 0.5 IS the decisiveness (0.97 = firm yes, 0.5 = "no idea").
def demo_noul() -> float:
    answer = jev.system_one(
        state=STATE,
        questions={
            "is_urgent": Noul(
                instructions="The message conveys urgency or time-sensitivity",
            ),
        },
    ).answers["is_urgent"]

    print("\n[Noul] is it urgent?")
    print(f"    noul : {answer.noul:.2f}   (probability the statement is true)")
    return answer.noul


# ---------------------------------------------------------------------------
# 5. All three at once, then let plain Python decide
# ---------------------------------------------------------------------------
# Every question in a request sees the same state, runs in parallel, and comes
# back under the ID you chose. Asking more questions barely changes latency, so
# ask everything you might need in one call and let code combine the answers.
def demo_combined() -> None:
    answers = jev.system_one(
        state=STATE,
        questions={
            "department": Choice(
                instructions="Which team should handle this message",
                criteria={
                    "billing": "Payments, invoices, or subscription issues",
                    "technical": "Bugs or integration problems",
                    "sales": "Pricing or account questions",
                },
            ),
            "frustration": Score(
                instructions="How frustrated does the customer sound",
                criteria=[
                    "Calm, just stating facts",
                    "Frustrated but civil",
                    "Very angry, strong language",
                ],
            ),
            "is_urgent": Noul(instructions="The message conveys urgency"),
        },
    ).answers

    department = answers["department"].choice
    frustration = answers["frustration"].score
    urgent = answers["is_urgent"].noul

    # The policy is ordinary Python. Jev told us WHAT IS; we decide WHAT HAPPENS.
    priority = "high" if (urgent > 0.5 or frustration >= 1.5) else "normal"

    print("\n[Combined] one call, three answers, then a plain-Python decision:")
    print(f"    route to {department!r} at {priority!r} priority")


def main() -> None:
    print("=" * 70)
    print("STATE:", STATE)
    print("=" * 70)
    demo_choice()
    demo_score()
    demo_noul()
    demo_combined()


if __name__ == "__main__":
    main()
