from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest

from mediatorx import IStreamRequest, Mediator


@dataclass
class Counts(IStreamRequest[int]):
    n: int = 3


class CountsHandler:
    async def handle(self, req: Counts) -> AsyncIterator[int]:
        for i in range(req.n):
            yield i


async def test_stream_handler_yields_all_items() -> None:
    m = Mediator()
    m.register(Counts, CountsHandler)
    result = [item async for item in m.create_stream(Counts(4))]
    assert result == [0, 1, 2, 3]


async def test_stream_pipeline_behavior_can_wrap_iteration() -> None:
    class Double:
        async def handle(self, msg: object, next: object) -> AsyncIterator[int]:
            async for item in next():  # type: ignore[attr-defined]
                yield item * 2

    m = Mediator()
    m.register(Counts, CountsHandler)
    m.add_stream_behavior(Double)
    result = [item async for item in m.create_stream(Counts(3))]
    assert result == [0, 2, 4]


async def test_stream_raises_keyerror_for_unregistered() -> None:
    @dataclass
    class Missing(IStreamRequest[int]):
        pass

    m = Mediator()
    with pytest.raises(KeyError, match="Missing"):
        async for _ in m.create_stream(Missing()):
            pass
