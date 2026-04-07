---
name: optimize-rate-limit
description: Optimize code that calls external APIs under a rate limit — fix concurrency bugs, remove throughput bottlenecks, reduce wasted calls, and maximize effective request-per-minute utilization. Use this skill whenever the user mentions rate limiting, API throttling, request-per-minute caps, 429 errors, slow API pipelines, or asks to speed up code that talks to an external service with usage limits. Also trigger when reviewing code that contains sliding-window limiters, semaphores paired with API calls, or fixed `sleep()` delays between requests.
---

# Optimize Rate-Limited API Code

This skill helps audit and refactor code that calls external APIs under a rate limit (requests per minute, per second, etc.). The goal is to maximize effective throughput without exceeding the limit.

## Workflow

1. Read the target file(s) the user provides.
2. Identify which anti-patterns from the checklist below are present.
3. Calculate the current effective throughput (requests/min) and explain why it's lower than the cap.
4. Apply the relevant fixes.
5. Report the new theoretical throughput and explain the improvement.

---

## Anti-Pattern Checklist

### 1. Holding a lock while sleeping

This is the single most common rate-limiter bug. When a thread sleeps inside a locked section, every other thread queues behind it — turning a concurrent system into a sequential one.

**Symptoms:** throughput is ~1 req/sec regardless of concurrency settings; CPU is idle; thread dump shows all workers blocked on the same lock.

**Bad** — serialises all threads behind one sleeper:

```python
def acquire(self):
    with self._lock:
        # ...
        time.sleep(wait)            # every other thread blocks here
        self._timestamps.append(time.monotonic())
```

**Good** — release lock, sleep, then retry:

```python
def acquire(self):
    while True:
        with self._lock:
            now = time.monotonic()
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()
            if len(self._timestamps) < self._limit:
                self._timestamps.append(time.monotonic())
                return                          # got a slot, leave immediately
            sleep_for = self._window - (now - self._timestamps[0]) + 0.05
        time.sleep(max(sleep_for, 0))           # sleep OUTSIDE the lock
```

The key insight: compute how long to wait while holding the lock, but do the actual sleeping after releasing it. This lets other threads check and potentially claim slots in the meantime.

---

### 2. Rate logic in the wrong layer

Rate limiting belongs at the **provider layer** — the thin wrapper where HTTP calls actually happen. When callers also sprinkle `asyncio.sleep()` or `time.sleep()` delays, you get two competing throttles fighting each other, and the effective rate is always worse than either one alone.

**What to do:**

- Put one authoritative rate limiter at the point where requests leave the process.
- Remove all fixed `sleep()` calls from orchestration / repository / caller layers.
- Let the caller control **concurrency** (via a semaphore) but not **rate**.

---

### 3. Fixed delays instead of rate-budget awareness

A fixed `sleep(1)` between calls caps throughput at 60 req/min — even if the API allows 300. It also wastes budget when calls are fast and provides no backpressure when calls are slow.

**Bad:**

```python
await asyncio.sleep(1)  # fixed 1s gap regardless of load
```

**Good:**

```python
limiter.acquire()  # returns instantly if budget available, blocks only when exhausted
```

A sliding-window or token-bucket limiter adapts naturally: when the API is fast, calls fire as quickly as the budget allows; when the budget is exhausted, only then does it block.

---

### 4. No two-phase fetch to skip wasted calls

When processing each item requires N sequential API calls, but an early call can disqualify the item, doing all N calls unconditionally wastes budget on items that will be discarded.

**Strategy:**

- **Phase 1:** Make the cheap / filtering call for all items concurrently.
- **Filter:** Drop items that fail the criteria.
- **Phase 2:** Make the remaining expensive calls only for survivors.

Depending on filter selectivity this can cut total API calls by 30–60%, which directly translates to faster wall-clock time under a fixed rate cap.

---

### 5. Concurrency mis-sized for the rate budget

The right concurrency level depends on both the rate cap and the average call latency:

```
max_concurrent ≈ (rate_limit_per_minute / 60) × avg_latency_seconds
```

| Problem                   | Symptom                                                             |
| ------------------------- | ------------------------------------------------------------------- |
| `max_concurrent` too low  | Threads idle, rate budget underused                                 |
| `max_concurrent` too high | Thread-pool thrashing, context-switch overhead, no extra throughput |

Rules of thumb:

- Thread pool `max_workers` should be ≥ `max_concurrent` (typically 2–3×).
- Target ~95% of the actual API cap as a safety margin to avoid 429s.

---

### 6. Missing async-to-sync bridge

When the orchestration layer is async but the API client is synchronous, you need both a thread pool and an async semaphore working together:

```python
_executor = ThreadPoolExecutor(max_workers=40)
_sem = asyncio.Semaphore(15)

async def call_api(payload):
    async with _sem:                                          # limit concurrency
        return await loop.run_in_executor(_executor, sync_api_fn, payload)
```

The semaphore caps in-flight work; the executor provides real threads for blocking I/O. Without the semaphore, all 40 threads fire at once and blow past the rate limit. Without enough executor threads, the semaphore's slots go unused.

---

## Throughput Reporting Template

After applying fixes, summarise the improvement like this:

```
Before:  ~12 req/min  (lock held during sleep → effectively serial)
After:   ~285 req/min (sliding-window limiter, 15 concurrent workers, 2-phase fetch)
API cap: 300 req/min  (operating at 95% utilisation)
```

Include the specific bottleneck(s) that were removed and why the new number is what it is.
