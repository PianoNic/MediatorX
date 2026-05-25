from __future__ import annotations

import pytest

from mediatorx import DictResolver, Mediator


class Service:
    def __init__(self, value: int = 0) -> None:
        self.value = value


def test_add_instance_returns_same_object() -> None:
    s = Service(99)
    r = DictResolver().add_instance(Service, s)
    assert r.resolve(Service) is s


def test_add_factory_invoked_each_time() -> None:
    calls = {"n": 0}

    def make() -> Service:
        calls["n"] += 1
        return Service(calls["n"])

    r = DictResolver().add_factory(Service, make)
    a = r.resolve(Service)
    b = r.resolve(Service)
    assert a.value == 1 and b.value == 2
    assert a is not b


def test_zero_arg_constructor_fallback() -> None:
    r = DictResolver()
    assert isinstance(r.resolve(Service), Service)


def test_unresolvable_type_raises_informative_keyerror() -> None:
    class NeedsArg:
        def __init__(self, x: int) -> None:
            self.x = x

    r = DictResolver()
    with pytest.raises(KeyError, match="NeedsArg"):
        r.resolve(NeedsArg)


async def test_custom_resolver_can_be_plugged_in() -> None:
    from dataclasses import dataclass

    from mediatorx import IRequest

    @dataclass
    class Q(IRequest[str]):
        pass

    class QHandler:
        async def handle(self, q: Q) -> str:
            return "ok"

    sentinel = QHandler()

    class Custom:
        def resolve(self, t: type) -> object:
            assert t is QHandler
            return sentinel

    med = Mediator(resolver=Custom())
    med.register(Q, QHandler)
    assert await med.send(Q()) == "ok"
