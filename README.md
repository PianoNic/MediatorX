# mediatorx

> CQRS-style mediator and pipeline for Python — designed for clean / onion architecture. Inspired by [MediatR](https://github.com/LuckyPennySoftware/MediatR) and interface-compatible with [martinothamar/Mediator](https://github.com/martinothamar/Mediator) for .NET.

[![PyPI version](https://img.shields.io/pypi/v/mediatorx.svg)](https://pypi.org/project/mediatorx/)
[![Python versions](https://img.shields.io/pypi/pyversions/mediatorx.svg)](https://pypi.org/project/mediatorx/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`mediatorx` brings the `IRequest` / `ICommand` / `IQuery` / `INotification` mediator pattern from .NET to Python, without runtime reflection magic, code generation, or scary metaclasses. Just protocols, async, and an explicit composition root.

If you've used MediatR or martinothamar's Mediator in C# and want the same shape in your FastAPI / clean architecture Python project, this is for you.

---

## Why another mediator library?

If you're coming from .NET, you've almost certainly used [MediatR](https://github.com/LuckyPennySoftware/MediatR) — the de facto mediator pattern library for ASP.NET Core / clean architecture projects. `mediatorx` exists because the equivalent Python ecosystem is thin: most packages (`mediatr`, `diator`, `mediatpy`, `python-mediator`) are abandoned, and the handful that are maintained either ship too much (Kafka, outbox, brokers) or too little (no streaming, no command/query separation, no pipeline pre/post split).

`mediatorx` aims for one thing: **mirror the MediatR interface contracts in idiomatic async Python** — specifically following the cleaner taxonomy from [martinothamar/Mediator](https://github.com/martinothamar/Mediator) (`IRequest` / `ICommand` / `IQuery` separation, stream variants, pre/post/exception processors). No more, no less.

- ✅ `IRequest<T>`, `ICommand<T>`, `IQuery<T>` — semantic CQRS separation
- ✅ Streaming variants (`IStreamRequest`, `IStreamCommand`, `IStreamQuery`) via `AsyncIterator`
- ✅ Notifications (pub/sub) with pluggable publishers (`ForeachAwait`, `TaskWhenAll`)
- ✅ Pipeline behaviors with `IPipelineBehavior`, plus split `PreProcessor` / `PostProcessor` / `ExceptionHandler` base classes
- ✅ Marker-interface constraints (`where TMessage : ICommand` equivalent)
- ✅ Async-first — no sync/async dual path, no `asyncio.run` hacks
- ❌ No runtime reflection, no source generation, no assembly scanning
- ❌ No broker integration — bring your own; this is in-process

---

## Installation

```bash
pip install mediatorx
# or
uv add mediatorx
```

Requires Python 3.11+.

---

## Quickstart

```python
import asyncio
from dataclasses import dataclass
from mediatorx import IRequest, IRequestHandler, Mediator

@dataclass
class Ping(IRequest[str]):
    message: str

class PingHandler(IRequestHandler[Ping, str]):
    async def handle(self, request: Ping) -> str:
        return f"pong: {request.message}"

async def main():
    mediator = Mediator()
    mediator.register(Ping, PingHandler())

    response = await mediator.send(Ping("hello"))
    print(response)  # "pong: hello"

asyncio.run(main())
```

---

## Core concepts

### Messages — Request, Command, Query

Three semantically distinct message kinds with identical mechanics. Pick the one that matches your CQRS intent; pipeline behaviors can be constrained by marker:

```python
from mediatorx import IRequest, ICommand, IQuery

@dataclass
class GetUserById(IQuery[User]):       # read — must return data
    user_id: int

@dataclass
class CreateBooking(ICommand[int]):    # write — returns booking id
    user_id: int
    room_id: int

@dataclass
class SendWelcomeEmail(ICommand[None]):  # write — no meaningful return
    user_id: int
```

### Handlers

One handler per message type. Constructor-injected dependencies — works with any DI container:

```python
from mediatorx import IQueryHandler

class GetUserByIdHandler(IQueryHandler[GetUserById, User]):
    def __init__(self, repo: IUserRepository):
        self._repo = repo

    async def handle(self, query: GetUserById) -> User:
        return await self._repo.get(query.user_id)
```

### Pipeline behaviors

Wrap every handler in cross-cutting concerns (logging, validation, transactions) without touching the handler itself:

```python
from mediatorx import IPipelineBehavior, MessageHandlerDelegate

class LoggingBehavior(IPipelineBehavior[IMessage, TResponse]):
    def __init__(self, logger: Logger):
        self._logger = logger

    async def handle(
        self,
        message: IMessage,
        next: MessageHandlerDelegate[TResponse],
    ) -> TResponse:
        self._logger.info(f"handling {type(message).__name__}")
        try:
            response = await next()
            self._logger.info(f"handled {type(message).__name__}")
            return response
        except Exception:
            self._logger.exception(f"failed {type(message).__name__}")
            raise
```

For simple cases, use split pre/post/exception processors instead of the omnibus middleware shape:

```python
from mediatorx import MessagePreProcessor, MessageExceptionHandler

class ValidationProcessor(MessagePreProcessor[IValidate, TResponse]):
    async def handle(self, message: IValidate) -> None:
        message.validate()  # raises on invalid input

class RetryableErrorHandler(MessageExceptionHandler[IMessage, TResponse, TransientError]):
    async def handle(self, message, exc):
        return self.NotHandled  # let it bubble; record metric elsewhere
```

### Constraining behaviors to a subset of messages

Use the marker hierarchy (`IMessage`, `IBaseCommand`, `IBaseQuery`) to scope behaviors. A behavior bound to `ICommand` only fires for commands, not queries — exactly like the C# `where TMessage : ICommand` constraint:

```python
class TransactionBehavior(IPipelineBehavior[IBaseCommand, TResponse]):
    """Wraps commands in a DB transaction. Queries skip this entirely."""
    ...
```

### Notifications (pub/sub)

```python
from mediatorx import INotification, INotificationHandler

@dataclass(frozen=True)
class UserRegistered(INotification):
    user_id: int

class SendWelcomeEmailOnRegister(INotificationHandler[UserRegistered]):
    async def handle(self, n: UserRegistered) -> None: ...

class LogRegistrationOnRegister(INotificationHandler[UserRegistered]):
    async def handle(self, n: UserRegistered) -> None: ...

# Both handlers run on every publish
await mediator.publish(UserRegistered(user_id=42))
```

Pick a publisher strategy at construction:

```python
from mediatorx import Mediator, ForeachAwaitPublisher, TaskWhenAllPublisher

mediator = Mediator(publisher=TaskWhenAllPublisher())  # parallel
# or
mediator = Mediator(publisher=ForeachAwaitPublisher())  # sequential, default
```

### Streaming

```python
from mediatorx import IStreamRequest, IStreamRequestHandler
from typing import AsyncIterator

@dataclass
class TailLogs(IStreamRequest[LogLine]):
    service: str

class TailLogsHandler(IStreamRequestHandler[TailLogs, LogLine]):
    async def handle(self, request: TailLogs) -> AsyncIterator[LogLine]:
        async for line in log_source(request.service):
            yield line

async for line in mediator.create_stream(TailLogs("api")):
    print(line)
```

---

## Clean architecture with FastAPI

`mediatorx` is designed to live in your application layer. Endpoints become two-liners that hand a DTO to the mediator and return the response:

```
src/myapp/
├── domain/              # entities, value objects, repository interfaces
├── application/         # commands, queries, handlers, behaviors  ← uses mediatorx
├── infrastructure/      # repository impls, db, external services
└── api/                 # FastAPI routes (composition root)
```

```python
# api/bookings.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/bookings")
async def create_booking(
    body: CreateBookingDto,
    mediator: Mediator = Depends(get_mediator),
) -> BookingResponse:
    booking_id = await mediator.send(CreateBookingCommand(**body.dict()))
    return BookingResponse(id=booking_id)
```

Wire handlers and behaviors in your composition root (typically `main.py` or a `container.py`):

```python
def build_mediator(container: Container) -> Mediator:
    m = Mediator()

    # Behaviors run outermost-first
    m.add_behavior(LoggingBehavior(container.logger()))
    m.add_behavior(TransactionBehavior(container.uow()))
    m.add_behavior(ValidationProcessor())

    # Handlers
    m.register(CreateBookingCommand, CreateBookingHandler(container.booking_repo()))
    m.register(GetUserById, GetUserByIdHandler(container.user_repo()))

    return m
```

---

## Comparison to .NET libraries

| Feature | MediatR | Mediator (martinothamar) | **mediatorx** |
|---|---|---|---|
| `IRequest<T>` / `IRequestHandler<,>` | ✅ | ✅ | ✅ |
| Command / Query separation | ❌ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ✅ |
| Pipeline behaviors | ✅ | ✅ | ✅ |
| Pre/Post/Exception processors | ✅ | ✅ | ✅ |
| Compile-time handler validation | ❌ | ✅ (source gen) | ❌ (runtime) |
| Native AOT / no reflection | ❌ | ✅ | N/A (Python) |
| Async-only | ❌ | ❌ | ✅ |

---

## Status

Early. The interface surface is stable and mirrors Mediator.Abstractions; expect the concrete `Mediator` implementation and DI integration helpers to evolve. Pinning a minor version is recommended.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Acknowledgements

- [Jimmy Bogard](https://github.com/jbogard) for [MediatR](https://github.com/LuckyPennySoftware/MediatR), which started all of this.
- [Martin Othamar](https://github.com/martinothamar) for [Mediator](https://github.com/martinothamar/Mediator), whose interface taxonomy this library mirrors.