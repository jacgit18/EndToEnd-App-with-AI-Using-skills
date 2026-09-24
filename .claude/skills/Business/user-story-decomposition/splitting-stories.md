# Splitting a story that's too big

Read from `SKILL.md` when a story fails the size check. Check whether all of these are needed *right now*, in this order — drop or defer whichever
aren't:

- **Conditions** — are all the stated conditions required immediately, or can some wait?
- **Workflow steps** — is this too many steps for one slice?
- **Paths** — does the happy path alone deliver value, with alternates deferred?
- **Operations** — are all the named operations (create/read/update/delete/etc.) needed now?
- **Acceptance criteria** — are all the test scenarios needed at this point, or do some
  belong to a later story?
- **Data / interfaces / platforms** — are all the named variations (formats, integrations,
  client platforms) needed immediately?

A story that fails this check is written as two or more stories, not one story with a longer
list of acceptance criteria.
