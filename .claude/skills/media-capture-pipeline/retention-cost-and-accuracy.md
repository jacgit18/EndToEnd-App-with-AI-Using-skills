# Retention, cost and accuracy

Reference for `media-capture-pipeline`. Prices and limits change; a number in an ADR is labelled "estimate" or "measured on N scans".

## Contents

- [Image retention](#image-retention)
- [Cost and caps](#cost-and-caps)
- [Accuracy check](#accuracy-check)
- [Failure states](#failure-states)

## Image retention

| Choice | Pros | Cons |
|---|---|---|
| Delete after confirm | least privacy risk, no storage cost | cannot re-check a scan later |
| Keep N days | lets the owner re-check, then clears itself | needs a cleanup job |
| Keep until the owner deletes | works as a record | unbounded storage, needs delete and export, backup size grows |
| Owner chooses per scan | matches how people use receipts | one more control and one more state to test |

Rules whichever is chosen: images are served only to the signed-in owner; deleting a record deletes its image; a kept image is in the backup note; images are never logged, never in error reports. A kept image of a personal document may carry legal duties: flag it to `legal-readiness-gate` if there is more than one user.

## Cost and caps

- Per-scan cost for a vision model scales with image size and output length: resize first.
- Cap scans per user per month, show "N of M used", enforce the cap **before** calling the API, and keep manual entry working at the cap.
- Estimate at the cap and at 10x usage; label the number an estimate until measured on the first real scans.
- Failed and retried scans cost too; decide whether a failure counts against the cap (default: no, but limit retries per scan).
- A cap by itself is a cost ceiling; a paid tier only matters when there is more than one user (`feature-planning.md`).

## Accuracy check

- Build a small sample set: 5 to 10 real examples with the expected output written by hand. Keep them out of the repo if they hold personal data.
- Run the real extractor against them by hand when the method, model or prompt changes; compare field by field, not by feel.
- Pass line: written before the run (for example all totals exact, at least 90 percent of line items exact).
- CI uses a mocked extractor; a real-model run is a manual step and is reported as such (`evidence-labels.md`).
- Re-run when the provider changes the model.

## Failure states

Blurry or not a receipt; model or network error; permission denied for the camera; offline; image too large; cap reached; duplicate; totals mismatch. Each has a visible message and a manual-entry path, and none saves anything on its own.
