# Evidence, notice, and enforcement

Reference for `SKILL.md` and `sunset-framework.md` steps 2–6.

---

## Usage evidence: how strong is "nobody uses it"?

Rank the evidence you have. The plan's window and enforcement ladder depend on this rung.

| Strength | Evidence | Blind spots |
|---|---|---|
| **Weak** | Team memory, a grep of your own repo, "we shipped the replacement a year ago" | Every external caller, every job outside the repo |
| **Moderate** | Access logs or metrics over a window shorter than the longest periodic consumer | Quarterly or annual consumers; callers behind shared credentials |
| **Strong** | Logs attributed per key or tenant, over a window that spans the longest periodic cycle, with the attribution source named | Anything that bypasses the logged path (direct DB reads, cached copies, a shared proxy that strips identity) |
| **Closed set** | The consumer set is enumerable by construction: every consumer needs a key you issued, every key has an owner | Keys shared outside the owner's team |

State the strength in the output. Weak or moderate evidence pushes toward **freeze** (to measure) or a longer window with brownouts; it never supports a hard remove.

How to run the underlying consumer audit — API consumers, database and ETL dependents, flags, caches, UI paths — is `change-surface-audit`'s `removal-and-silent-changes.md`. Do not redo it here; consume its findings.

---

## Notice channels: what each actually reaches

| Channel | Reaches | Misses |
|---|---|---|
| **Direct email or message to a named owner** | The one person who knows about the integration | That person left; the alias is dead |
| **Changelog / release notes** | People who read them | Most integrators, most of the time |
| **Docs banner** | People currently reading the docs | Anyone with a running integration who is not in the docs |
| **Status page or in-product notice** | People looking at the page | A headless integration |
| **Response headers** | Clients or middleware that log or alert on them | Nearly everyone, unless a client library surfaces them |
| **Log warnings on your side** | Only you | All consumers; use it to track who you have warned, not as notice |
| **Brownouts** | Everyone who depends on it, immediately and unavoidably | Nobody who isn't calling during the brownout |

The last row is why brownouts matter: every other channel is a message; a brownout is a consequence. Use direct contact for the known list, public channels for the unknown ones, and brownouts to test that the first two worked.

### The HTTP headers

- **`Deprecation`** (RFC 9745) — marks a resource as deprecated and carries the date it was, or will be, deprecated. Pair it with a `Link` header using `rel="deprecation"` pointing at the migration guide.
- **`Sunset`** (RFC 8594) — the date and time after which the resource is expected to become unresponsive. Use it with the dated end of the window.
- Both are signals for tooling and careful clients. They do not replace direct contact.

Check the current text of both RFCs before copying exact syntax into an implementation brief; this file names them so the plan can cite them.

---

## The enforcement ladder

| Rung | What it does | Use for |
|---|---|---|
| **Warn** | Headers, log lines, client-library warnings, docs banner. Behavior unchanged. | Day 0, always. |
| **Brownout** | The target fails or errors for a short, pre-announced slot, then recovers. Slots get longer as the date nears. | Surfacing consumers the evidence missed; making ignoring the notice cost something. |
| **Read-only** | Writes rejected, reads still work. | Targets that hold state consumers might still need to read or export. |
| **Remove** | The target is gone, ideally returning a clear error that names the replacement and the migration guide, not a generic 404. | The final dated event. |

Brownout practice:
- Announce slot times in advance, directly and publicly.
- Start short (an hour), then lengthen (a day) as the date approaches.
- Have a one-step revert and name who watches the support channel during the slot.
- Treat who complains during a brownout as new evidence: add them to the consumer list, contact them, and consider whether the window must stretch.

Remove practice:
- Keep a tombstone response for a while: a clear error with the migration link. A 404 looks like an outage; a 410 with a pointer looks like a decision.
- Removal is the **point of no return**. Name it in the record.

---

## Stragglers

A straggler is a consumer still calling at the date. Decide in advance (this is gate 10), and apply the same rule to everyone.

- **Surfaced by a brownout:** this is the system working. Contact them, offer the migration guide, and see whether they fit inside the current window.
- **Asks for an extension:** grant it per the cap, in writing, with a new dated end for that consumer only. Record it in `Status`.
- **Cannot migrate at all:** a real signal. Either the exit path is wrong (go back to gate 5), or the capability is genuinely needed (go back to step 2 and consider freeze).
- **Never responded:** the enforcement ladder applies; silence is not a reason to wait.

Track every straggler in the deprecation record's `Status` field: consumer, last request date, contact, extension granted.

---

## What goes wrong

- **Window set from the engineering calendar, not the consumer's.** The slowest consumer is the real floor.
- **Evidence window shorter than the longest periodic job.** The quarterly batch finds out on the removal date.
- **Notice by header only.** Most clients never read it.
- **No cap on extensions.** The date stops being a date.
- **Removal returns a generic 404.** Support receives "your API is down" instead of "I forgot to migrate".
- **A freeze with no review date.** A sunset you decided not to run, left running forever.
