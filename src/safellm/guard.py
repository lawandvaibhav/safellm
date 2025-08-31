"""Guard protocol and base classes for SafeLLM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from .context import Context
from .decisions import Decision


@runtime_checkable
class Guard(Protocol):
    """Protocol for guards that can validate and transform data."""

    name: str

    def check(self, data: Any, ctx: Context) -> Decision:
        """Synchronously check data and return a decision.

        Args:
            data: The data to validate
            ctx: Context object with request metadata

        Returns:
            Decision object indicating the result
        """
        ...

    async def acheck(self, data: Any, ctx: Context) -> Decision:
        """Asynchronously check data and return a decision.

        Args:
            data: The data to validate
            ctx: Context object with request metadata

        Returns:
            Decision object indicating the result
        """
        ...


class BaseGuard(ABC):
    """Base class for implementing guards.

    Provides default async implementation that calls the sync version.
    Subclasses should implement either check() or both check() and acheck().
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the guard for identification and logging."""
        ...

    @abstractmethod
    def check(self, data: Any, ctx: Context) -> Decision:
        """Synchronously check data and return a decision."""
        ...

    async def acheck(self, data: Any, ctx: Context) -> Decision:
        """Asynchronously check data and return a decision.

        Default implementation calls the synchronous check method.
        Override this method for guards that need async operations.
        """
        return self.check(data, ctx)


class AsyncGuard(ABC):
    """Base class for guards that are primarily asynchronous.

    Provides default sync implementation that runs the async version.
    Use this for guards that need to make network calls or other async operations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the guard for identification and logging."""
        ...

    def check(self, data: Any, ctx: Context) -> Decision:
        """Synchronously check data by running async implementation.

        Note: This will raise an error if called from within an async context.
        Use acheck() directly in async code.
        """
        import asyncio

        try:
            # Check if we're already in an event loop
            asyncio.get_running_loop()
            raise RuntimeError(
                f"Cannot call sync check() on async guard {self.name} "
                "from within an async context. Use acheck() instead."
            )
        except RuntimeError:
            # No event loop running, we can create one
            pass

        return asyncio.run(self.acheck(data, ctx))

    @abstractmethod
    async def acheck(self, data: Any, ctx: Context) -> Decision:
        """Asynchronously check data and return a decision."""
        ...
