"""Immutable storage contract and thread-safe in-memory test adapter."""
from dataclasses import dataclass
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class Receipt:
    event_id: str
    accepted_at_ms: int
    status: str = 'accepted'


@dataclass(frozen=True)
class Event:
    pk: str
    sk: str
    profile: str
    request_digest: str
    wrapper_bytes: bytes
    principal_ref: str
    binding_version: str
    receipt: Receipt


class StoreUnavailable(Exception):
    """Includes uncertain commit outcomes. Caller may retry the same request."""


class EventStore(Protocol):
    def insert_if_absent(self, event: Event) -> bool:
        """Atomically insert immutable event; False ONLY for existing key.

        Never overwrite. Raise StoreUnavailable on failure/unknown outcome.
        """
        ...

    def get(self, pk: str, sk: str) -> Event | None:
        """Strongly consistent read, or StoreUnavailable. Never delete records."""
        ...


class MemoryStore:
    """Single-process only; no durability or DynamoDB concurrency claim."""
    def __init__(self):
        self._rows = {}
        self._lock = Lock()

    def insert_if_absent(self, event):
        with self._lock:
            key = event.pk, event.sk
            if key in self._rows:
                return False
            self._rows[key] = event
            return True

    def get(self, pk, sk):
        with self._lock:
            return self._rows.get((pk, sk))
