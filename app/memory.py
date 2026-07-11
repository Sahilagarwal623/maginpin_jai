"""
In-memory context store.

Stores all context objects pushed via /v1/context and conversation state
for /v1/reply. Thread-safe for single-process uvicorn (no async writes
from multiple workers).

Design decisions:
  - Pure dict storage — no external dependencies, fast for the 255-context
    base dataset the judge pushes.
  - Version-gated idempotent writes — higher version replaces lower version
    atomically; same or lower version is rejected with 409.
  - Conversation history is append-only; each conversation_id gets a list
    of turns.
"""

from __future__ import annotations

from typing import Any, Optional


class Memory:
    """Stateful in-memory store for contexts and conversations."""

    def __init__(self) -> None:
        # (scope, context_id) -> {version: int, payload: dict}
        self._contexts: dict[tuple[str, str], dict[str, Any]] = {}
        # conversation_id -> list of turn dicts
        self._conversations: dict[str, list[dict[str, Any]]] = {}
        # suppression_key -> bool (tracks already-sent recommendations)
        self._suppressed: set[str] = set()

    # ── context CRUD ──────────────────────────────────────────

    def get_context(self, scope: str, context_id: str) -> Optional[dict[str, Any]]:
        """Return the payload for a stored context, or None."""
        entry = self._contexts.get((scope, context_id))
        return entry["payload"] if entry else None

    def get_context_version(self, scope: str, context_id: str) -> Optional[int]:
        entry = self._contexts.get((scope, context_id))
        return entry["version"] if entry else None

    def store_context(
        self, scope: str, context_id: str, version: int, payload: dict[str, Any]
    ) -> tuple[bool, Optional[int]]:
        """
        Store or update a context.
        Returns (accepted, current_version).
        If the incoming version <= existing version, returns (False, current_version).
        """
        key = (scope, context_id)
        existing = self._contexts.get(key)
        if existing and existing["version"] >= version:
            return False, existing["version"]
        self._contexts[key] = {"version": version, "payload": payload}
        return True, version

    def count_by_scope(self) -> dict[str, int]:
        """Return counts of stored contexts grouped by scope."""
        counts: dict[str, int] = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
        for (scope, _), _ in self._contexts.items():
            counts[scope] = counts.get(scope, 0) + 1
        return counts

    def all_contexts_by_scope(self, scope: str) -> list[dict[str, Any]]:
        """Return all payloads for a given scope."""
        results = []
        for (s, _), entry in sorted(self._contexts.items()):
            if s == scope:
                results.append(entry["payload"])
        return results

    def get_all_trigger_ids(self) -> list[str]:
        """Return all stored trigger context_ids, sorted for determinism."""
        return sorted(
            cid for (scope, cid), _ in self._contexts.items() if scope == "trigger"
        )

    # ── conversation state ────────────────────────────────────

    def get_conversation(self, conversation_id: str) -> list[dict[str, Any]]:
        return self._conversations.get(conversation_id, [])

    def append_turn(self, conversation_id: str, turn: dict[str, Any]) -> None:
        self._conversations.setdefault(conversation_id, []).append(turn)

    def conversation_exists(self, conversation_id: str) -> bool:
        return conversation_id in self._conversations

    # ── suppression ───────────────────────────────────────────

    def is_suppressed(self, key: str) -> bool:
        return key in self._suppressed

    def suppress(self, key: str) -> None:
        self._suppressed.add(key)

    def clear_all(self) -> None:
        """Wipe everything — called on teardown."""
        self._contexts.clear()
        self._conversations.clear()
        self._suppressed.clear()
