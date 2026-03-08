import asyncio
import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger(__name__)


class EventBus:
    """
    Async application-level event bus.

    - Business logic calls  await bus.publish(SomeEvent(...))
    - Side-effect handlers (file writing, RabbitMQ) are registered via subscribe()
    - All handlers run concurrently via asyncio.gather — core logic never blocks on them
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a single handler — useful if sir wants to disable one side effect."""
        try:
            self._handlers[event_type].remove(handler)
        except ValueError:
            pass

    async def publish(self, event) -> None:
        """
        Fire event to all registered handlers concurrently.
        Handlers must be  async def handle_*(event) -> None.
        """
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return

        tasks = [asyncio.create_task(h(event)) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any handler errors without crashing the pipeline
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler '{handler.__name__}' failed for event "
                    f"'{event.type}': {result}"
                )


# Singleton imported everywhere
event_bus = EventBus()