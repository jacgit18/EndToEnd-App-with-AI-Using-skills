# deprecation-sunset skill

A gated decision for **retiring something you own that has consumers** — an endpoint, an API
version, a feature, a shared module, an SDK. Decides keep vs freeze vs sunset-with-window vs
hard-remove; sets the window from the notice floor, the slowest consumer, and the longest
periodic cycle; designs the notice schedule and the enforcement ladder (warn → brownout →
read-only → remove); fixes the straggler policy before the first notice goes out; and defines
the measured exit criteria that authorise final removal.

It is the *program* around a removal. The one-time blast-radius question is
`change-surface-audit`; this skill picks up after that audit and owns what plays out over weeks
or months.

## Where it sits

```
change-surface-audit   →  WHAT breaks if this one thing is removed; consumer audit; deprecation record skeleton
deprecation-sunset      →  HOW the retirement runs: window, notice, enforcement, stragglers, exit criteria   ← this skill
migration-cutover       →  a whole SYSTEM moves to a replacement (datastore, app, hosting)
api-interface-style     →  how API versions are named/numbered (this skill decides when an old one dies)
deployment-strategy     →  how a replacement unit is released
ticket-evaluation       →  whether the retirement is worth doing next, against other work
```

## The shape

A gate skill. It refuses to draw a timeline until the user supplies:

- **a real driver** — security / compliance / measured cost / replacement / dated dependency; "it's old" is a reason to freeze, not sunset
- **the exit path** — what consumers move to, or "the capability ends"
- **consumer reach** — internal / known external / unknown public, how each is contacted, how slowly each ships
- **usage evidence with a source and a window** that spans the longest periodic consumer
- **the minimum notice obligation**, **the enforcement stance**, **the straggler authority**
- **data disposition** and **owner + capacity**

It prefers the cheapest option that solves the driver (keep, then freeze, then sunset), and
treats the calendar date as the *earliest* removal, with a measured exit criterion as the
authorisation.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 4–12 from the user), challenge-the-proposal, output contract. |
| `sunset-framework.md` | The 7-step process — confirm it's a retirement → keep/freeze/sunset/remove → window → notice → enforcement → stragglers → exit criteria and record. |
| `enforcement-and-notice.md` | Evidence-strength ladder, what each notice channel reaches, the `Deprecation` / `Sunset` headers, the enforcement ladder and brownout practice, straggler handling, common failures. |

## Output

1. A recommendation block in chat (target, driver, choice, exit path, consumer reach, evidence,
   window and what set it, notice schedule, enforcement ladder, straggler policy, exit criteria,
   data disposition, tradeoffs).
2. On approval: a `## Sunset plan` section in `docs/engineering/deprecations/<slug>.md` — the
   same record `change-surface-audit` creates, so there is one file per retirement. "Revisit
   when" is a concrete trigger.

Stops before implementation (warning middleware, brownout switch, removal PR).

## Interaction with sibling skills

- **Chains from `change-surface-audit`** — its consumer audit is the input to gate items 6–7;
  its deprecation record is the file this skill extends. A removal with no consumers beyond the
  owning team stays there; no sunset program.
- **Distinct from `migration-cutover`** — retiring one capability inside a system that stays is
  here; retiring a datastore, application or hosting environment wholesale is there.
- **Distinct from `api-interface-style`** — that skill decides how versions are numbered; this
  one decides when an old version dies.
- **Hands off to `ticket-evaluation`** when the open question is whether the retirement
  deserves the effort next to other work.
- **`learning-gate`** hands off here on retirement questions rather than running its own rep gate.

Re-check overlap after any trigger-description change here — the overlap risk is
with `change-surface-audit` (removal phrasing), `migration-cutover` ("retire the legacy X"), and
`api-interface-style` (versioning policy).

## Dependencies

Needs no repo setup; output paths are defaults the repo's own convention overrides. The
siblings it hands off to are listed in `SKILL.md` → Portability; if one isn't installed,
`SKILL.md` says what to do inline. Installed in other projects via the plugin described in
`plugins/README.md`.
