# Example: Optimization Mode

**Context:** A search endpoint p95 is 1.2s; product owner wants it under 400ms.

**Precondition check:** Do I have a measurement? Not yet — I *think* it's the database query, because search is "always the query." That's a guess, not a measurement. So first I profile one real request end to end.

**Profile result:** 1180ms total — 240ms in the Postgres query, 90ms in the HTTP call to the ranking service, **780ms** in a Python loop that re-scores every one of ~5,000 candidate rows in the app after fetching them, 70ms spread thin.

**Me:** "Optimizing a search endpoint, p95 1.2s, target 400ms. I profiled a representative request: 780ms of the 1180ms is an in-app re-scoring loop over ~5,000 candidate rows; the query itself is only 240ms; ranking-service call 90ms. My plan: push the scoring into the SQL query as a computed expression so the loop goes away. What am I missing?"

**Claude:** "So the dominant cost — two-thirds of the request — is CPU in the re-scoring loop, not I/O. Confirming I read that right. Before moving scoring into SQL: does the score depend only on columns in that table, or on data from the ranking-service response too? If it needs the ranking-service output, it can't move into the query as written. And — do you need all 5,000 candidates scored, or just enough to fill the result page plus some margin? Cutting the candidate set with a cheaper pre-filter attacks the same 780ms without moving the logic."

**Me:** "...the score uses two columns from the table plus a recency weight we compute from `now()`. No ranking-service data in the score itself — that's a separate re-rank on the top 50. And no, we only show 20 results; we score 5,000 because that's what the candidate query returns."

**Claude:** "Then you have two independent levers on that 780ms, and the measurement supports both: move the per-row score into the query (all inputs are available there), and/or `LIMIT` the candidate set closer to what the page needs. Trade to name: a SQL-side score is harder to unit-test and tune than the Python, and a tighter candidate `LIMIT` risks dropping a row that would have re-ranked into the top 20. Re-profile after each change — if moving the score into SQL gets you to 400ms, the `LIMIT` change may not be worth the recall risk."

**Outcome:** I moved the score into the query and re-profiled: 210ms total, loop gone. I skipped the `LIMIT` change — the measurement said I didn't need it, and it carried a recall risk. Claude never guessed the bottleneck (I'd have gone in assuming "it's the query" without the profile) and didn't let me over-optimize once the number hit target.
