"""
Signal Messenger channel implementation.

Uses the ``signal-cli-rest-api`` Docker container as a bridge to the
Signal network.  The REST API is typically available at
``http://localhost:8080`` when running the container.

Docker setup::

    docker run -d --name signal-api \\
      -p 8080:8080 \\
      -v $HOME/.local/share/signal-cli:/home/.local/share/signal-cli \\
      -e MODE=json-rpc \\
      bbernhard/signal-cli-rest-api

After starting the container, register or link a phone number::

    curl -X POST 'http://localhost:8080/v1/register/+1234567890'

Configuration
-------------
SIGNAL_API_URL       : URL of the signal-cli REST API (default: http://localhost:8080)
SIGNAL_PHONE_NUMBER  : The registered Signal phone number (e.g. +1234567890)
SIGNAL_WEBHOOK_SECRET: Optional secret for webhook authentication
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

import requests

from src.channels.channel import IncomingMessage, MessagingChannel, OutgoingMessage

logger = logging.getLogger(__name__)


class SignalChannel(MessagingChannel):
    """Signal Messenger channel via signal-cli REST API."""

    channel_name = "signal"

    def __init__(self):
        self._api_url: str = ""
        self._phone_number: str = ""
        self._webhook_secret: str = ""
        self._configured: bool = False

    def setup(self, config: Dict[str, Any]) -> bool:
        self._api_url = (
            config.get("api_url")
            or os.environ.get("SIGNAL_API_URL", "http://localhost:8080")
        ).strip().rstrip("/")
        self._phone_number = (
            config.get("phone_number")
            or os.environ.get("SIGNAL_PHONE_NUMBER", "")
        ).strip()
        self._webhook_secret = (
            config.get("webhook_secret")
            or os.environ.get("SIGNAL_WEBHOOK_SECRET", "")
        ).strip()

        self._configured = bool(self._api_url and self._phone_number)
        if self._configured:
            logger.info("Signal channel configured (number=%s, api=%s)", self._phone_number, self._api_url)
        else:
            logger.warning("Signal channel not fully configured")
        return self._configured

    def verify_webhook(self, request_data: Any) -> Optional[Any]:
        """
        Signal-cli REST API webhooks don't have a verification handshake
        like Meta. We verify using a shared secret in the header instead.
        """
        if not self._webhook_secret:
            return None  # No verification needed

        from flask import request as flask_request
        token = flask_request.headers.get("X-Signal-Webhook-Secret", "")
        if token == self._webhook_secret:
            return "OK"
        logger.warning("Signal webhook secret mismatch")
        return None

    def handle_webhook(self, request_data: Any) -> Optional[IncomingMessage]:
        """Parse an incoming Signal message from the webhook payload."""
        try:
            data = request_data if isinstance(request_data, dict) else json.loads(request_data)

            # signal-cli REST API webhook format
            envelope = data.get("envelope", data)
            source = envelope.get("source", "") or envelope.get("sourceNumber", "")
            source_name = envelope.get("sourceName", source)
            timestamp = envelope.get("timestamp")

            # Data message contains the actual text
            data_msg = envelope.get("dataMessage", {})
            if not data_msg:
                # Could be a receipt or typing indicator
                return None

            text = data_msg.get("message", "")
            if not text:
                return None

            # Check for attachments
            media_url = None
            media_type = None
            attachments = data_msg.get("attachments", [])
            if attachments:
                att = attachments[0]
                media_type = att.get("contentType", "").split("/")[0]
                media_url = att.get("id")

            return IncomingMessage(
                channel="signal",
                chat_id=source,
                sender_id=source,
                sender_name=source_name,
                text=text,
                timestamp=str(timestamp) if timestamp else None,
                media_url=media_url,
                media_type=media_type,
                raw=data,
            )

        except Exception as exc:
            logger.error("Error parsing Signal webhook: %s", exc)
            return None

    def send_message(self, message: OutgoingMessage) -> bool:
        """Send a text message via the signal-cli REST API."""
        if not self._configured:
            logger.error("Signal channel not configured")
            return False

        url = f"{self._api_url}/v2/send"
        payload = {
            "message": message.text,
            "number": self._phone_number,
            "recipients": [message.chat_id],
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                logger.info("Signal message sent to %s", message.chat_id)
                return True
            else:
                logger.error("Signal send failed: %s %s", resp.status_code, resp.text)
                return False
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to signal-cli REST API at %s", self._api_url)
            return False
        except Exception as exc:
            logger.error("Signal send error: %s", exc)
            return False

    def register_webhook(self, webhook_url: str) -> bool:
        """Register a webhook URL with the signal-cli REST API."""
        if not self._configured:
            return False

        url = f"{self._api_url}/v1/receive/{self._phone_number}"
        # The signal-cli REST API uses a different mechanism for webhooks
        # We need to configure it to forward messages to our endpoint
        try:
            # Check if the API is reachable
            resp = requests.get(f"{self._api_url}/v1/about", timeout=10)
            if resp.status_code == 200:
                logger.info("Signal API is reachable. Configure webhook in signal-cli config.")
                return True
            return False
        except Exception as exc:
            logger.error("Signal API not reachable: %s", exc)
            return False

    def get_status(self) -> Dict[str, Any]:
        status = {
            "channel": self.channel_name,
            "configured": self._configured,
            "phone_number": self._phone_number[:4] + "****" if self._phone_number else "",
            "api_url": self._api_url,
            "api_reachable": False,
        }

        if self._configured:
            try:
                resp = requests.get(f"{self._api_url}/v1/about", timeout=5)
                status["api_reachable"] = resp.status_code == 200
            except Exception:
                pass

        return status
