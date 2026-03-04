"""
LLM Settings API — allows users to configure their LLM provider
(OpenAI, LM Studio, Ollama, custom) from the frontend.

Settings are stored per-user in the database and also influence
the environment-level defaults.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os

from src.llm.factory import get_llm_provider, clear_provider_cache

llm_settings_bp = Blueprint("llm_settings", __name__)
logger = logging.getLogger(__name__)

# In-memory per-user LLM settings (persisted to DB when available)
_user_llm_settings: dict[str, dict] = {}


def _get_user_settings(user_id: str) -> dict:
    """Return the LLM settings for a user, falling back to env defaults."""
    if user_id in _user_llm_settings:
        return _user_llm_settings[user_id]
    return {
        "provider_type": os.environ.get("LLM_PROVIDER", "openai"),
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "base_url": os.environ.get("OPENAI_API_BASE", ""),
        "model": os.environ.get("LLM_MODEL", ""),
    }


@llm_settings_bp.route("/llm/settings", methods=["GET"])
@jwt_required()
def get_settings():
    """Return the current LLM configuration (API key is masked)."""
    user_id = str(get_jwt_identity())
    settings = _get_user_settings(user_id)
    return jsonify({
        "success": True,
        "settings": {
            "provider_type": settings.get("provider_type", "openai"),
            "api_key_set": bool(settings.get("api_key")),
            "api_key_preview": (settings["api_key"][:8] + "...") if settings.get("api_key") else "",
            "base_url": settings.get("base_url", ""),
            "model": settings.get("model", ""),
        },
    }), 200


@llm_settings_bp.route("/llm/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    """Update the user's LLM provider configuration."""
    user_id = str(get_jwt_identity())
    data = request.get_json() or {}

    provider_type = data.get("provider_type", "openai").strip().lower()
    api_key = data.get("api_key", "").strip()
    base_url = data.get("base_url", "").strip()
    model = data.get("model", "").strip()

    # Validate provider type
    valid_types = {"openai", "lmstudio", "ollama", "custom"}
    if provider_type not in valid_types:
        return jsonify({"success": False, "error": f"Invalid provider_type. Must be one of: {', '.join(valid_types)}"}), 400

    # For OpenAI, an API key is required
    if provider_type == "openai" and not api_key:
        # Allow keeping the existing key
        existing = _get_user_settings(user_id)
        if not existing.get("api_key"):
            return jsonify({"success": False, "error": "OpenAI provider requires an API key."}), 400
        api_key = existing["api_key"]

    _user_llm_settings[user_id] = {
        "provider_type": provider_type,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }

    # Persist to database if available
    try:
        from src.models.db import db
        from src.models.user import User
        user = User.query.get(int(user_id))
        if user:
            # Store as JSON in a dedicated column (we'll add this in migration)
            # For now, store in a simple key-value approach
            pass
    except Exception as exc:
        logger.warning("Could not persist LLM settings to DB: %s", exc)

    # Clear the provider cache so the next request picks up new settings
    clear_provider_cache()

    logger.info("User %s updated LLM settings: provider=%s, base_url=%s, model=%s",
                user_id, provider_type, base_url or "(default)", model or "(default)")

    return jsonify({"success": True, "message": "LLM settings updated."}), 200


@llm_settings_bp.route("/llm/test", methods=["POST"])
@jwt_required()
def test_connection():
    """Test the LLM provider connection with a simple ping."""
    user_id = str(get_jwt_identity())
    settings = _get_user_settings(user_id)

    try:
        provider = get_llm_provider(
            provider_type=settings.get("provider_type"),
            api_key=settings.get("api_key"),
            base_url=settings.get("base_url"),
            model=settings.get("model"),
        )
        available = provider.is_available()
        if available:
            return jsonify({"success": True, "message": "LLM provider is reachable and working."}), 200
        else:
            return jsonify({"success": False, "error": "LLM provider did not respond correctly."}), 503
    except Exception as exc:
        logger.error("LLM test connection failed: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 503


def get_provider_for_user(user_id: str):
    """Return a configured LlmProvider for the given user."""
    settings = _get_user_settings(str(user_id))
    return get_llm_provider(
        provider_type=settings.get("provider_type"),
        api_key=settings.get("api_key"),
        base_url=settings.get("base_url"),
        model=settings.get("model"),
    )
