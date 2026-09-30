# Jev on Strands --- Demos

A small collection of runnable demo scripts showing how to use
[Jev](https://docs.typesafe.ai/) (TypeSafe's "System One" classifier model)
alongside the [Strands Agents SDK](https://strandsagents.com).

The theme across every demo: **Jev is the semantic classifier, ordinary Python is
the policy.** Jev answers narrow, typed questions and returns probabilities --- it
never decides what to do. Your code turns those probabilities into decisions with
plain, readable logic you can trace by eye.

Each demo is a single self-contained script with its dependencies declared inline
(PEP 723), so there's no environment to manage --- [uv](https://docs.astral.sh/uv/)
installs what it needs on the fly.

## Demos

| Demo | What it shows |
|------|---------------|
| `jev_basics` | The "hello world" for Jev --- no agent, no Strands. Walks the three question types (Noul, Choice, Score) one at a time, then combines them and lets plain Python decide. Available as a script *and* a notebook. Start here. |
| `escalation_gate` | A Claude-backed Strands support agent whose every caller turn is gated by Jev. Jev classifies whether the call is going badly; a plain-Python policy returns escalate (hand off to a human) or continue (let the agent reply). |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) --- runs the scripts and handles dependencies.
- A **TypeSafe API key** for Jev. Get one from the TypeSafe console.
- An **Anthropic API key** for the `escalation_gate` demo (its Strands agent uses
  Claude). The `jev_basics` demo needs only the TypeSafe key.

## Setup

```bash
cp .env.example .env
# then edit .env and set TYPESAFE_API_KEY (and ANTHROPIC_API_KEY for escalation_gate)
```

`.env` is gitignored, so your keys stay out of version control.

## Running a demo

From the repo root, point uv at any demo's `main.py`. `--env-file` loads your keys
from `.env`:

```bash
uv run --env-file .env demos/jev_basics/main.py
uv run --env-file .env demos/escalation_gate/main.py
```

uv reads the inline dependency block at the top of the script, installs the
packages into an ephemeral environment, and runs it. No pip install, no virtualenv.

`jev_basics` is also available as a notebook --- open `demos/jev_basics/jev_basics.ipynb`
in Jupyter or VS Code and run it top to bottom (it reads `TYPESAFE_API_KEY` from `.env`).

## Repo layout

```
.
├── README.md            # you are here
├── .env.example         # template --- copy to .env
├── .gitignore
└── demos/               # one folder per demo
    ├── jev_basics/
    │   ├── README.md
    │   ├── main.py
    │   └── jev_basics.ipynb
    └── escalation_gate/
        ├── README.md
        └── main.py
```
