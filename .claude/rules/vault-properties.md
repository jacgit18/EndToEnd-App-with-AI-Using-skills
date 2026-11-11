# Vault documents keep intact properties (applies to every project, 2026-11-02)

<!-- toc -->
## Contents

- [[#The rules]]
<!-- /toc -->

Every markdown document written into the vault starts with a valid properties block (YAML frontmatter). A broken block is silent damage: Obsidian shows the properties as raw text or drops them, Bases, Dataview and the publish filter (`dg-publish`) skip the note, and the generated table of contents (`document-toc.md`) lands in the wrong place. Found 2026-11-02: 5 of 391 project docs had a value YAML cannot parse (an unquoted `[[wikilink]]` in `Relates`, a `: ` inside `Status`), and the brief template had no block at all, so every brief copied from it started without one.

## The rules

1. **Line 1 is `---`.** Nothing above it: no blank line, no BOM, no H1, no comment. A new document starts with the block, then the `# Title`.
2. **The block is closed** by a second `---` line before any content, and holds only properties. The `<!-- toc -->` markers go below the closing `---`, never inside.
3. **Use the vault property set**, keys spelled exactly (case matters): `dg-publish`, `tags`, `author`, `banner`, `banner_x`, `banner_y`, `cssclasses`, `Comments`, `Purpose`, `Status`, `Started`, `EditDate`, `Relates`. Keep empty keys empty (`tags:`), do not delete them. Knowledge notes may add `type`, `source`, `verified`, `Peer Reviewed` (see `Documentation Criteria.md`). Copy an existing doc's block or a template; do not retype it.
4. **Required on every document:** `Purpose` (one line), `Status`, `EditDate` (today's date, `YYYY-MM-DD`). Set `Started` when the document is created and refresh `EditDate` on every edit.
5. **Quote what YAML would misread.** Wrap the value in double quotes when it contains `: ` or ` #`, or starts with `[`, `{`, `*`, `&`, `!`, `|`, `>`, `%`, `@` or a backtick. A wikilink value is always quoted: `Relates: "[[049-paid-subscriber-flag]]"`. Several links are a list of quoted items, one per line. Escape an inner `"` as `\"`, or use single quotes.
6. **One key once.** No duplicate keys; lists are `key:` followed by indented `  - item` lines, indented with spaces, never tabs.
7. **Edit in place, never rewrite the block.** An edit that changes the body leaves the properties alone except `EditDate` (and `Status` when it changed). When using Edit, match the line you change; when using Write on an existing file, read it first and carry the whole block over unchanged.
8. **Check before saying done:** `node /home/jac/.claude/scripts/fm-check.mjs <file-or-folder>` (exit 1 on a broken or incomplete block). It runs automatically after a Write or Edit under `DevHiveMind/Projects/`; its message is what to fix, right then.
9. **Templates carry the block.** Any template that creates a vault document (briefs, ADRs, handoffs, audits, journal entries) starts with the property block, so copies are valid from the first line.

## Exempt

- `archive/`, `images/`, `node_modules/` (frozen copies, same as `document-toc.md`).
- Files a tool reads and that must not carry properties: `CLAUDE.md`, JSON Canvas, `.base`.
- A repo document outside the vault (`README.md`): follows the repo's own convention.

## Enforcer

- Script `~/.claude/scripts/fm-check.mjs` (line-based; no YAML library): errors on no block on line 1, no closing `---`, tab indent, duplicate key, unquotable value, unbalanced quote, toc marker inside the block, missing `Purpose`, `Status` or `EditDate`. `--require=` changes the required list.
- Hook `~/.claude/hooks/doc-toc.sh` runs it after every Write/Edit of a `.md` under `DevHiveMind/Projects/` and exits 2 with the message, so the problem reaches the agent at once. Run by hand over a folder when onboarding a project, and add `fm-check.mjs` to a project's docs check if it has one.
- Baseline 2026-11-02: 390 project docs checked, 0 broken, after the 5 fixes above (`verified`). A hand-run over other vault folders (knowledge notes, Personal) was `not run`; their property sets differ.

Related: `document-toc.md` (the toc sits under the block), `rule-enforcers.md`, `definition-of-done.md` (docs line), vault `Documentation Criteria.md`.
