# Bug Injection Patterns

## Contents

- [Easy (typos, logic flips, obvious off-by-one)](#easy-typos-logic-flips-obvious-off-by-one)
- [Medium (missing await, stale keys, wrong layer)](#medium-missing-await-stale-keys-wrong-layer)
- [Hard (race conditions, timezone boundaries, cascading logic)](#hard-race-conditions-timezone-boundaries-cascading-logic)
- [Guidelines for injection](#guidelines-for-injection)

## Easy (typos, logic flips, obvious off-by-one)

**Missing not operator:**
```python
# Before
if user.is_active:
    process_payment(user)

# After (bug)
if not user.is_active:
    process_payment(user)
```
Symptom: payments fail for active users only.

**Off-by-one in slice:**
```python
# Before
def get_page(items, page_num, page_size=10):
    start = (page_num - 1) * page_size
    return items[start : start + page_size]

# After (bug)
def get_page(items, page_num, page_size=10):
    start = (page_num - 1) * page_size
    return items[start : start + page_size - 1]  # drops last item
```
Symptom: each page has one fewer item than expected.

**Wrong variable:**
```python
# Before
total = 0
for price, qty in items:
    total += price * qty

# After (bug)
total = 0
for price, qty in items:
    total += qty * qty  # using qty twice
```
Symptom: totals are wrong (squared quantities instead of price × qty).

**Inverted comparison:**
```python
# Before
if timeout_seconds < max_timeout:
    proceed()

# After (bug)
if timeout_seconds > max_timeout:  # inverted
    proceed()
```
Symptom: requests timeout too early or hang.

---

## Medium (missing await, stale keys, wrong layer)

**Missing `await`:**
```python
# Before
async def fetch_user(user_id):
    result = await db.get(user_id)
    return result

# After (bug)
async def fetch_user(user_id):
    result = db.get(user_id)  # missing await
    return result
```
Symptom: returns a coroutine object instead of data; deserialization or attribute access fails.

**Stale cache key:**
```python
# Before
def get_user_settings(user_id, org_id):
    key = f"user:{user_id}:settings"
    cached = cache.get(key)
    if cached:
        return cached
    # ... fetch and cache ...

# After (bug)
def get_user_settings(user_id, org_id):
    key = f"user:{user_id}"  # forgot :settings and :org_id
    cached = cache.get(key)
    if cached:
        return cached
    # ... returns wrong org's settings ...
```
Symptom: wrong settings returned; inconsistent between users/orgs; cache hit when it shouldn't be.

**Missing index:**
```python
# Before (with index)
SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC;

# After (bug)
# Index on user_id is dropped or the query is rewritten
SELECT * FROM transactions WHERE user_id = ? AND status = 'completed' ORDER BY created_at DESC;
# This query now does a table scan instead of index + filter
```
Symptom: slow query, high CPU, timeouts on large tables; fast on small test data.

**Wrong async context:**
```python
# Before
async def process_batch():
    for item in items:
        await handle(item)

# After (bug)
async def process_batch():
    tasks = [handle(item) for item in items]  # creates coroutines but doesn't await
    # ... function returns before any handle() completes
```
Symptom: jobs appear to complete instantly but nothing happens; side effects are missing.

**Skip a required step:**
```python
# Before
def save_user(user_data):
    user = User(**user_data)
    db.add(user)
    db.commit()  # required
    emit_user_created(user.id)
    return user

# After (bug)
def save_user(user_data):
    user = User(**user_data)
    db.add(user)
    # forgot db.commit()
    emit_user_created(user.id)  # emits but user isn't in DB yet
    return user
```
Symptom: events fire but data doesn't persist; rollback or transaction issues.

---

## Hard (race conditions, timezone boundaries, cascading logic)

**Race condition — check-then-act:**
```python
# Before (safe)
def transfer(from_user, to_user, amount):
    with lock:
        balance = from_user.balance
        if balance >= amount:
            from_user.balance -= amount
            to_user.balance += amount
            db.save_both()

# After (bug)
def transfer(from_user, to_user, amount):
    balance = from_user.balance  # check
    if balance >= amount:  # time passes here
        # another thread withdraws; balance is now wrong
        from_user.balance -= amount  # act on stale value
        to_user.balance += amount
        db.save_both()
```
Symptom: duplicate transfers, negative balance, or race-condition errors under load.

**Timezone boundary:**
```python
# Before (correct)
def daily_cutoff(transaction_date, user_tz):
    cutoff_utc = convert_to_utc(transaction_date, user_tz)
    return transaction.created_at < cutoff_utc

# After (bug)
def daily_cutoff(transaction_date, user_tz):
    # forgot to convert user_tz to UTC; comparing different zones
    cutoff_local = datetime.fromisoformat(transaction_date)
    return transaction.created_at < cutoff_local
```
Symptom: off-by-one day; transactions included or excluded based on user's timezone, not actual time.

**Authorization check buried deep:**
```python
# Before
def delete_post(post_id, user):
    post = db.get_post(post_id)
    if post.author_id != user.id:
        raise PermissionError()
    db.delete(post)

# After (bug)
def delete_post(post_id, user):
    post = db.get_post(post_id)
    db.delete(post)  # forgot the permission check
    if post.author_id != user.id:
        raise PermissionError()  # check after delete — too late
```
Symptom: users can delete other people's posts; data loss.

**Cascading side effect:**
```python
# Before (handles cancellation)
def cancel_order(order_id):
    order = db.get_order(order_id)
    for item in order.items:
        inventory.add_back(item)
    refund_payment(order.payment_id)
    order.status = 'cancelled'
    db.save(order)

# After (bug)
def cancel_order(order_id):
    order = db.get_order(order_id)
    order.status = 'cancelled'  # mark cancelled first
    db.save(order)  # now the order is already cancelled
    for item in order.items:  # but item.quantity_reserved refers to old state
        inventory.add_back(item)  # adds back wrong quantities
```
Symptom: inventory is incorrect after cancellation; off-by-one or phantom stock.

**Mutation of shared state:**
```python
# Before
def process_config(config_dict):
    config = config_dict.copy()  # safe copy
    config['debug'] = False
    return apply_config(config)

# After (bug)
def process_config(config_dict):
    config = config_dict  # shared reference, not a copy
    config['debug'] = False  # mutates the original
    return apply_config(config)
```
Symptom: global state is modified; subsequent calls behave unexpectedly; side effects leak.

---

## Guidelines for injection

1. **One bug = one small diff.** Two-line changes are ideal. Never change logic and rename a variable at the same time.
2. **Make the symptom visible without hours of tracing.** Running the test suite, hitting an endpoint, or checking an output should expose the bug within seconds.
3. **Do not make the bug syntactically invalid.** It should parse and run; the bug is in the logic or semantics.
4. **Prefer bugs that tests miss.** Tests that pass are harder to find; they teach the skill better.
5. **Vary the layers.** One frontend bug, one API bug, one database bug teaches more than three API bugs.
6. **Vary the methods to find them.** One requires reading code, one requires running tests, one requires a debugger.
