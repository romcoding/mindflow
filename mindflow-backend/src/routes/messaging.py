"""
Unified Messaging API — handles webhooks and configuration for all
messaging channels (Telegram, WhatsApp, Signal).

Provides a single webhook endpoint pattern:
    /api/messaging/webhook/<channel_name>

And configuration endpoints:
    /api/messaging/<channel_name>/setup
    /api/messaging/<channel_name>/status
    /api/messaging/<channel_name>/test
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import logging

from src.channels.channel import IncomingMessage, OutgoingMessage
from src.channels.whatsapp_channel import WhatsAppChannel
from src.channels.signal_channel import SignalChannel

messaging_bp = Blueprint("messaging", __name__)
logger = logging.getLogger(__name__)

# Channel registry
_channels = {
    "whatsapp": WhatsAppChannel(),
    "signal": SignalChannel(),
}

# User-channel linking (chat_id -> user_id)
_channel_links: dict[str, dict[str, str]] = {
    "whatsapp": {},
    "signal": {},
}

# Pending link tokens (token -> user_id)
_pending_links: dict[str, dict] = {}


def _process_message(channel_name: str, msg: IncomingMessage):
    """
    Process an incoming message from any channel.

    1. Check if the sender is linked to a user account.
    2. If linked, forward to the AI assistant for processing.
    3. If not linked, check for link commands.
    """
    channel = _channels.get(channel_name)
    if not channel:
        return

    # Check for link command
    text_lower = msg.text.strip().lower()
    if text_lower.startswith("/link ") or text_lower.startswith("/start "):
        token = msg.text.strip().split(" ", 1)[1].strip() if " " in msg.text else ""
        if token and token in _pending_links:
            link_info = _pending_links.pop(token)
            user_id = link_info["user_id"]
            _channel_links.setdefault(channel_name, {})[msg.chat_id] = user_id

            # Persist the link
            try:
                from src.models.user import User
                from src.models.db import db
                user = User.query.get(int(user_id))
                if user and channel_name == "whatsapp":
                    # Store in a generic field or dedicated column
                    pass
            except Exception:
                pass

            channel.send_message(OutgoingMessage(
                chat_id=msg.chat_id,
                text="Your account has been linked successfully! You can now send me messages and I'll process them as tasks, notes, or contacts.\n\nTry saying: *Create a task: Review quarterly report*",
            ))
            return

        channel.send_message(OutgoingMessage(
            chat_id=msg.chat_id,
            text="Invalid or expired link token. Please generate a new one from the MindFlow settings page.",
        ))
        return

    # Check if sender is linked
    user_id = _channel_links.get(channel_name, {}).get(msg.chat_id)
    if not user_id:
        channel.send_message(OutgoingMessage(
            chat_id=msg.chat_id,
            text=(
                "Welcome to Rovot! To get started, link your account:\n\n"
                "1. Go to MindFlow Settings > Messaging Channels\n"
                f"2. Select {channel_name.title()} and click 'Generate Link Token'\n"
                "3. Send me: /link YOUR_TOKEN"
            ),
        ))
        return

    # Process message through AI assistant
    try:
        from flask import current_app
        from src.llm.factory import get_llm_provider
        from src.routes.ai_assistant import SYSTEM_PROMPT, TOOLS, FUNCTION_MAP
        from datetime import datetime

        provider = get_llm_provider()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        system_msg = SYSTEM_PROMPT.replace('{today}', today)

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": msg.text},
        ]

        response = provider.chat_completion(
            messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1500,
        )

        # Execute tool calls
        if response.tool_calls:
            if response.raw:
                messages.append(response.raw.choices[0].message)

            for tc in response.tool_calls:
                executor = FUNCTION_MAP.get(tc.function_name)
                if executor:
                    try:
                        result = executor(int(user_id), tc.arguments)
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                else:
                    result = {"success": False, "error": f"Unknown function: {tc.function_name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

            final = provider.chat_completion(messages, temperature=0.7, max_tokens=1500)
            reply_text = final.content or "Done!"
        else:
            reply_text = response.content or "I couldn't process that. Please try again."

        # Send reply (truncate for messaging platforms)
        if len(reply_text) > 4000:
            reply_text = reply_text[:3997] + "..."

        channel.send_message(OutgoingMessage(chat_id=msg.chat_id, text=reply_text))

    except Exception as exc:
        logger.error("Error processing %s message: %s", channel_name, exc)
        channel.send_message(OutgoingMessage(
            chat_id=msg.chat_id,
            text="Sorry, I encountered an error processing your message. Please try again later.",
        ))


# ── Webhook endpoints ──────────────────────────────────────────────────

@messaging_bp.route("/messaging/webhook/<channel_name>", methods=["GET"])
def webhook_verify(channel_name: str):
    """Handle webhook verification (GET requests)."""
    channel = _channels.get(channel_name)
    if not channel:
        return jsonify({"error": f"Unknown channel: {channel_name}"}), 404

    result = channel.verify_webhook(request)
    if result is not None:
        return str(result), 200
    return jsonify({"error": "Verification failed"}), 403


@messaging_bp.route("/messaging/webhook/<channel_name>", methods=["POST"])
def webhook_receive(channel_name: str):
    """Handle incoming messages (POST requests)."""
    channel = _channels.get(channel_name)
    if not channel:
        return jsonify({"error": f"Unknown channel: {channel_name}"}), 404

    try:
        data = request.get_json(force=True, silent=True) or {}
        msg = channel.handle_webhook(data)

        if msg:
            # Process in the current request context
            _process_message(channel_name, msg)

        return jsonify({"status": "ok"}), 200

    except Exception as exc:
        logger.error("Webhook error for %s: %s", channel_name, exc)
        return jsonify({"status": "ok"}), 200  # Always return 200 to avoid retries


# ── Configuration endpoints ───────────────────────────────────────────

@messaging_bp.route("/messaging/<channel_name>/setup", methods=["POST"])
@jwt_required()
def setup_channel(channel_name: str):
    """Configure a messaging channel."""
    channel = _channels.get(channel_name)
    if not channel:
        return jsonify({"success": False, "error": f"Unknown channel: {channel_name}"}), 404

    config = request.get_json() or {}
    success = channel.setup(config)

    if success:
        return jsonify({"success": True, "message": f"{channel_name.title()} channel configured."}), 200
    return jsonify({"success": False, "error": "Configuration failed. Check your credentials."}), 400


@messaging_bp.route("/messaging/<channel_name>/status", methods=["GET"])
@jwt_required()
def channel_status(channel_name: str):
    """Get the status of a messaging channel."""
    channel = _channels.get(channel_name)
    if not channel:
        return jsonify({"success": False, "error": f"Unknown channel: {channel_name}"}), 404

    return jsonify({"success": True, "status": channel.get_status()}), 200


@messaging_bp.route("/messaging/<channel_name>/test", methods=["POST"])
@jwt_required()
def test_channel(channel_name: str):
    """Send a test message through a channel."""
    channel = _channels.get(channel_name)
    if not channel:
        return jsonify({"success": False, "error": f"Unknown channel: {channel_name}"}), 404

    data = request.get_json() or {}
    chat_id = data.get("chat_id", "").strip()
    if not chat_id:
        return jsonify({"success": False, "error": "chat_id is required."}), 400

    success = channel.send_message(OutgoingMessage(
        chat_id=chat_id,
        text="This is a test message from Rovot/MindFlow. Your channel is configured correctly!",
    ))

    if success:
        return jsonify({"success": True, "message": "Test message sent."}), 200
    return jsonify({"success": False, "error": "Failed to send test message."}), 500


@messaging_bp.route("/messaging/generate-link-token", methods=["POST"])
@jwt_required()
def generate_link_token():
    """Generate a one-time token for linking a messaging account."""
    import secrets
    user_id = str(get_jwt_identity())
    token = secrets.token_urlsafe(16)
    _pending_links[token] = {
        "user_id": user_id,
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    }
    return jsonify({
        "success": True,
        "token": token,
        "instructions": "Send this to the bot: /link " + token,
    }), 200


@messaging_bp.route("/messaging/channels", methods=["GET"])
@jwt_required()
def list_channels():
    """List all available messaging channels and their status."""
    statuses = {}
    for name, channel in _channels.items():
        statuses[name] = channel.get_status()
    return jsonify({"success": True, "channels": statuses}), 200
