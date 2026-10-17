# Production access (applies to every project)

- Reading production data is the owner's call. Use the project's read-only script or role; never write.
- Confirm the exact command with the owner first, and let the owner run commands that touch production.
- Ask for the least data that answers the question (counts, plan, last seen); no emails or other personal data in output, logs or reports unless needed.
- Never print secrets or connection strings; never paste them into reports or handoffs.
- Backups and dumps on disk are sensitive: create them mode 600 (`umask 077`), keep them out of git, and keep them in encrypted storage.
- Migrations run against the direct (non-pooled) database URL, only after the owner has the command and the rollback plan.
