#!/usr/bin/env python3
"""Mechanical skill-catalog lint. Read-only.

Errors (exit 1 with --strict):
  - SKILL.md frontmatter: line 1 '---', line 2 'name: <dir>', 'description:' on line 3, closing '---'
  - a backticked skill-like name in a description that is not a skill directory (dead pointer)
Warnings:
  - description length over --desc-warn chars (default 1536)
  - SKILL.md longer than --lines-warn lines (default 250)
  - companion *.md in a skill dir never mentioned in that SKILL.md
  - one-way pointers: A's description names skill B, but B's SKILL.md never mentions A
    (summary count by default; --pairs lists them — many are legitimate hub fan-out)
Usage: lint.py [--strict] [--quiet] [--errors-only] [--pairs] [--root .claude/skills]
"""
import argparse, glob, os, re, sys

EXTERNAL = {  # real skills/commands that live outside .claude/skills
    "claude-api", "code-review", "security-review", "spec-executor", "equity-trade-decision",
    "sync-catalog", "new-skill", "skill-creator", "linkedin-humanizer", "linkedin-post-writer",
    "linkedin-comment-drafter", "linkedin-reply-handler",
}
TOKEN = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")


def read_frontmatter(path):
    L = open(path, encoding="utf-8").read().split("\n")
    errs = []
    if L[0] != "---":
        errs.append("line 1 is not '---'")
    if len(L) < 3 or not L[1].startswith("name: "):
        errs.append("line 2 is not 'name: ...'")
    if len(L) < 3 or not L[2].startswith("description:"):
        errs.append("'description:' is not on line 3")
    desc, k = "", 2
    if len(L) > 2 and L[2].startswith("description:"):
        first = L[2][len("description:"):].strip()
        if first in (">", "|", ">-", "|-"):
            k, buf = 3, []
            while k < len(L) and L[k].strip() != "---":
                buf.append(L[k].strip()); k += 1
            desc = " ".join(buf)
        else:
            desc = first
            k = 3
            if k < len(L) and L[k].strip() != "---":
                errs.append("description continues past line 3 without a folded block")
    closed = any(l.strip() == "---" for l in L[k:k + 2]) or (k < len(L) and L[k].strip() == "---")
    if not closed:
        errs.append("no closing '---' after the description")
    name = L[1][len("name: "):].strip() if len(L) > 1 and L[1].startswith("name: ") else ""
    return name, desc, errs, len(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".claude/skills")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--pairs", action="store_true")
    ap.add_argument("--errors-only", action="store_true", help="drop warnings and pointer counts")
    ap.add_argument("--desc-warn", type=int, default=1536)
    ap.add_argument("--lines-warn", type=int, default=250)
    a = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(a.root, "**", "SKILL.md"), recursive=True))
    skills = {os.path.basename(os.path.dirname(p)): p for p in paths}
    errors, warns = [], []
    body = {}
    descs = {}
    for n, p in skills.items():
        name, desc, errs, nlines = read_frontmatter(p)
        rel = os.path.relpath(p, a.root)
        if name and name != n:
            errs.append(f"name '{name}' != directory '{n}'")
        for e in errs:
            errors.append(f"{rel}: {e}")
        descs[n] = desc
        body[n] = open(p, encoding="utf-8").read()
        if len(desc) > a.desc_warn:
            warns.append(f"{rel}: description {len(desc)} chars (> {a.desc_warn})")
        if nlines > a.lines_warn:
            warns.append(f"{rel}: {nlines} lines (> {a.lines_warn}) — split candidate")
        for t in TOKEN.findall(desc):
            if t not in skills and t not in EXTERNAL:
                errors.append(f"{rel}: description names `{t}`, which is not a skill directory")
        d = os.path.dirname(p)
        for f in sorted(os.listdir(d)):
            if f.endswith(".md") and f not in ("SKILL.md", "README.md") and f not in body[n]:
                warns.append(f"{rel}: companion '{f}' is never mentioned in SKILL.md")

    oneway = []
    for a_, d in descs.items():
        for b in set(TOKEN.findall(d)):
            if b in skills and b != a_ and a_ not in body[b]:
                oneway.append((a_, b))

    if a.errors_only:
        warns, oneway = [], []
    total_desc = sum(len(d) for d in descs.values())
    if a.quiet and not errors and not warns:
        return 0
    print(f"skills: {len(skills)}   description total: {total_desc} chars (~{total_desc // 4} tokens)")
    for title, items in (("ERRORS", errors), ("WARNINGS", warns)):
        if items:
            print(f"\n{title} ({len(items)})")
            for i in items:
                print("  -", i)
    if not a.errors_only:
        print(f"\none-way description pointers: {len(oneway)}"
              + ("" if a.pairs else "  (use --pairs to list; many are legitimate hub fan-out)"))
    if a.pairs and not a.errors_only:
        for x, y in sorted(oneway):
            print(f"  - `{x}` names `{y}`; `{y}` never mentions `{x}`")
    return 1 if (a.strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main())
