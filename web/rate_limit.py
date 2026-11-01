"""Lightweight in-process rate limiter for public endpoints.

Pure-stdlib sliding-window counter, thread-safe. No external dependency
(flask-limiter is not installed in this environment). Designed to harden
the public booking endpoint against abuse without affecting internal auth.
"""

import time
import threading
from collections import defaultdict
from functools import wraps

from flask import jsonify, request


class RateLimiter:
    """Sliding-window rate limiter keyed by (endpoint, client ip)."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> list of request timestamps
        self._hits = defaultdict(list)

    def _prune(self, key, window, now):
        bucket = self._hits[key]
        cutoff = now - window
        # drop entries older than the window
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        return len(bucket)

    def allow(self, key, limit, window):
        """Return True if request is allowed, False if over limit."""
        now = time.monotonic()
        with self._lock:
            count = self._prune(key, window, now)
            if count >= limit:
                return False
            self._hits[key].append(now)
            return True

    def decorator(self, limit=5, window=60, key_func=None):
        """Decorator factory. limit requests per window seconds per key."""
        def dec(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if key_func is not None:
                    k = key_func()
                else:
                    k = f"{request.endpoint}:{request.remote_addr or 'anon'}"
                if not self.allow(k, limit, window):
                    return jsonify({
                        "success": False,
                        "error": "Too many requests. Please wait a minute and try again.",
                    }), 429
                return fn(*args, **kwargs)
            return wrapped
        return dec


# Shared instance
booking_limiter = RateLimiter()