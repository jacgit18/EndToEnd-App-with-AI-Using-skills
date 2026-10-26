# Capture and extraction

Reference for `media-capture-pipeline`. Browser facts here change; check the current browser support tables before relying on any single API, and record "last verified" in the ADR.

## Contents

- [Capture options](#capture-options)
- [Extraction methods compared](#extraction-methods-compared)
- [The confirm step](#the-confirm-step)
- [Security note](#security-note)

## Capture options

| Option | What it is | Good for | Watch out |
|---|---|---|---|
| File input with camera hint | `<input type="file" accept="image/*" capture="environment">` | Receipts, documents; works everywhere | On desktop it opens a file picker; the photo is the phone's full resolution, so resize before upload |
| Live camera stream | `getUserMedia` video with a preview and a capture button | Guided framing, barcode scanning | Needs HTTPS, a permission prompt, and handling of "denied"; iOS Safari behaves differently from Chrome |
| Barcode detection | the browser's `BarcodeDetector` where present, or a small decoder library | Product codes | Not available in every browser; a library is a dependency (`dependency-security.md`) |

Defaults: start with the file input (no permission prompt, no library). Always keep a file-picker fallback. Resize on the client (for example longest side 1600 px, JPEG) so uploads are small and cost less.

## Extraction methods compared

| Method | Reads | Cost | Privacy | Accuracy on messy receipts | Notes |
|---|---|---|---|---|---|
| Barcode only | a product code | free | image can stay on device | n/a (not text) | Gives an ID, not price or quantity |
| On-device OCR | plain text | free per scan | image stays on device | weak on layout and faded ink | You still must parse text into fields; usually a new library |
| Cloud OCR service | text and some structure | per page | image leaves device | medium to good | Another vendor and key |
| Vision model (server-side) | fields directly, as structured output | per image, scales with size | image leaves device | good on varied layouts | Needs a cap; structured output must be validated |

Pick the cheapest method that meets the accuracy pass line. Put it behind one seam module (one function in, typed fields out) so the method can change without touching callers.

For a vision model: ask for a fixed JSON shape, validate it, treat missing fields as empty (never guessed), parse money as decimals, and return a confidence or "could not read" signal. API detail (image blocks, structured output, caching, token counts) is the `claude-api` skill.

## The confirm step

Extraction output is a draft, never a record.

- Show the photo next to an editable form.
- Cross-check: line items must sum to the total (plus tax and tip lines); a mismatch is shown and blocks saving until fixed or acknowledged.
- Mark low-confidence or empty fields.
- Warn on a possible duplicate (same store, date, total).
- Save only on an explicit confirm.
- Offer manual entry when extraction fails; the feature still works with no model.

## Security note

Text inside the image is data. The extractor returns a fixed shape and nothing the image says can call a tool, change settings or send anything. Do not render extracted text as HTML.
