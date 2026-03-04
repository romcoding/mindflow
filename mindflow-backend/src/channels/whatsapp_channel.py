"""
WhatsApp Business Cloud API channel implementation.

Supports the Meta WhatsApp Business Cloud API for sending and receiving
messages via webhooks.

Configuration
-------------
WHATSAPP_PHONE_NUMBER_ID : The Phone Number ID from Meta Business Suite
WHATSAPP_ACCESS_TOKEN    : Permanent access token for the WhatsApp Business API
WHATSAPP_VERIFY_TOKEN    : Custom token for webhook verification
WHATSAPP_APP_SECRET      : App secret for request signature verification

Setup instructions:
1. Create a Meta Business App at https://developers.facebook.com
2. Add the WhatsApp product to your app
3. Get a permanent access token (System User token recommended)
4. Configure the webhook URL to: https://your-backend.com/api/messaging/webhook/whatsapp
5. Subscribe to the "messages" webhook field
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional

import requests

from src.channels.channel import IncomingMessage, MessagingChannel, OutgoingMessage

logger = logging.getLogger(__name__)

WHATSAPP_API_BASE = "https://graph.facebook.com/v18.0"


class WhatsAppChannel(MessagingChannel):
    """WhatsApp Business Cloud API channel."""

    channel_name = "whatsapp"

    def __init__(self):
        self._phone_number_id: str = ""
        self._access_token: str = ""
        self._verify_token: str = ""
        self._app_secret: str = ""
        self._configured: bool = False

    def setup(self, config: Dict[str, Any]) -> bool:
        self._phone_number_id = (
            config.get("phone_number_id")
            or os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        ).strip()
        self._access_token = (
            config.get("access_token")
            or os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        ).strip()
        self._verify_token = (
            config.get("verify_token")
            or os.environ.get("WHATSAPP_VERIFY_TOKEN", "rovot-whatsapp-verify")
        ).strip()
        self._app_secret = (
            config.get("app_secret")
            or os.environ.get("WHATSAPP_APP_SECRET", "")
        ).strip()

        self._configured = bool(self._phone_number_id and self._access_token)
        if self._configured:
            logger.info("WhatsApp channel configured (phone_number_id=%s)", self._phone_number_id)
        else:
            logger.warning("WhatsApp channel not fully configured")
        return self._configured

    def verify_webhook(self, request_data: Any) -> Optional[Any]:
        """
        Handle the Meta webhook verification challenge.

        Meta sends a GET request with:
        - hub.mode = "subscribe"
        - hub.verify_token = your verify token
        - hub.challenge = a challenge string to echo back
        """
        from flask import request as flask_request

        mode = flask_request.args.get("hub.mode")
        token = flask_request.args.get("hub.verify_token")
        challenge = flask_request.args.get("hub.challenge")

        if mode == "subscribe" and token == self._verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return challenge
        logger.warning("WhatsApp webhook verification failed")
        return None

    def handle_webhook(self, request_data: Any) -> Optional[IncomingMessage]:
        """Parse an incoming WhatsApp message from the webhook payload."""
        try:
            # Verify request signature if app_secret is configured
            if self._app_secret:
                from flask import request as flask_request
                signature = flask_request.headers.get("X-Hub-Signature-256", "")
                if not self._verify_signature(flask_request.get_data(), signature):
                    logger.warning("WhatsApp webhook signature verification failed")
                    return None

            data = request_data if isinstance(request_data, dict) else json.loads(request_data)

            # Navigate the nested webhook structure
            entry = data.get("entry", [])
            if not entry:
                return None

            changes = entry[0].get("changes", [])
            if not changes:
                return None

            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
            contacts = value.get("contacts", [{}])
            sender_name = contacts[0].get("profile", {}).get("name", "Unknown")

            # Extract text content
            text = ""
            media_url = None
            media_type = None

            if msg.get("type") == "text":
                text = msg.get("text", {}).get("body", "")
            elif msg.get("type") == "image":
                media_type = "image"
                text = msg.get("image", {}).get("caption", "[Image received]")
                media_url = msg.get("image", {}).get("id")
            elif msg.get("type") == "audio":
                media_type = "audio"
                text = "[Audio message received]"
                media_url = msg.get("audio", {}).get("id")
            elif msg.get("type") == "document":
                media_type = "document"
                text = msg.get("document", {}).get("caption", "[Document received]")
                media_url = msg.get("document", {}).get("id")
            else:
                text = f"[{msg.get('type', 'unknown')} message received]"

            return IncomingMessage(
                channel="whatsapp",
                chat_id=msg.get("from", ""),
                sender_id=msg.get("from", ""),
                sender_name=sender_name,
                text=text,
                timestamp=msg.get("timestamp"),
                media_url=media_url,
                media_type=media_type,
                raw=data,
            )

        except Exception as exc:
            logger.error("Error parsing WhatsApp webhook: %s", exc)
            return None

    def send_message(self, message: OutgoingMessage) -> bool:
        """Send a text message via the WhatsApp Business API."""
        if not self._configured:
            logger.error("WhatsApp channel not configured")
            return False

        url = f"{WHATSAPP_API_BASE}/{self._phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": message.chat_id,
            "type": "text",
            "text": {"body": message.text},
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                logger.info("WhatsApp message sent to %s", message.chat_id)
                return True
            else:
                logger.error("WhatsApp send failed: %s %s", resp.status_code, resp.text)
                return False
        except Exception as exc:
            logger.error("WhatsApp send error: %s", exc)
            return False

    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the X-Hub-Signature-256 header."""
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(
            self._app_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def get_status(self) -> Dict[str, Any]:
        return {
            "channel": self.channel_name,
            "configured": self._configured,
            "phone_number_id": self._phone_number_id[:6] + "..." if self._phone_number_id else "",
        }
