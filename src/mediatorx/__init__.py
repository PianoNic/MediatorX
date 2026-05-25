"""mediatorx — CQRS-style mediator and pipeline for Python."""

from __future__ import annotations

from ._unit import UNIT, Unit
from .behaviors import (
    IPipelineBehavior,
    IStreamPipelineBehavior,
    MessageHandlerDelegate,
    StreamHandlerDelegate,
)
from .handlers import (
    ICommandHandler,
    INotificationHandler,
    IQueryHandler,
    IRequestHandler,
    IStreamCommandHandler,
    IStreamQueryHandler,
    IStreamRequestHandler,
)
from .markers import (
    IBaseCommand,
    IBaseQuery,
    IBaseRequest,
    IMessage,
    INotification,
    IStreamMessage,
)
from .mediator import IMediator, IPublisher, ISender, Mediator
from .messages import (
    ICommand,
    IQuery,
    IRequest,
    IStreamCommand,
    IStreamQuery,
    IStreamRequest,
)
from .processors import (
    ExceptionHandlingResult,
    MessageExceptionHandler,
    MessagePostProcessor,
    MessagePreProcessor,
    StreamMessagePostProcessor,
    StreamMessagePreProcessor,
)
from .publishers import (
    ForeachAwaitPublisher,
    INotificationPublisher,
    TaskWhenAllPublisher,
)
from .registry import Registry
from .resolvers import DictResolver, IResolver

__all__ = [
    "UNIT",
    "DictResolver",
    "ExceptionHandlingResult",
    "ForeachAwaitPublisher",
    "IBaseCommand",
    "IBaseQuery",
    "IBaseRequest",
    "ICommand",
    "ICommandHandler",
    "IMediator",
    "IMessage",
    "INotification",
    "INotificationHandler",
    "INotificationPublisher",
    "IPipelineBehavior",
    "IPublisher",
    "IQuery",
    "IQueryHandler",
    "IRequest",
    "IRequestHandler",
    "IResolver",
    "ISender",
    "IStreamCommand",
    "IStreamCommandHandler",
    "IStreamMessage",
    "IStreamPipelineBehavior",
    "IStreamQuery",
    "IStreamQueryHandler",
    "IStreamRequest",
    "IStreamRequestHandler",
    "Mediator",
    "MessageExceptionHandler",
    "MessageHandlerDelegate",
    "MessagePostProcessor",
    "MessagePreProcessor",
    "Registry",
    "StreamHandlerDelegate",
    "StreamMessagePostProcessor",
    "StreamMessagePreProcessor",
    "TaskWhenAllPublisher",
    "Unit",
]
