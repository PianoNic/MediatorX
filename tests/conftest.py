from __future__ import annotations

from dataclasses import dataclass

import pytest

from mediatorx import IRequest, Mediator


@dataclass
class Ping(IRequest[str]):
    """Ping fixture request."""

    message: str = "hi"


class PingHandler:
    """Ping fixture handler."""

    async def handle(self, request: Ping) -> str:
        return f"pong: {request.message}"


@pytest.fixture
def mediator() -> Mediator:
    """Return a fresh Mediator for each test."""
    return Mediator()


@pytest.fixture
def ping_cls() -> type[Ping]:
    """Expose the Ping class."""
    return Ping


@pytest.fixture
def ping_handler_cls() -> type[PingHandler]:
    """Expose the PingHandler class."""
    return PingHandler
