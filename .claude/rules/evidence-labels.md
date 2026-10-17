# Evidence labels (applies to every project)

Tag every claim in a report, handoff or PR body with how it is known, so a reader knows what to trust.

- `verified`: you ran it or measured it and saw the result.
- `read-only`: you read the code or docs; nothing was run. Static reads miss overrides (a later CSS rule, a feature flag, a wrapper).
- `agent-reported`: a subagent or reviewer said so and you have not opened the cited file:line. Keep its confidence next to it.
- `not run`: a check you skipped (e2e, a real device, a production read). Say why.

Rules:
- Spot-check agent findings (every high or medium, and any you will act on) before reporting them as findings. Say which you checked.
- Anything the user would act on must not rest on `read-only` or `agent-reported` alone without saying so. A feature that depends on a real device (push, install prompt, back-swipe) is `not run` until tried on one.
- Handoffs and PR bodies carry the labels forward; a resuming session re-checks `read-only` and `agent-reported` items before building on them.
