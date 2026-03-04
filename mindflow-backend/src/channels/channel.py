"""
Abstract base class for messaging channels.

Each channel (Telegram, WhatsApp, Signal) implements this interface
so that the core application can interact with any channel uniformly.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IncomingMessage:
    """Normalised incoming message from any channel."""
    channel: str  # "telegram", "whatsapp", "signal"
    chat_id: str
    sender_id: str
    sender_name: str
    text: str
    timestamp: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # "image", "audio", "document"
    raw: Any = None


@dataclass
class OutgoingMessage:
    """Message to be sent through a channel."""
    chat_id: str
    text: str
    parse_mode: Optional[str] = "markdown"  # "markdown", "html", "plain"
    reply_to: Optional[str] = None


class MessagingChannel(ABC):
    """
    Abstract messaging channel interface.

    Subclasses implement the specifics of each platform (API calls,
    webhook verification, message formatting).
    """

    channel_name: str = "base"

    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> bool:
        """
        Configure the channel with platform-specific settings.

        Returns ``True`` if setup was successful.
        """
        ...

    @abstractmethod
    def handle_webhook(self, request_data: Any) -> Optional[IncomingMessage]:
        """
        Parse an incoming webhook request into an ``IncomingMessage``.

        Returns ``None`` if the request is not a valid message
        (e.g., a verification challenge).
        """
        ...

    @abstractmethod
    def send_message(self, message: OutgoingMessage) -> bool:
        """
        Send a message through the channel.

        Returns ``True`` if the message was sent successfully.
        """
        ...

    @abstractmethod
    def verify_webhook(self, request_data: Any) -> Optional[Any]:
        """
        Handle webhook verification challenges.

        Returns the appropriate response for the platform's verification
        protocol, or ``None`` if this is not a verification request.
        """
        ...

    def get_status(self) -> Dict[str, Any]:
        """Return the channel's current status."""
        return {
            "channel": self.channel_name,
            "configured": False,
        }
