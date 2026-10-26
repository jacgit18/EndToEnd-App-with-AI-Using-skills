# media-capture-pipeline skill

A gate skill, same shape as `pwa-adoption` and `caching-strategy`. Decides how a feature turns a camera or file photo into saved data: capture, extraction method, human confirm, image retention, cost cap and accuracy check.

## Where it sits

```
model-routing-decision   →  which model tier handles a call
claude-api (built in)    →  how to call the API: image blocks, structured output, caching
api-tooling-selection    →  how an agent integrates with an external system
pwa-adoption             →  installable / offline scope; a queued offline scan is its write question
legal-readiness-gate     →  what is owed for personal data in images
media-capture-pipeline   →  photo → trustworthy saved data, retention, cap, accuracy   (ADR)  ← this skill
```

None of these decide the pipeline between a photo and a saved record. This skill owns that gap and hands the model choice, API mechanics and legal duties to the siblings above.

## The shape

Refuses to recommend a method until the user states what the photo becomes and what a wrong value costs, who confirms, retention, a cost ceiling, whether data may leave the device, and how accuracy will be known.

## Origin

Built from a real case: scanning grocery receipts into the finance-dashboard (brief `receipt-scan.md` in the project docs). The brief is the case the isolation screen runs against.

## Packaging

Ships in the `architecture-skills` plugin (0.5.0), as a relative symlink in `plugins/architecture-skills/skills/`.
