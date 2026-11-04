"""
In-memory session storage with idle expiry.

`ExpiringDict` behaves like a dict (tests and callers index it directly), but
entries not read or written for `ttl_seconds` are dropped on the next write.
This bounds memory: uploaded reference corpora and BM25 indexes used to stay
in memory for the lifetime of the process.
"""
import threading
import time
from collections.abc import MutableMapping


class ExpiringDict(MutableMapping):
    def __init__(self, ttl_seconds: float, clock=time.monotonic):
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._data = {}
        self._touched = {}
        self._lock = threading.RLock()

    def _touch(self, key):
        self._touched[key] = self._clock()

    def purge_expired(self) -> list:
        """Drop entries idle for longer than the TTL; returns the removed keys."""
        if not self.ttl_seconds or self.ttl_seconds <= 0:
            return []
        with self._lock:
            cutoff = self._clock() - self.ttl_seconds
            expired = [k for k, t in self._touched.items() if t < cutoff]
            for k in expired:
                self._data.pop(k, None)
                self._touched.pop(k, None)
            return expired

    def __getitem__(self, key):
        with self._lock:
            value = self._data[key]
            self._touch(key)
            return value

    def __setitem__(self, key, value):
        with self._lock:
            self.purge_expired()
            self._data[key] = value
            self._touch(key)

    def __delitem__(self, key):
        with self._lock:
            del self._data[key]
            self._touched.pop(key, None)

    def __iter__(self):
        return iter(list(self._data))

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data
