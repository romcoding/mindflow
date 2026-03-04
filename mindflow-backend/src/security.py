"""
Security middleware and utilities for MindFlow/Rovot.

Provides:
- Request validation and sanitization
- CORS configuration helper
- Security headers middleware
- Input validation decorators
- Logging sanitization (prevent credential leaks in logs)
"""
from __future__ import annotations

import functools
import logging
import os
import re
from typing import Any, Dict, List, Optional

from flask import Flask, Response, request

logger = logging.getLogger(__name__)

# Patterns that should never appear in logs
_SENSITIVE_PATTERNS = re.compile(
    r"(password|secret|token|api_key|apikey|authorization|cookie|session)"
    r"[\s]*[=:]\s*['\"]?([^\s'\"&]+)",
    re.IGNORECASE,
)


def configure_security(app: Flask) -> None:
    """
    Apply security configurations to the Flask application.

    This function should be called during application initialisation.
    """
    # ── Security headers ─────────────────────────────────────────────
    @app.after_request
    def add_security_headers(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # Remove server header
        response.headers.pop("Server", None)

        # HSTS in production
        if os.environ.get("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    # ── Request size limit ───────────────────────────────────────────
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # ── Session security ─────────────────────────────────────────────
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    logger.info("Security middleware configured")


def configure_cors(app: Flask) -> None:
    """
    Configure CORS with strict origin control.

    In production, only explicitly allowed origins are permitted.
    In development, localhost origins are allowed.
    """
    from flask_cors import CORS

    env = os.environ.get("FLASK_ENV", "production")
    origins_str = os.environ.get("CORS_ORIGINS", "")

    if env == "production" and origins_str:
        origins = [o.strip() for o in origins_str.split(",") if o.strip()]
    else:
        origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
        if origins_str:
            origins.extend(o.strip() for o in origins_str.split(",") if o.strip())

    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=600,
    )

    logger.info("CORS configured for origins: %s", origins)


def sanitize_log_message(message: str) -> str:
    """Remove sensitive values from log messages."""
    return _SENSITIVE_PATTERNS.sub(r"\1=***REDACTED***", message)


def validate_email(email_str: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email_str))


def validate_url(url: str) -> bool:
    """Validate that a string is a valid HTTP(S) URL."""
    pattern = r"^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$"
    return bool(re.match(pattern, url))


def sanitize_input(text: str, *, max_length: int = 10000) -> str:
    """
    Sanitize user input by removing potentially dangerous content.

    This is a defense-in-depth measure; the primary defense is
    parameterised queries and proper output encoding.
    """
    if not text:
        return ""
    # Truncate
    text = text[:max_length]
    # Remove null bytes
    text = text.replace("\x00", "")
    return text.strip()


def require_json(f):
    """Decorator that ensures the request has a JSON body."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            from flask import jsonify
            return jsonify({"error": "Content-Type must be application/json"}), 415
        return f(*args, **kwargs)
    return wrapper
