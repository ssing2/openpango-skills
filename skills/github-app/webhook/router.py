"""
Event router for GitHub webhook events
"""

import logging
from typing import Dict, Any, Callable, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """GitHub event types"""
    PULL_REQUEST = "pull_request"
    ISSUE_COMMENT = "issue_comment"
    PUSH = "push"
    ISSUES = "issues"
    RELEASE = "release"
    CREATE = "create"
    DELETE = "delete"


class EventRouter:
    """
    Route GitHub webhook events to appropriate handlers
    
    Example:
        >>> router = EventRouter()
        >>> @router.on(EventType.PULL_REQUEST)
        ... async def handle_pr(data):
        ...     print(f"PR #{data['pull_request']['number']}")
    """
    
    def __init__(self):
        self.handlers: Dict[EventType, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
    
    def on(self, event_type: EventType):
        """
        Decorator to register event handler
        
        Args:
            event_type: Type of GitHub event
        
        Example:
            @router.on(EventType.PULL_REQUEST)
            async def handle_pr(data):
                # Process PR
                pass
        """
        def decorator(func: Callable[[Dict[str, Any]], Awaitable[None]]):
            self.handlers[event_type] = func
            logger.info(f"Registered handler for {event_type.value}")
            return func
        return decorator
    
    async def route(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Route event to registered handler
        
        Args:
            event_type: GitHub event type string
            data: Event payload
        
        Returns:
            bool: True if handler was called, False otherwise
        """
        try:
            event = EventType(event_type)
        except ValueError:
            logger.info(f"No handler for event type: {event_type}")
            return False
        
        handler = self.handlers.get(event)
        if not handler:
            logger.info(f"No registered handler for {event.value}")
            return False
        
        try:
            await handler(data)
            return True
        except Exception as e:
            logger.error(f"Error in handler for {event.value}: {e}", exc_info=True)
            return False
    
    def list_handlers(self) -> list:
        """List all registered event types"""
        return [event.value for event in self.handlers.keys()]


# Global router instance
router = EventRouter()
