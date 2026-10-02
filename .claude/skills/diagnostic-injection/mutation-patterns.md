# Diagnostic Mutation Patterns

## Quick reference: mutation type by hypothesis

| Hypothesis | Mutation | Why it works |
|---|---|---|
| Function is not being called | Add `print("called")` or `raise Exception()` | If you don't see it, function is skipped |
| Function returns too early | Delete/comment the `return` statement | If work continues, early return was the problem |
| Value is not being cached / cached value is stale | Force a cache miss: `return None` or skip the cache check | If performance drops, cache was working; if it stays slow, cache wasn't helping |
| Async task never completes | Add `return` before the `await` | If task exits instantly, async work was being skipped |
| Permission check is missing or wrong | Delete/comment the check | If unauthorized access succeeds, the check was needed |
| Variable is mutated unintentionally | Save the original value, `print(before/after)` | If values differ, unintended mutation is happening |
| Loop is iterating too many times | Add `break` after first iteration | If symptom disappears, loop iteration is the cause |
| Computation is expensive | Replace with a constant or mock result | If symptom goes away, this computation was the bottleneck |
| I/O is slow (disk, network) | Skip the I/O: `return dummy_data` | If symptom disappears, I/O was slow |
| Timezone conversion is wrong | Use a fixed timezone or raw time | If symptom changes, conversion is involved |

## Real-world examples

### Example 1: Cache stale-key bug

**Symptom:** Users see each other's cached payment history. Switching between accounts shows old data.

**Hypothesis:** Cache key includes user ID but not org ID, so different orgs see each other's data.

**Injection:** In the cache retrieval function, before returning the cached value:
```python
# Diagnostic: test if cache is the problem
return None  # force cache miss
```

**Run the test:** Reload the app, switch accounts, check history.

**Results:**
- If history is now correct (no shared data) → hypothesis confirmed. Cache key is wrong.
- If history is still wrong → cache is not the problem. Look elsewhere.

**Real fix:** Add org ID to the cache key.

---

### Example 2: Async job doesn't complete

**Symptom:** Job logs "started" but never logs "completed". Async side effects (sending emails, updating records) never happen.

**Hypothesis:** The coroutine is created but never awaited. The function returns before the work happens.

**Injection:** In the job handler, right before the return statement:
```python
# Diagnostic: test if async work is actually happening
# Skip the await to see if work is fire-and-forget or blocking
return  # skip the await, return immediately
```

**Run the test:** Trigger the job, check if emails are sent and records are updated.

**Results:**
- If the job returns instantly and nothing happens → hypothesis confirmed. The `await` was being skipped (or `asyncio.create_task` is missing).
- If the job still takes time even with this return → work is happening elsewhere (async task was created before this function).

**Real fix:** Add `await` or `asyncio.create_task()` to actually wait for the work.

---

### Example 3: Permission check is missing

**Symptom:** Users can delete other users' posts. Authorization should prevent this.

**Hypothesis:** The auth check is missing or it's checking the wrong condition.

**Injection:** Comment out the auth check:
```python
def delete_post(post_id, user):
    post = db.get(post_id)
    # Diagnostic: test if auth check is working
    # if post.owner != user:
    #     raise PermissionError()
    db.delete(post)
```

**Run the test:** Try to delete another user's post.

**Results:**
- If the delete succeeds → auth check was needed. It's missing or the condition is wrong.
- If the delete still fails → auth is checked elsewhere (or the error is coming from a different layer).

**Real fix:** Uncomment and verify the condition is correct.

---

### Example 4: Slow query or computation

**Symptom:** Endpoint takes 30 seconds on a large dataset.

**Hypothesis:** A specific query or computation inside the handler is the bottleneck.

**Injection:** Replace the expensive operation with a mock:
```python
def get_user_stats(user_id):
    # Diagnostic: test if this query is the bottleneck
    # stats = db.query(UserStats).filter(user_id=user_id).all()  # expensive
    stats = []  # mock: no query
    return stats
```

**Run the test:** Time the endpoint with and without the mock.

**Results:**
- If the endpoint is now fast → the query is the bottleneck. Add an index, optimize the query, or cache it.
- If the endpoint is still slow → the bottleneck is elsewhere. Test another mutation.

**Real fix:** Add a database index, restructure the query, or cache the result.

---

### Example 5: Timezone boundary bug

**Symptom:** Transactions are off by one day for some users. The cutoff time is inconsistent.

**Hypothesis:** Timezone conversion is wrong. The app is comparing UTC times with local times without converting.

**Injection:** Use UTC directly, skipping the user's timezone:
```python
def daily_cutoff(transaction_date, user_tz):
    # Diagnostic: test if timezone conversion is the problem
    cutoff_utc = datetime.fromisoformat(transaction_date)  # assume UTC
    # cutoff_utc = convert_to_utc(transaction_date, user_tz)  # convert properly
    return transaction.created_at < cutoff_utc
```

**Run the test:** Check transactions for a user in a different timezone.

**Results:**
- If transactions are now correct → timezone conversion was wrong.
- If transactions are still wrong → the issue is not the timezone conversion.

**Real fix:** Fix the conversion function or the comparison logic.

---

## Mutation discipline

1. **One change per test.** Change one function, one line, one condition at a time. If you change two things, you won't know which one fixed the symptom.

2. **Make the change obvious.** If you're removing a line, comment it out with a `# Diagnostic:` label. If you're injecting early return or exception, add a print statement first so you know the mutation was reached.

3. **Test the test.** Before concluding "the symptom didn't change," verify you actually reached the mutation. Add a `print()` or `raise Exception()` to confirm.

4. **Clean up after.** Delete the worktree and the mutation. Don't leave debug code behind.

5. **The mutation is not the fix.** Forcing a cache miss is not the same as fixing the cache key. A diagnostic mutation isolates the problem; the real fix addresses the root cause.
