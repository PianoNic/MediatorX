from __future__ import annotations

from dataclasses import dataclass

from mediatorx import (
    DictResolver,
    IBaseCommand,
    ICommand,
    IQuery,
    Mediator,
    MessageExceptionHandler,
    MessagePostProcessor,
    MessagePreProcessor,
)


@dataclass
class Cmd(ICommand[str]):
    val: str = "x"


@dataclass
class Qry(IQuery[str]):
    val: str = "y"


class CmdHandler:
    async def handle(self, c: Cmd) -> str:
        return f"handled:{c.val}"


class QryHandler:
    async def handle(self, q: Qry) -> str:
        return f"answered:{q.val}"


async def test_behaviors_compose_outermost_first() -> None:
    trace: list[str] = []

    class Outer:
        async def handle(self, m: object, next: object) -> object:
            trace.append("outer-pre")
            r = await next()  # type: ignore[operator]
            trace.append("outer-post")
            return r

    class Inner:
        async def handle(self, m: object, next: object) -> object:
            trace.append("inner-pre")
            r = await next()  # type: ignore[operator]
            trace.append("inner-post")
            return r

    m = Mediator()
    m.register(Cmd, CmdHandler)
    m.add_behavior(Outer)
    m.add_behavior(Inner)
    await m.send(Cmd("a"))
    assert trace == ["outer-pre", "inner-pre", "inner-post", "outer-post"]


async def test_behavior_can_short_circuit() -> None:
    class ShortCircuit:
        async def handle(self, m: object, next: object) -> object:
            return "short"

    med = Mediator()
    med.register(Cmd, CmdHandler)
    med.add_behavior(ShortCircuit)
    assert await med.send(Cmd("a")) == "short"


async def test_behavior_can_transform_response() -> None:
    class Upper:
        async def handle(self, m: object, next: object) -> object:
            r = await next()  # type: ignore[operator]
            return str(r).upper()

    med = Mediator()
    med.register(Cmd, CmdHandler)
    med.add_behavior(Upper)
    assert await med.send(Cmd("a")) == "HANDLED:A"


async def test_constraint_filtering_skips_non_matching_message() -> None:
    fired: list[str] = []

    class CommandOnly:
        async def handle(self, m: object, next: object) -> object:
            fired.append(type(m).__name__)
            return await next()  # type: ignore[operator]

    med = Mediator()
    med.register(Cmd, CmdHandler)
    med.register(Qry, QryHandler)
    med.add_behavior(CommandOnly, constraint=IBaseCommand)

    await med.send(Cmd())
    await med.send(Qry())
    assert fired == ["Cmd"]


async def test_pre_post_processor_subclasses_work_as_behaviors() -> None:
    pre_calls: list[object] = []
    post_calls: list[tuple[object, object]] = []

    class Pre(MessagePreProcessor[Cmd, str]):
        async def handle(self, message: Cmd) -> None:
            pre_calls.append(message.val)

    class Post(MessagePostProcessor[Cmd, str]):
        async def handle(self, message: Cmd, response: str) -> None:
            post_calls.append((message.val, response))

    class PreAdapter:
        def __init__(self, pre: Pre) -> None:
            self.pre = pre

        async def handle(self, m: Cmd, next: object) -> object:
            await self.pre.handle(m)
            return await next()  # type: ignore[operator]

    class PostAdapter:
        def __init__(self, post: Post) -> None:
            self.post = post

        async def handle(self, m: Cmd, next: object) -> object:
            r = await next()  # type: ignore[operator]
            await self.post.handle(m, r)  # type: ignore[arg-type]
            return r

    pre, post = Pre(), Post()
    pre_a, post_a = PreAdapter(pre), PostAdapter(post)
    resolver = (
        DictResolver()
        .add_instance(CmdHandler, CmdHandler())
        .add_instance(PreAdapter, pre_a)
        .add_instance(PostAdapter, post_a)
    )
    med = Mediator(resolver=resolver)
    med.register(Cmd, CmdHandler)
    med.add_behavior(PreAdapter)
    med.add_behavior(PostAdapter)

    await med.send(Cmd("z"))
    assert pre_calls == ["z"]
    assert post_calls == [("z", "handled:z")]


async def test_exception_handler_base_class_is_subclassable() -> None:
    class Boom(RuntimeError):
        pass

    class Recover(MessageExceptionHandler[Cmd, str, Boom]):
        async def handle(self, message: Cmd, exception: Boom):
            return self.Handled("recovered")

    r = Recover()
    result = await r.handle(Cmd("x"), Boom("fail"))
    assert result.handled is True
    assert result.response == "recovered"
    assert r.NotHandled.handled is False
