# The eight layers

Source: a diagram of where project time goes, with eight kinds of work. A build estimate covers only "the work"; the other layers are real effort that often has no number until it shows up as overrun.

## Contents

- The layers and the question for each
- Inside versus outside the project
- Answer format
- estimates-log.md format

## The layers and the question for each

| # | Layer | What it holds | Question to ask |
|---|---|---|---|
| 1 | **Around the work** | meetings, reviews, project management | How much time goes to meetings, check-ins and reviews in total? (If you only know a weekly figure, give it and the number of weeks; I'll multiply.) |
| 2 | **To get the work** | research, experimentation, scoping, quoting, pitching | What did, or will, it take to win or scope this before any building? |
| 3 | **Before the work** | configuration, setup, services, infrastructure | What must exist before the first real line is written: accounts, environments, CI, data, access? |
| 4 | **The work** | the actual build, product, design, tests, docs | Your optimistic number for the build itself. (Asked first, in step 2.) |
| 5 | **Between the work** | iteration, debugging, refactoring, maintenance, tooling | Between the pieces, how much goes to fixing, reworking and tool friction? |
| 6 | **Beyond the work** | changes, omissions, nice-to-haves, scope creep | What is likely to be added, changed or discovered missing once someone uses it? |
| 7 | **Outside the work** | surprises, contingency, disasters, mission creep | What is the budget for the thing nobody predicted: a sick week, a dead dependency, a rewrite? |
| 8 | **After the work** | hosting, deployment, security, support, updates, fixes | Who runs this after it ships, and how much time per month does that take? |

The user does not have to know. `unknown` is accepted for every layer; the questions exist to put the layer in front of them.

## Inside versus outside the project

In the diagram the dotted "project" box holds layers 3 to 7. Layers 1, 2 and 8 sit outside it:

- **Around** and **To get** are usually unbilled to a client. A personal or employer project still pays them in time.
- **After** is ongoing, not a one-off. Ask for it per month and show it on its own line; never add it into project hours.

When quoting a client, ask the user which layers the quote covers; the box above is the diagram's convention, not a rule. When estimating your own time, count all eight.

## Answer format

Ask for each layer as `likely / worst-case`. Any figures shown as examples in this file show the *shape* only; never reuse them as defaults or suggestions. Accept:

- a pair of numbers;
- a single number (treated as likely; worst-case marked `unknown`);
- `unknown`: the layer is real but cannot be sized yet;
- `n/a` with a one-line reason. Challenge a thin reason once, by asking only for the reason; never propose a figure. Do not argue twice.

## estimates-log.md format

Lives in the journal root from the user's global CLAUDE.md (quote the path; it has spaces). It is a third log there, beside `decisions-log.md` and `problems-log.md`. New entries are appended; close-out edits only that entry's Status line and Actual column, and nothing else in the file.

```
## <id> <project or ticket name> (unit: hours)
Status: open
| Layer | Likely | Worst | Actual |
|---|---|---|---|
| around | <n> | <n> | |
| to get | unknown | | |
...
Notes: <one line: what "done" meant>
```

`<id>` is `YYYY-MM-DD-short-slug`, unique; close-out finds the entry by it, not by project name. After is recorded per month.

On close-out set `Status: closed <date>`, fill the Actual column from the user, and add one line: which layer missed most. The log's ratios (actual divided by likely, per layer) become quotable only after 3 entries are closed; until then the log just accumulates.
