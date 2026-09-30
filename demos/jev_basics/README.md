# jev_basics

The "hello world" for Jev --- no agent, no Strands. Walks the three question
types on one shared state, then combines them with plain Python.

- **Choice** --- pick one option from a fixed set (`.choice`, `.confidence`, `.probabilities`)
- **Score** --- rate on an ordered scale (`.score`, `.confidence`, `.legend`)
- **Noul** --- is this statement true? (`.noul`, a probability 0..1)

The takeaway: answers are typed and constrained to what you asked for. Nothing
comes back off-schema; your code reads `.choice` / `.score` / `.noul` directly.

## Run

```bash
uv run --env-file .env demos/jev_basics/main.py
```

Needs only `TYPESAFE_API_KEY`.
