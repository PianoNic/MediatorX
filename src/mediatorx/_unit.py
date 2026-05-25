from __future__ import annotations

from typing import ClassVar


class Unit:
    """Singleton return type for messages that don't produce a meaningful response."""

    _instance: ClassVar[Unit | None] = None

    def __new__(cls) -> Unit:
        """Return the cached singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        """Return a stable repr for logging."""
        return "Unit"


UNIT = Unit()
