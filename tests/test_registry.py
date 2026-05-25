from __future__ import annotations

from dataclasses import dataclass

from mediatorx import INotification, IRequest, Mediator, Registry


@dataclass
class Hello(IRequest[str]):
    name: str = "world"


@dataclass(frozen=True)
class Joined(INotification):
    who: str = "alice"


async def test_decorator_registration_wires_handler() -> None:
    reg = Registry()

    @reg.handler(Hello)
    class HelloHandler:
        async def handle(self, h: Hello) -> str:
            return f"hi {h.name}"

    m = Mediator()
    reg.apply_to(m)
    assert await m.send(Hello("nic")) == "hi nic"


async def test_multiple_notification_handlers_per_type() -> None:
    reg = Registry()
    seen: list[str] = []

    @reg.notification(Joined)
    class A:
        async def handle(self, n: Joined) -> None:
            seen.append(f"a:{n.who}")

    @reg.notification(Joined)
    class B:
        async def handle(self, n: Joined) -> None:
            seen.append(f"b:{n.who}")

    m = Mediator()
    reg.apply_to(m)
    await m.publish(Joined("nic"))
    assert sorted(seen) == ["a:nic", "b:nic"]


async def test_two_registries_are_independent() -> None:
    r1, r2 = Registry(), Registry()

    @r1.handler(Hello)
    class H1:
        async def handle(self, h: Hello) -> str:
            return "from-r1"

    @r2.handler(Hello)
    class H2:
        async def handle(self, h: Hello) -> str:
            return "from-r2"

    m1, m2 = Mediator(), Mediator()
    r1.apply_to(m1)
    r2.apply_to(m2)
    assert await m1.send(Hello()) == "from-r1"
    assert await m2.send(Hello()) == "from-r2"
