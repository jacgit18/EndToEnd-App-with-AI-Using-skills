---
name: document-page-check
description: A pre-flight integrity check for any paginated document (PDF, EPUB, and other formats that render to fixed pages) before Claude reads, quotes, summarizes, extracts from, or answers questions about it. It verifies two things. (1) Completeness — the number of pages Claude can actually render or extract matches the document's own declared page count; the file is not truncated (PDF ends with %%EOF and its xref/trailer are intact; every EPUB spine item resolves); and each page actually carries the content it should (flagging pages that are blank when they shouldn't be, and image-only pages with no text layer that need OCR). (2) Citation resolution — for every "see page N" / "p. N" / table-of-contents entry / index entry that an answer will lean on, going to that physical page and confirming the referenced content is really there, after working out the printed-label-vs-physical-index offset (roman-numbered front matter, body that starts at printed "1" on the 13th sheet, plate sections). It emits a compact page-map + integrity report, then asks whether to gate (stop until the user has reviewed the findings) or just proceed with the original task. Use when a PDF or EPUB is attached or referenced and the user says "read this", "summarize this book / report / paper", "what does it say on page 40", "pull the section on X", "check the citations in this", "is this file complete", "did the whole thing come through", "the page numbers look off", "the TOC doesn't match", or "quote the part about Y". Not for running OCR (it flags the need and stops), not for fact-checking the document's claims beyond "the cited text is on the cited page", not for re-paginating or reformatting a document, not for choosing extraction tooling or libraries. Formats with no fixed pagination — raw .docx, .md, .html, .txt — have no page numbers to check; say so and skip the check. Not for authoring a companion / orientation doc about a source-code file (its role, entry points, dependencies, gotchas) — that is `codebase-file-orientation`, the opposite direction: it produces a doc about code rather than checking a document being consumed.
---

# Document Page Check

A paginated document handed to Claude can be quietly broken in ways that corrupt every
answer built on it: the upload was truncated, the last chapter never came through, a run of
pages is scanned images with no text, or the numbering the document uses for its own
cross-references is offset from the page positions Claude is counting. This skill runs a
short pre-flight before the document is used for anything — it checks that the whole thing
is present and readable, resolves the page-number scheme so later references are
unambiguous, spot-checks the citations an answer will depend on, and prints a compact
report. It is a mechanical check, not a reasoning gate; the only decision it puts to the
user is whether a bad report should **stop** work or just be **noted**.

## When to use

- A **PDF or EPUB is attached or referenced** and the user wants it read, summarized,
  quoted, searched, or used to answer a question.
- The user asks about **a specific page**: "what's on page 40", "quote page 112", "the
  table on p. 8".
- The user suspects a **pagination or completeness problem**: "the page numbers seem off",
  "the TOC links are wrong", "I don't think the whole file uploaded", "is this the full
  document".
- The user asks to **check or follow the citations / cross-references** in a document.
- Before Claude itself **cites a page number** back to the user from a document — resolve
  the offset first so the citation is correct.

## Out of scope

- **Running OCR.** If pages are image-only with no text layer, the skill names which pages
  and stops. Actually OCR-ing them is a separate, explicitly-started step.
- **Fact-checking the document.** The citation check confirms *the cited text is on the
  cited page*, not that the claim it makes is true.
- **Re-paginating or reformatting** — fixing the numbering, rebuilding the TOC, splitting
  or merging files.
- **Extraction-tooling choice** — which library or command pulls the text. The skill uses
  whatever is available and reports what it could and couldn't get.
- **Non-paginated formats** — raw `.docx`, `.md`, `.html`, `.txt`, a Google Doc. These have
  no fixed page numbers. Say so and skip; if the user cites "page N" of one, tell them it
  has no stable pagination.

---

## The check

Run both parts. Keep notes for the report block.

### 1. Completeness — is the whole document here and readable

1. **Declared page count.** Get the document's own count:
   - **PDF** — the page tree root (`/Type /Pages` → `/Count`), or the count reported by a
     PDF tool. Note if the file is linearized ("fast web view") and only partially present.
   - **EPUB** — the number of spine items (`<spine>` in the OPF), and, if present, the
     page list (`nav` with `epub:type="page-list"`, or the NCX `pageList`).
2. **Rendered / extracted count.** How many pages can actually be opened or pulled. Compare
   to the declared count. Any shortfall is a **MISMATCH** — the file is likely truncated or
   the extractor gave up partway.
3. **Truncation signs.**
   - **PDF** — file ends with `%%EOF`; the xref table / trailer resolves; no "damaged /
     repaired" warning from the reader; the last page renders.
   - **EPUB** — the zip opens cleanly; `container.xml` and the OPF parse; every spine
     `idref` points to a file that exists in the archive.
4. **Per-page content.** Scan for pages that are **blank when they shouldn't be** (mid-body
   blank pages, not deliberate section breaks) and runs of pages that are **image-only with
   no extractable text** — a scanned or flattened section that needs OCR before it can be
   read or quoted.
