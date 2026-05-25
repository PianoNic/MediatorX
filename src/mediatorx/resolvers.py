from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class IResolver(Protocol):
    """Pluggable handler factory. Adapt your DI container to this protocol."""

    def resolve(self, t: type[T]) -> T:
        """Resolve an instance of the given type."""
        ...


class DictResolver:
    """Default in-memory resolver. Maps type to instance or factory."""

    def __init__(self) -> None:
        """Create an empty resolver."""
        self._instances: dict[type, object] = {}
        self._factories: dict[type, Callable[[], object]] = {}

    def add_instance(self, t: type, instance: object) -> DictResolver:
        """Register a pre-built instance for type t."""
        self._instances[t] = instance
        return self

    def add_factory(self, t: type, factory: Callable[[], object]) -> DictResolver:
        """Register a zero-arg factory for type t."""
        self._factories[t] = factory
        return self

    def resolve(self, t: type) -> object:
        """Return a registered instance, factory-built instance, or fall back to t()."""
        if t in self._instances:
            return self._instances[t]
        if t in self._factories:
            return self._factories[t]()
        try:
            return t()
        except TypeError as e:
            raise KeyError(
                f"no registration for {t.__name__} - register it via "
                f"add_instance/add_factory, or use a real DI container"
            ) from e
