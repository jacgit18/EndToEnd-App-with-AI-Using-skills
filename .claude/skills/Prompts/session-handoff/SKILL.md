---
name: session-handoff
description: Creates a handoff file to preserve context when a session is ending, getting long, about to be compacted, or work will resume later/in a new chat. Captures goals, current state, files touched, what changed, and next steps in a structured markdown file. Trigger this proactively — don't wait to be asked — whenever the conversation is running long, the user says something like "let's pick this up later," "I'll continue this tomorrow," "new chat," "wrap up," "save my progress," or when you notice context is getting heavy (many files touched, many decisions made, long back-and-forth). Also trigger when the user explicitly asks for a "handoff," "session summary," "context dump," or "recap file." Not for a post-mortem of a single already-resolved bug (symptom / cause / fix / worth-learning) — that's `problem-journal` (Journal mode); this skill preserves in-progress context so work can resume, it doesn't retrospect finished debugging.
---

# Session Handoff

Produces a single markdown file that lets the user (or a fresh Claude session) pick up exactly where this one left off — without needing the full chat history.

## When to offer this unprompted

Don't wait for the user to ask every time. Proactively suggest a handoff when you notice:
- The conversation has touched several files or made several distinct decisions
- The user signals they're stopping soon ("that's it for today," "I'll finish this later")
- You're doing multi-step work (debugging, a build-out, a refactor) that would be expensive to reconstruct from scratch
- The conversation is long enough that context compaction is a realistic risk

A one-line offer is enough: "Want me to write a handoff file before we stop, so the next session has full context?" Don't create the file without confirmation unless the user has already asked for one.

## What to gather

Before writing, pull together — from the conversation, not from guessing:

1. **Goal** — what the user is actually trying to accomplish, in their words if possible. Distinguish the overall goal from today's specific sub-task.
2. **Current state** — where things stand right now. What's working, what's broken, what's mid-change.
3. **Files touched** — every file created, edited, or centrally discussed. Include path and a one-line note on its role.
4. **What changed** — a concrete list of the actual changes made this session (not a narrative of the conversation — the deltas).
5. **Open decisions / constraints** — anything the user decided on, ruled out, or specified as a requirement. These are easy to silently drop on a fresh start.
6. **Next steps** — the specific next action(s), in order. Not a generic "continue working on X" — the actual next move.

If any of these is genuinely unclear or missing (e.g., you don't know if a change is finished or half-done), ask rather than guessing — a wrong guess here is worse than a short pause, since the whole point is accuracy for someone with zero other context.

If a `spec-drift-gate` spec document already exists for this build, **link to it** for items 1 and 5 (Goal, Open decisions / constraints) rather than re-deriving them from the conversation — the spec is the source of truth for problem framing and scope; duplicating it here risks the copy drifting from the original.

## Output format

Write to a markdown file. Use this structure:

```markdown
# Session Handoff — [short task name]
_[date]_

## Goal
[1-3 sentences: what this work is for]

## Current State
[Where things stand right now — what's done, what's in progress, what's broken]

## Files Touched
- `path/to/file` — [what it is / what changed]
- `path/to/file` — [what it is / what changed]

## What Changed This Session
- [concrete change]
- [concrete change]

## Decisions & Constraints
- [anything decided, ruled out, or required — only include if there are real ones]

## Next Steps
1. [specific next action]
2. [specific next action]
```

Omit a section entirely if it has nothing real to put in it (e.g., no firm decisions were made) — don't pad with placeholder text.

## Delivery

- Keep it tight — this is a working document, not a report. Prefer bullets and short lines over paragraphs.
- Save it as a file (`.md`) and present it to the user rather than just printing it in chat, so it's easy to carry into the next session or hand to a fresh Claude instance.
- Suggest a short, descriptive filename (e.g., `handoff-auth-refactor-2026-09-02.md`), not a generic one.
- After creating it, tell the user in one line where it is and that they can drop its contents into a new chat to resume — don't over-explain.
