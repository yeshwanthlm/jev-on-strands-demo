# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "strands-agents[anthropic]>=1.56,<2",
#     "typesafe-sdk>=0.7.2,<0.8",
# ]
# ///
"""
Jev + Strands --- gate a live support call to a human (single-file demo)
========================================================================

What this shows
---------------
A Claude-backed Strands agent handles a support call. Before it answers each
caller turn, Jev looks at the conversation and classifies whether the call is
going badly. A plain-Python policy turns that into one of two outcomes:

    escalate  -> stop the bot, hand off to a human
    continue  -> let the agent answer this turn

This is the "is this going badly?" gut-check every voice/support agent needs.
It's a good fit for Jev: the signals are enumerable (frustrated? wants a human?
out of scope?), the judgment is a snap decision, and it's fast enough to run
mid-conversation without adding a noticeable pause.

The flow you'll see printed to the console, per caller turn:

    caller says something
        -> Jev classifies the call so far (a few narrow, typed questions)
        -> plain Python `if` statements decide (the policy)
        -> escalate (hand off) OR the agent answers and we continue

Design intent (read this before editing):
------------------------------------------
* Jev is ONLY a classifier. It answers small, atomic questions and returns
  probabilities. It never decides what to do.
* The policy is ordinary, deterministic Python --- the thresholds and the
  escalate-vs-continue logic live in `should_escalate` as readable `if`s.
* The Strands agent (Claude) does what LLMs are for: talking to the caller. Jev
  does what it's for: the fast typed judgment. Neither does the other's job.

Run it with uv (no manual install --- deps are declared inline above, and
--env-file loads your keys from .env):

    uv run --env-file .env demos/escalation_gate/main.py

Needs TYPESAFE_API_KEY (Jev) and ANTHROPIC_API_KEY (the agent's Claude model).

Optimized for readability, not production robustness.
"""

from __future__ import annotations

import os

# --- Strands: the agent + the Anthropic (Claude) model provider ------------
from strands import Agent
from strands.models.anthropic import AnthropicModel

# --- Jev: the TypeSafe classifier client ------------------------------------
from typesafe_sdk import Noul, Score, TypeSafeClient


# ---------------------------------------------------------------------------
# 0. Config / secrets
# ---------------------------------------------------------------------------
# Both keys come from the environment. Run via `uv run --env-file .env ...`.
jev = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


# ---------------------------------------------------------------------------
# 1. Ask Jev to classify the call (semantic step)
# ---------------------------------------------------------------------------
# A few atomic questions, all evaluated in one parallel call against the same
# state. Each is one narrow judgment. Jev returns, per question, a typed answer:
# Score gives .score along the levels; Noul gives .noul (probability of "yes").
def classify_call(transcript: str):
    """Ask Jev the narrow questions that tell us if the call is going badly."""
    return jev.system_one(
        state=transcript,
        questions={
            "frustration": Score(
                instructions="How frustrated does the caller sound",
                criteria=[
                    "Calm and cooperative",
                    "Mildly annoyed but still working with the agent",
                    "Clearly upset, patience running out",
                    "Angry, threatening to leave or escalate",
                ],
            ),
            "wants_human": Noul(
                instructions="The caller is explicitly asking to speak to a human or manager",
            ),
            "repeated_failure": Noul(
                instructions="The agent has already tried and failed to resolve this more than once",
            ),
            "outside_scope": Noul(
                instructions="The request is outside what an automated agent can handle",
            ),
        },
    ).answers


# ---------------------------------------------------------------------------
# 2. The policy --- plain Python decides (deterministic step)
# ---------------------------------------------------------------------------
# Thresholds are the policy knobs, owned by us, not Jev. Bias: fail toward a
# human --- any one strong signal is enough to escalate.
FRUSTRATED = 2.0   # Score at/above this counts as "upset"
YES = 0.70         # Noul at/above this counts as a confident "yes"


def should_escalate(answers) -> str | None:
    """Return a reason to escalate, or None to let the agent continue."""
    frustration = answers["frustration"].score
    wants_human = answers["wants_human"].noul
    repeated_failure = answers["repeated_failure"].noul
    outside_scope = answers["outside_scope"].noul

    print(f"    [jev] frustration={frustration:.1f} wants_human={wants_human:.2f} "
          f"repeated_failure={repeated_failure:.2f} outside_scope={outside_scope:.2f}")

    if wants_human >= YES:
        return "caller explicitly asked for a human"
    if outside_scope >= YES:
        return "request is outside the automated agent's scope"
    if frustration >= FRUSTRATED and repeated_failure >= YES:
        return "frustrated caller after repeated failed attempts"
    if frustration >= FRUSTRATED + 0.8:
        return "caller is highly frustrated"
    return None


# ---------------------------------------------------------------------------
# 3. One agent, one call --- gate every caller turn through Jev
# ---------------------------------------------------------------------------
def main() -> None:
    agent = Agent(
        model=AnthropicModel(
            client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
            model_id=CLAUDE_MODEL,
            max_tokens=300,
        ),
        system_prompt=(
            "You are a friendly customer support voice agent. Keep replies short, "
            "one or two sentences, as if speaking on a call."
        ),
    )

    # A scripted call that starts fine and goes downhill, so you can watch the
    # gate stay out of the way and then trip. The transcript grows each turn;
    # Jev judges the whole thing so far.
    caller_turns = [
        "Hi, my app won't sync my latest orders.",
        "I already tried logging out and back in. Didn't help.",
        "This is the third time I've called about this. It's still broken.",
        "Forget it, just get me a real person.",
    ]

    transcript = ""
    for turn in caller_turns:
        transcript += f"caller: {turn}\n"
        print("\n" + "=" * 70)
        print(f"CALLER: {turn}")

        # --- Jev classifies, then the policy decides ----------------------
        reason = should_escalate(classify_call(transcript))
        if reason:
            print(f"    [policy] ESCALATE --- {reason}")
            print("    >> Handing off to a human agent. The bot stops here.")
            break

        # --- Not escalating: let the Claude agent answer this turn --------
        reply = agent(turn)
        transcript += f"agent: {reply}\n"
        print(f"    [policy] continue")
        print(f"AGENT: {reply}")

    print("\n" + "=" * 70)
    print("Jev made the fast typed judgment; plain Python owned the policy; "
          "Claude did the talking.")


if __name__ == "__main__":
    main()
