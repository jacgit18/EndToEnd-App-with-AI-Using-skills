# user-story-decomposition skill

Turns a stated feature or epic into sprint-ready backlog items. It forces two steps in
order: a **format decision** (use case vs user story) and a **breakdown discipline**
(epic, story, acceptance criteria), each held to an INVEST-style quality bar and a
Definition of Ready. It withholds stories until the user has stated the epic/feature, the
real actor(s), and the format signal; it never invents personas, benefits, or acceptance
criteria. Optional passes: a documentation-cadence lens, a "documentation candidate" flag,
and a MoSCoW triage over a batch of stories.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The three-item gate, format decision, the ladder, story writing, quality bar, Definition of Ready, output block, red flags. |
| `out-of-scope.md` | Full reasoning behind the one-line hand-offs. Read when a request sits near a sibling boundary. |
| `splitting-stories.md` | The six splitting questions for a story that is too big. |
| `documentation-cadence.md` | The documentation-cadence split test, the "documentation candidate" criteria, and the closing-date rule. Read for the optional documentation passes. |
| `moscow.md` | The Must / Should / Could / Won't category table. Read for the optional prioritization pass. |
| `worked-example.md` | Condensed epic to stories to acceptance-criteria example (card-game app). |

## Where it sits

- **Input from `design-scoping`** — its in-scope functional list is this skill's input;
  scoping a whole system stays there and is not re-opened here.
- **`entry-point-first`** — a user stalled before starting goes there first; a feature or
  epic that then needs breaking down comes back here.
- **`ambiguity-gate`** — a vague ask with no established feature.
- **`ticket-evaluation`** — takes over once these are real tickets and someone needs a
  sprint-worthiness verdict; this skill does not judge or size a written ticket.
- **Specialist Architecture skills** (`database-architecture`, `api-interface-style`,
  `microservices-decision`, `access-control-modeling`) — the technical design a story
  implies; this skill only flags the load-bearing decision.
- **`technical-cost-decision`** — when acceptance criteria imply a real recurring cost.
- **`explaining-my-work`** — the writeup of a story, only once it is closed (voice:
  `software-carpentier-brand`). This skill flags candidates but never hands off early.

Stakeholder elicitation is unowned, and UML diagrams are out of scope.

## Output

Stories (or a use case) with acceptance criteria in chat, plus quality-bar and Definition of
Ready gap lists. It writes no files.

## Using it in another repo

Repo-agnostic. Copy the directory into the other repo's `.claude/skills/`:

```
cp -r .claude/skills/user-story-decomposition /path/to/other-repo/.claude/skills/
```
