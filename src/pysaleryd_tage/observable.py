"""Generic async observable implementation"""

import asyncio
from typing import Any, Callable, Generic, List, Self, TypeVar

T = TypeVar("T")


class Observable(Generic[T]):
    """A simple observable pattern implementation for async callbacks"""

    def __init__(self):
        self._observers: List[Callable[[T], Any]] = []

    def subscribe(self, observer: Callable[[T], Any]) -> Self:
        """Subscribe to changes"""
        self._observers.append(observer)
        return self

    def unsubscribe(self, observer: Callable[[T], Any]) -> Self:
        """Unsubscribe from changes"""
        self._observers.remove(observer)
        return self

    async def notify(self, value: T) -> Self:
        """Notify all observers of a change"""
        for observer in self._observers:
            result = observer(value)
            if asyncio.iscoroutine(result):
                await result

        return self
