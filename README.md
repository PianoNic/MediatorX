# <p align="center">MediatorX</p>
<p align="center">
  <img src="./assets/logo.svg" width="160" alt="MediatorX Logo">
</p>
<p align="center">
  <strong>CQRS-style mediator and pipeline for Python - designed for clean / onion architecture.</strong><br>
  Inspired by <a href="https://github.com/LuckyPennySoftware/MediatR">MediatR</a> and interface-compatible with <a href="https://github.com/martinothamar/Mediator">martinothamar/Mediator</a> for .NET.
</p>
<p align="center">
  <a href="https://github.com/PianoNic/MediatorX"><img src="https://badgetrack.pianonic.ch/badge?tag=mediatorx&label=visits&color=4338ca&style=flat" alt="visits"/></a>
  <a href="https://pypi.org/project/mediatorx/"><img src="https://img.shields.io/pypi/v/mediatorx?color=4338ca&label=PyPI" alt="PyPI version"/></a>
  <a href="https://pypi.org/project/mediatorx/"><img src="https://img.shields.io/pypi/pyversions/mediatorx?color=4338ca" alt="Python versions"/></a>
  <a href="https://github.com/PianoNic/MediatorX/blob/main/LICENSE"><img src="https://img.shields.io/github/license/PianoNic/MediatorX?color=4338ca" alt="license"/></a>
  <a href="https://github.com/PianoNic/MediatorX/releases"><img src="https://img.shields.io/github/v/release/PianoNic/MediatorX?include_prereleases&color=4338ca&label=Latest%20Release" alt="latest release"/></a>
</p>

> [!NOTE]
> Early-stage release. The public interface mirrors `Mediator.Abstractions` and is stable; the concrete `Mediator` implementation and DI helpers will still evolve. Pin a minor version.

## ⚙️ About The Project

`mediatorx` brings the `IRequest` / `ICommand` / `IQuery` / `INotification` mediator pattern from .NET to Python - without runtime reflection magic, code generation, or scary metaclasses. Just protocols, async, and an explicit composition root.

The Python ecosystem is thin here: most existing packages (`mediatr`, `diator`, `mediatpy`, `python-mediator`) are abandoned, and the maintained ones either ship too much (Kafka, outbox, brokers) or too little (no streaming, no command/query separation, no pipeline pre/post split). `mediatorx` aims for one thing: **mirror the MediatR interface contracts in idiomatic async Python**, following the cleaner taxonomy from [martinothamar/Mediator](https://github.com/martinothamar/Mediator) - `IRequest` / `ICommand` / `IQuery` separation, stream variants, pre/post/exception processors. No more, no less.

If you've used MediatR or martinothamar's Mediator in C# and want the same shape in your FastAPI / clean architecture Python project, this is for you.

## ✨ Features

- **CQRS separation** - `IRequest<T>`, `ICommand<T>`, `IQuery<T>` with marker-interface constraints (`where TMessage : ICommand` equivalent)
- **Streaming** - `IStreamRequest`, `IStreamCommand`, `IStreamQuery` via `AsyncIterator`
- **Notifications (pub/sub)** - pluggable publishers (`ForeachAwait`, `TaskWhenAll`)
- **Pipeline behaviors** - `IPipelineBehavior` plus split `PreProcessor` / `PostProcessor` / `ExceptionHandler` base classes
- **Async-first** - no sync/async dual path, no `asyncio.run` hacks
- **Typed** - ships with `py.typed`, mypy-strict friendly
- **Zero runtime deps** - no broker integration, no reflection, no source generation; in-process only

## 📦 Installation

```bash
pip install mediatorx
# or
uv add mediatorx
```

Requires Python 3.11+.

## 🚀 Quickstart

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
    mediator.register(Ping, PingHandler)

    response = await mediator.send(Ping("hello"))
    print(response)  # "pong: hello"

asyncio.run(main())
```

## 🧠 Core Concepts

### Messages - Request, Command, Query

Three semantically distinct message kinds with identical mechanics. Pick the one that matches your CQRS intent; pipeline behaviors can be constrained by marker:

```python
from mediatorx import IRequest, ICommand, IQuery

@dataclass
class GetUserById(IQuery[User]):       # read - must return data
    user_id: int

@dataclass
class CreateBooking(ICommand[int]):    # write - returns booking id
    user_id: int
    room_id: int

@dataclass
class SendWelcomeEmail(ICommand[None]):  # write - no meaningful return
    user_id: int
```

### Handlers

One handler per message type. Constructor-injected dependencies - works with any DI container:

```python
from mediatorx import IQueryHandler

class GetUserByIdHandler(IQueryHandler[GetUserById, User]):
    def __init__(self, repo: IUserRepository):
        self._repo = repo

    async def handle(self, query: GetUserById) -> User:
        return await self._repo.get(query.user_id)
```

### Pipeline Behaviors

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

For simpler cases, use split pre/post/exception processors instead of the omnibus middleware shape:

```python
from mediatorx import MessagePreProcessor, MessageExceptionHandler

class ValidationProcessor(MessagePreProcessor[IValidate, TResponse]):
    async def handle(self, message: IValidate) -> None:
        message.validate()  # raises on invalid input

class RetryableErrorHandler(MessageExceptionHandler[IMessage, TResponse, TransientError]):
    async def handle(self, message, exc):
        return self.NotHandled  # let it bubble; record metric elsewhere
```

### Constraining Behaviors

Use the marker hierarchy (`IMessage`, `IBaseCommand`, `IBaseQuery`) to scope behaviors. A behavior bound to `IBaseCommand` only fires for commands, not queries - exactly like the C# `where TMessage : ICommand` constraint:

```python
mediator.add_behavior(TransactionBehavior, constraint=IBaseCommand)
# Wraps commands in a DB transaction. Queries skip this entirely.
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

mediator = Mediator(publisher=TaskWhenAllPublisher())   # parallel
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

## 🏗️ Clean Architecture with FastAPI

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
    m = Mediator(resolver=container.resolver())

    # Behaviors run outermost-first
    m.add_behavior(LoggingBehavior)
    m.add_behavior(TransactionBehavior, constraint=IBaseCommand)
    m.add_behavior(ValidationBehavior)

    # Handlers
    m.register(CreateBookingCommand, CreateBookingHandler)
    m.register(GetUserById, GetUserByIdHandler)

    return m
```

## 📊 Comparison

| Feature                              | MediatR | Mediator (martinothamar) | **mediatorx** |
|--------------------------------------|:-------:|:------------------------:|:-------------:|
| `IRequest<T>` / `IRequestHandler<,>` |   ✅    |            ✅            |      ✅       |
| Command / Query separation           |   ❌    |            ✅            |      ✅       |
| Streaming                            |   ✅    |            ✅            |      ✅       |
| Notifications                        |   ✅    |            ✅            |      ✅       |
| Pipeline behaviors                   |   ✅    |            ✅            |      ✅       |
| Pre/Post/Exception processors        |   ✅    |            ✅            |      ✅       |
| Compile-time handler validation      |   ❌    |     ✅ (source gen)      |   ❌ (runtime) |
| Native AOT / no reflection           |   ❌    |            ✅            |   N/A (Python) |
| Async-only                           |   ❌    |            ❌            |      ✅       |

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [Jimmy Bogard](https://github.com/jbogard) for [MediatR](https://github.com/LuckyPennySoftware/MediatR), which started all of this.
- [Martin Othamar](https://github.com/martinothamar) for [Mediator](https://github.com/martinothamar/Mediator), whose interface taxonomy this library mirrors.
