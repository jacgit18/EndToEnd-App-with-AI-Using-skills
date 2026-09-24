# Pagination mechanics

How to determine, per format, whether a document is complete, where its pages are, and how
its own numbering maps to physical page positions. Reference for `SKILL.md`'s two-part
check.

---

## PDF

### Page count

- The page tree root is a dictionary `/Type /Pages` with `/Count N` — `N` is the
  authoritative page count. Intermediate `/Pages` nodes also carry `/Count`; the root's is
  the total.
- Any PDF tool reports it: `pdfinfo file.pdf` → `Pages:`, `qpdf --show-npages file.pdf`,
  `mutool info file.pdf`. In Claude Code, the Read tool's `pages` parameter reads a PDF —
  ask for a range past the expected end and see where it stops.
- **Linearized ("fast web view") PDFs** put a partial cross-reference at the front so a
  viewer can show page 1 before the whole file arrives. A truncated download of one renders
  the first pages and fails later — the declared `/Count` will exceed what actually opens.

### Truncation / integrity

- A well-formed PDF ends with the literal `%%EOF` after a `startxref` offset. Missing or
  mid-stream ending ⇒ truncated.
- The cross-reference table (`xref` + `trailer`) or cross-reference stream must resolve.
  `qpdf --check file.pdf` reports damage, missing objects, and whether it had to recover
  the xref. `pdfinfo` prints nothing useful on a broken file; `qpdf --check` and
  `mutool clean` are the tells.
- "Repaired" / "rebuilt xref" warnings from a reader mean the file was damaged and
  reconstructed — usable but worth flagging.
- The last page failing to render while earlier pages are fine is the classic partial
  upload / interrupted export signature.

### Printed page numbers vs physical index (the offset)

- Physical/PDF page index is 1..N in file order. What is *printed* on the page — or shown
  in a viewer's page box — can differ.
- **`/PageLabels`** (in the document catalog) is a number tree mapping page indices to
  label ranges. Each range dict:
  - `/S` style — `/D` decimal, `/r` lowercase roman, `/R` uppercase roman, `/a` / `/A`
    letters; absent `/S` with only `/P` means a plain prefix with no number.
  - `/P` a prefix string (e.g. `"A-"` for appendix pages `A-1`, `A-2`).
  - `/St` the starting number for the range (default 1).
  - Example: `{0 << /S /r >> 12 << /S /D >>}` = physical pages 1–12 are `i`–`xii`, physical
    page 13 onward is `1`, `2`, … so **printed 1 = physical 13, offset +12**.
- Most PDFs have **no `/PageLabels`**. Then determine the offset by inspection: find the
  physical page that prints "1" (or shows the first body content), and
  `offset = physical_index_of_printed_1 - 1`.
- Things that break a single global offset: roman front matter, unpaginated plate/photo
  sections inserted mid-book, per-chapter restarts, appendices with prefixed numbers,
  blank verso pages counted or not counted by the publisher. When the offset isn't
  constant, record it per span.

### Per-page content

- A page whose content stream is empty or whitespace-only ⇒ blank. Deliberate (section
  breaks, chapter-end versos) vs unexpected (a gap mid-paragraph) is a judgement call from
  context.
- A page that renders visually but yields **no extractable text** is image-only — a scan or
  a flattened export. `pdffonts` showing no fonts for those pages, or `pdftotext`
  returning empty for a page that clearly has prose, confirms it. These need OCR before
  they can be read or quoted; name the range and stop.

---

## EPUB

An EPUB is a ZIP. `unzip -l book.epub` lists entries; unpack to inspect.

### Structure and reading order

- `META-INF/container.xml` points to the OPF package file (usually `OEBPS/content.opf` or
  `content.opf`).
- The OPF `<manifest>` lists every content file with an `id`. The OPF `<spine>` is an
  ordered list of `<itemref idref="...">` — **this is the reading order and the page/section
  count** for a reflowable EPUB.
- Completeness check: every spine `idref` resolves to a manifest `item`, and every such
  `item`'s `href` exists in the archive. A spine entry with no file in the zip = missing
  chapter = truncated export.

### Page numbers

- Reflowable EPUBs have **no inherent page numbers** — pagination depends on the reading
  system, font size, and screen. This is normal; say so rather than reporting it as a
  fault.
- Some EPUBs carry an explicit page list tied to a print edition:
  - **EPUB 3** — the navigation document (`nav.xhtml`) has a
    `<nav epub:type="page-list">` of links, and content files contain
    `<span epub:type="pagebreak" id="..." title="N"/>` (or `role="doc-pagebreak"`) markers
    at the print page boundaries.
  - **EPUB 2** — the NCX file (`toc.ncx`) may have a `<pageList>` with `<pageTarget>`
    entries.
  - If present, these give a real printed-number → location map; use them to resolve "page
    N". If absent, tell the user the EPUB can't answer a "page N" question and offer to
    locate by chapter/heading instead.
- **Fixed-layout EPUBs** (`rendition:layout-pre-paginated` in the OPF) — each spine item is
  one page, so spine order ≈ page number, and a missing spine file is a missing page.

### Truncation / integrity

- `unzip -t book.epub` tests the archive CRCs — a failure means a corrupt/partial file.
- `container.xml` or the OPF failing to parse as XML ⇒ broken.
- The first ZIP entry of a valid EPUB should be an uncompressed `mimetype` file containing
  exactly `application/epub+zip`; its absence signals a malformed or re-zipped file.

---

## Formats with no fixed pagination

`.docx`, `.odt`, `.md`, `.html`, `.rtf`, plain `.txt`, Google Docs — page breaks are
computed by the renderer from font, page size, and margins, so "page N" is not stable and
not stored in the file. `.docx` may contain a cached `<w:lastRenderedPageBreak>` from the
last time Word painted it, but it's advisory and often stale.

For these: state that there are no page numbers to check, and locate content by heading,
section, or search string instead. If the user cites "page N" of one, explain the number
isn't reproducible.

Note: a `.docx` *converted to PDF* then gets whatever pagination the converter produced —
check the PDF, and be aware its numbers won't match anyone else's conversion.

---

## Common failure signatures

| Symptom | Likely cause |
|---|---|
| `/Count` says 300, reader opens 180 and errors | Truncated download / interrupted export; linearized PDF partially transferred |
| No `%%EOF`; `qpdf --check` reports missing objects | File cut off mid-write |
| "Rebuilt cross-reference table" warning | Damaged xref, recovered — usable, flag it |
| A run of pages renders but `pdftotext` returns nothing for them | Scanned / image-only section — OCR needed |
| TOC entry "p. 203" consistently lands ~8 pages late | Global offset not applied (roman front matter) |
| TOC offset is right early, drifts later | Unpaginated plate section or inserted pages mid-book |
| EPUB opens but one chapter is blank / 404 in reader | Spine references a manifest item whose file is missing from the zip |
| "Page N" request on an EPUB has no stable answer | Reflowable EPUB with no `page-list` / `pageList` |
| `.docx` page numbers don't match between two people | Expected — pagination is renderer-computed, not stored |