5. **Numbering scheme.** Identify the front-matter / body / back-matter boundaries and how
   the document numbers itself: e.g. `i–xiv` roman front matter, then `1–356` arabic
   starting on the 15th physical page; plate sections that interrupt the sequence;
   `/PageLabels` in a PDF if set. Record the **offset**: `printed page 1 = physical/PDF
   page 15 (+14)`.

### 2. Citation resolution — do the references land

For every page reference an answer will rely on — one the user gave, one the document makes
about itself (TOC, index, "see p. N", "as noted on page 12"), or one Claude is about to
make back to the user:

1. **Apply the offset** from step 1.5 to convert the printed number to a physical/PDF page.
2. **Go to that page** and confirm the referenced content is actually there — the chapter
   the TOC promises, the figure the text points to, the term the index lists.
3. **On a miss**, widen by ±2 pages and report the discrepancy: the reference points to
   printed page N, content found on printed page M, likely cause (offset not applied,
   stale TOC from before a revision, plate section shifting the count).
4. If the document is large and citations are many, check the TOC top-level entries, the
   user's specific references, and a sample of in-text "see page" pointers — not every
   index line. Say what was sampled.

---

## The report

Emit this block before doing anything else with the document:

```
Document:          <filename>  ·  <PDF | EPUB | other>  ·  <declared page count>
Completeness:      <extracted N / declared N>  —  <OK | MISMATCH: last page reached is X>
Truncation:        <clean — %%EOF + xref intact | PDF ends mid-stream, no %%EOF | EPUB: spine items A, B unresolved>
Renderable pages:  <all N | blank mid-body: pp. X, Y | image-only, no text layer: pp. A–B (OCR needed to read/quote these)>
Numbering:         <e.g. front matter i–xiv, body 1–356; printed page 1 = PDF page 15 (offset +14); plate section between pp. 180–181>
Citations checked: <n checked, all resolved with offset applied | TOC "Chapter 7 · p.203" lands on p.211; index term "latency" p.88 not found near there>
Safe to rely on:   <yes | yes, with the caveats above | NO — <what has to happen first: re-upload, OCR pp. A–B, confirm intended numbering>>
```

## Then ask

After the report, ask the user which behaviour they want:

- **"Report only"** — note the findings and proceed with the original task.
- **"Gate"** — stop here until the user has reviewed the report and says to continue.

Default recommendation: if `Safe to rely on` is **yes**, proceed. If it is **NO** or
carries a caveat that the requested task depends on (a MISMATCH when they asked for a full
summary; an unresolved citation when they asked you to follow the references; an image-only
range when they asked what it says), recommend **Gate** and say why in one line.

---

## Reference file

- `pagination-mechanics.md` — how page count, truncation, page labels, and the page list
  are actually determined in each format (PDF page tree / xref / trailer / `%%EOF` /
  `/PageLabels` number tree; EPUB OPF spine / `nav` page-list / NCX `pageList`; why `.docx`
  and HTML have no fixed pages), the offset-detection method, and the common failure
  signatures — partial linearized PDF, Ghostscript export cut short, scanned PDF with no
  text layer, EPUB with a missing or stale page-list, TOC built before a re-paginating
  revision.

---

## Portability

Repo-agnostic and self-contained — it writes no files and touches no `docs/` tree, it just
inspects a document and reports. Copy the `document-page-check/` directory into another
repo's `.claude/skills/` to use it there.

```
cp -r ".claude/skills/Documents/document-page-check" /path/to/other-repo/.claude/skills/
```

See `README.md` for how it sits next to the other skills.

---

## Example invocations

> "Summarize this — attached the PDF of the annual report."

Run the check first. Declared 84 pages, extractor reached 84, ends with `%%EOF`, xref
intact. Pages 61–68 are image-only (scanned financial statements) with no text layer.
Front matter i–iv, body 1–80, printed page 1 = PDF page 5 (+4). Report it; `Safe to rely
on: yes, with the caveat that pp. 61–68 (the statements) can't be read without OCR`.
Recommend proceeding with the narrative summary and flagging the statements section as
not-summarized. Ask: report only or gate.

> "What does it say on page 210 about churn?"

Resolve the offset before answering. Front matter is xii pages, body starts on PDF page 13,
so printed page 210 = PDF page 222. Go there, confirm the churn passage is on it, quote it,
and state "printed page 210 (PDF page 222)". If PDF page 222 is a different topic, widen ±2,
report where the churn discussion actually sits, and give the corrected number.

> "Check this EPUB is the complete book before I send it to the editor."

Completeness only, then gate by default (their ask *is* the check). Spine has 32 items;
`container.xml` and OPF parse; all 32 `idref`s resolve; no page-list present (normal for
reflowable EPUB — note it). If item 30 (`chapter-28.xhtml`) is referenced by the spine but
absent from the archive: `Truncation: EPUB spine item chapter-28.xhtml unresolved`,
`Safe to rely on: NO — re-export, chapter 28 is missing`, recommend Gate.

> "Pull the methodology section — it's a .docx."

No fixed pagination. Tell the user `.docx` has no stable page numbers (they depend on the
renderer, font, and page size), locate the methodology section by heading instead, and
skip the page check.
