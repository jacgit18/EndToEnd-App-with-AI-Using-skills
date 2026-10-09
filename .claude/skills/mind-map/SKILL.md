---
name: mind-map
description: Builds or updates an Obsidian JSON Canvas design mind map for a project from its docs (ADRs, data model, runbooks, audits), saved in the project's docs folder. Use for "mind map this project", "visualize how X is designed", "update the project map". Not for a single concept map (hand-draw it), nor `codebase-file-orientation` (one file's sidecar doc).
---

# Project design mind map

Produces `/home/jac/Videos/DevHiveMind/<project>/docs/architecture/<Project> Design Mind Map.canvas`.
Reference output: `iron-log/docs/architecture/Iron Log Design Mind Map.canvas`; reference generator: `gen_example.py` in this skill folder.

## Create

1. Read the project's docs first (`<project>/docs/`: ADRs, stack walkthrough, data model, feature map, runbooks, audits, backlog). Never invent; if there are no docs or no source, say the map shows only what is documented.
2. Pick ~8 branches that fit the project, 4 per side. Default set: Product, Client, Sync, Backend/API, Data, Auth & security, Hosting & ops, Quality & process. Rename or drop to fit.
3. Center node: project name, one line of purpose, the top priority. Each branch: a header node, then 4–7 leaf text nodes, one fact each.
4. Leaves link to real docs with `[[full/vault/path|alias]]` (vault root is `/home/jac/Videos/DevHiveMind`, so paths start with `<project>/docs/...`). Edges coloured per branch (canvas colours "1"–"6").
5. Generate with a Python script in the scratchpad (copy `gen_example.py`, replace the content lists), writing JSON Canvas (`nodes`, `edges`).
6. Verify: every wikilink resolves to an existing `.md` file, node ids unique, JSON parses.

## Maintain

When an ADR, data model, runbook or audit changes, update the matching branch in the same piece of work and say so. Keep leaves short; the docs hold the detail.

## Report

Path as a link, branch list, and what was not verified (the layout is not rendered in Obsidian from here).
