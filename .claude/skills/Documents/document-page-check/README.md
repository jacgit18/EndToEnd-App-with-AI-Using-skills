# document-page-check skill

A **pre-flight integrity check for a paginated document** — PDF, EPUB, or anything that
renders to fixed pages — run before Claude reads, quotes, summarizes, extracts from, or
answers questions about it. It checks two things and prints one report:

1. **Completeness** — the pages Claude can actually render/extract match the document's own
   declared count, the file isn't truncated (`%%EOF` + xref for PDF; every spine item
   resolves for EPUB), and each page carries its content (blank-page and image-only/OCR
   flags).
2. **Citation resolution** — every "see page N" / TOC / index entry an answer will lean on
   is checked against the physical page, after working out the printed-vs-physical offset
   (roman front matter, plate sections, body starting on the 13th sheet).

Then it asks whether a bad report should **gate** (stop work until reviewed) or just be
**noted**.

## Where it sits

This is the first skill in the `Documents/` group and it is a different shape from the rest
of the library. The other skills are **Socratic decision-gates** — they withhold an answer
until the user states a hypothesis or a prior decision, and they write an ADR. This one is
a **mechanical pre-flight**: it inspects a file, reports facts, writes nothing, and the only
thing it puts to the user is report-only vs gate.

```
document-page-check  →  is this document whole, readable, and correctly numbered   (this skill)  → report
                        before anything else is built on its contents
```

No sibling overlaps that fight. Nearest neighbours by theme:

- **`Documents/codebase-file-orientation`** — the other `Documents/` skill, and the exact
  opposite direction: it *produces* an orientation doc about a source-code file, this
  *checks* a paginated document that is about to be consumed. They share a group, not a
  request — tested CLEAN 2026-09-07. On "document how our module implements section 4 of
  this PDF" they chain: page-check the PDF section, then `codebase-file-orientation` (or
  `explaining-my-work`) writes the code side.
- **`Prompts/ambiguity-gate`** — fires when a *request* is ambiguous. This fires on a
  *document* being unreliable. A "summarize this PDF" request that's clear but backed by a
  truncated file is this skill's case, not ambiguity-gate's.
- **`Business/ticket-evaluation`** — separates what a ticket says from what it's missing.
  Unrelated mechanism; named only because both are "check the input before acting".

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The two-part check, the report block, the report-vs-gate ask, worked examples. |
| `pagination-mechanics.md` | Per-format detail — PDF page tree / xref / `%%EOF` / `/PageLabels`; EPUB OPF spine / `nav` page-list / NCX `pageList`; why `.docx`/HTML have no fixed pages; the offset method; a failure-signature table. |

## What it produces

A single report block in chat — document, completeness (extracted vs declared),
truncation state, unrenderable/image-only pages, the numbering scheme and offset, citations
checked, and a "safe to rely on" verdict — followed by the report-only vs gate question. No
files are written.

## Deliberately out of scope

- **Running OCR** — flags which pages need it and stops.
- **Fact-checking the document** — confirms the cited text is *on* the cited page, not that
  it's *true*.
- **Re-paginating / reformatting / rebuilding a TOC.**
- **Extraction-tooling choice** — uses whatever is available, reports what it couldn't get.
- **Non-paginated formats** (`.docx`, `.md`, `.html`, `.txt`) — says they have no stable
  page numbers and skips.

## Using it in another repo

Repo-agnostic and self-contained — writes nothing, reads no `docs/` tree.

```
cp -r ".claude/skills/Documents/document-page-check" /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Tested against the full skill set on 2026-09-04 (`Prompts/skill-interaction-testing`,
5 fresh-agent scenarios) — **all CLEAN, no description edits needed**:

- **vs `Prompts/ambiguity-gate`** — "check this PDF for me": this skill owns it end to end;
  ambiguity-gate classifies out rather than asking "check what?" (absorption).
- **vs `Skill Development/problem-solving-gates` (Rubber Duck)** — "the page numbers don't
  match the TOC, what's going on?": mechanical inspection, routes here; Rubber Duck stays
  dormant (no code, no hypothesis rep).
- **vs `Skill Development/learning-gate`** — "walk me through chapter 3 of this PDF": one
  lightweight file-check, then learning-gate does its own classification; no stacked
  precondition.
- **vs `Architecture/Data/caching-strategy`** — a design-doc PDF with a cache proposal:
  this skill does a short completeness pass and hands off; caching-strategy leads the
  decision (chain, not stack).
- **control** — a code refactor with no file attached: this skill stays fully silent.

Re-run the test when this skill's or a sibling's trigger description changes. The boundary
to keep holding: ambiguous *request* → `ambiguity-gate`; unreliable *file* behind a clear
request → here.
