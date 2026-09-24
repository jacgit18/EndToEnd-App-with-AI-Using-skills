# Example: Options Generator Mode

**Context:** I'm adding search to a small app and need to decide how before writing code.

**Precondition check:** Do I have named constraints and an initial lean? Yes — ~50k rows, self-hosted with no budget for a managed service, needs typo tolerance. My lean: Postgres full-text search (`tsvector`), since I already run Postgres.

**Me:** "I'm deciding how to implement search. Constraints: ~50k rows, self-hosted, no budget for a managed service, need typo tolerance, already running Postgres. My lean is `tsvector`. What am I missing?"

**Claude:** "Does full-text search actually give you typo tolerance, or were you planning to add something for that? Have you considered `pg_trgm` — trigram similarity, also built into Postgres — instead of or alongside `tsvector`? And is Postgres a hard constraint, or just a lean?"

**Me:** "Postgres is a hard constraint. And no, I hadn't separated typo tolerance from full-text search — I was conflating the two. `pg_trgm` for fuzzy matching plus `tsvector` for ranking is probably the real answer."

**Claude:** "That tracks. Anything in your constraints that a self-hosted alternative like Meilisearch or Typesense would satisfy that this combination doesn't — or is 'no budget' specifically about hosted/paid services?"

**Me:** "I meant no budget for a *hosted* service. But operating another container is exactly what I was avoiding by leaning on Postgres, so I'm sticking with `tsvector` + `pg_trgm`."

**Outcome:** Decision made — `tsvector` for ranking, `pg_trgm` for typo tolerance, no extra service. Claude surfaced a gap (typo tolerance wasn't actually covered) and a real alternative, without ranking anything or picking for me.
