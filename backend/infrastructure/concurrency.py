"""Process-wide concurrency primitives.

`executor` is the single ThreadPoolExecutor every component uses to wrap
blocking vnstock calls. `CONCURRENCY` caps how many in-flight per-symbol
async tasks any orchestrator (market scan, Layer 2 scoring) runs at once.

Keeping these here — instead of as module-level globals on a feature module —
makes the dependency explicit and prevents the "first import wins" footgun.
"""

from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=30)
CONCURRENCY = 10
