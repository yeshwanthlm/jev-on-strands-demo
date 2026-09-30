# escalation_gate

A Claude-backed Strands agent handles a support call. Before it answers each
caller turn, Jev classifies whether the call is going badly and a plain-Python
policy decides: **escalate** to a human, or **continue** and let the agent reply.

The flow, per caller turn:

```
caller says something
    -> Jev classifies the call so far (frustration Score; wants_human,
       repeated_failure, outside_scope Nouls)
    -> plain Python `if` statements decide (the policy)
    -> escalate (hand off) OR the agent answers and we continue
```

Jev is only the classifier. The escalate-vs-continue logic and its thresholds
live in `should_escalate` as readable `if`s. Claude does the talking.

## Run

```bash
uv run --env-file .env demos/escalation_gate/main.py
```

Needs `TYPESAFE_API_KEY` (Jev) and `ANTHROPIC_API_KEY` (the agent's Claude model).
