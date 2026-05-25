from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .markers import IMessage

TMessage = TypeVar("TMessage", contravariant=True, bound=IMessage)
TResponseInv = TypeVar("TResponseInv")
TException = TypeVar("TException", bound=BaseException)


class MessagePreProcessor(ABC, Generic[TMessage, TResponseInv]):
    """Runs before the handler. Cannot short-circuit the pipeline."""

    @abstractmethod
    async def handle(self, message: TMessage) -> None:
        """Run before the handler executes."""
        ...


class MessagePostProcessor(ABC, Generic[TMessage, TResponseInv]):
    """Runs after the handler with access to the response."""

    @abstractmethod
    async def handle(self, message: TMessage, response: TResponseInv) -> None:
        """Run after the handler returns its response."""
        ...


class StreamMessagePreProcessor(ABC, Generic[TMessage, TResponseInv]):
    """Runs before a stream handler starts producing items."""

    @abstractmethod
    async def handle(self, message: TMessage) -> None:
        """Run before the stream begins."""
        ...


class StreamMessagePostProcessor(ABC, Generic[TMessage, TResponseInv]):
    """Runs after a stream handler finishes, with all collected responses."""

    @abstractmethod
    async def handle(self, message: TMessage, responses: list[TResponseInv]) -> None:
        """Run after the stream is exhausted."""
        ...


class ExceptionHandlingResult(Generic[TResponseInv]):
    """Outcome of a MessageExceptionHandler.handle() call."""

    __slots__ = ("handled", "response")

    def __init__(self, handled: bool, response: TResponseInv | None = None) -> None:
        """Capture whether the exception was handled and the recovery response."""
        self.handled = handled
        self.response = response


class MessageExceptionHandler(ABC, Generic[TMessage, TResponseInv, TException]):
    """Catch a specific exception type from the pipeline and optionally recover."""

    @property
    def NotHandled(self) -> ExceptionHandlingResult[TResponseInv]:
        """Sentinel result indicating the exception was not handled."""
        return ExceptionHandlingResult(handled=False)

    def Handled(self, response: TResponseInv) -> ExceptionHandlingResult[TResponseInv]:
        """Build a result indicating the exception was handled with the given response."""
        return ExceptionHandlingResult(handled=True, response=response)

    @abstractmethod
    async def handle(
        self,
        message: TMessage,
        exception: TException,
    ) -> ExceptionHandlingResult[TResponseInv]:
        """Handle the exception and return whether recovery succeeded."""
        ...
