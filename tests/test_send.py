from __future__ import annotations

from dataclasses import dataclass

import pytest

from mediatorx import (
    IBaseCommand,
    IBaseQuery,
    IBaseRequest,
    ICommand,
    IQuery,
    IRequest,
    Mediator,
)


async def test_send_resolves_handler_and_returns_response(
    mediator: Mediator, ping_cls: type, ping_handler_cls: type
) -> None:
    mediator.register(ping_cls, ping_handler_cls)
    response = await mediator.send(ping_cls("hello"))
    assert response == "pong: hello"


async def test_send_raises_keyerror_for_unregistered(mediator: Mediator) -> None:
    @dataclass
    class Unknown(IRequest[int]):
        pass

    with pytest.raises(KeyError, match="Unknown"):
        await mediator.send(Unknown())


async def test_request_command_query_marker_separation() -> None:
    @dataclass
    class R(IRequest[int]):
        pass

    @dataclass
    class C(ICommand[int]):
        pass

    @dataclass
    class Q(IQuery[int]):
        pass

    r, c, q = R(), C(), Q()
    assert isinstance(r, IBaseRequest) and not isinstance(r, IBaseCommand)
    assert isinstance(c, IBaseCommand) and not isinstance(c, IBaseQuery)
    assert isinstance(q, IBaseQuery) and not isinstance(q, IBaseRequest)
