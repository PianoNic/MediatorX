from __future__ import annotations


class IMessage:
    """Root marker for everything that goes through send()/create_stream()."""


class IStreamMessage:
    """Marker for messages that produce a stream of responses."""


class IBaseRequest(IMessage):
    """Marker for request-style messages (CQRS-neutral)."""


class IBaseCommand(IMessage):
    """Marker for command-style messages (writes / state changes)."""


class IBaseQuery(IMessage):
    """Marker for query-style messages (reads, must return data)."""


class INotification:
    """Marker for fire-and-forget pub/sub messages."""
