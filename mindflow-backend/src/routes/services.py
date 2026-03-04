"""
Services API — manage background services (File Watcher, Email Checker).

Provides endpoints to configure, start, stop, and query the status of
background services from the frontend settings page.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from src.services.file_watcher import FileWatcherService, FileEvent
from src.services.email_checker import EmailCheckerService, EmailRule

services_bp = Blueprint("services", __name__)
logger = logging.getLogger(__name__)

# Singleton service instances (initialised by init_services)
_file_watcher: FileWatcherService | None = None
_email_checker: EmailCheckerService | None = None


def init_services(app):
    """
    Initialise background services with the Flask app context.

    Called from ``main.py`` during application startup.
    """
    global _file_watcher, _email_checker

    def _on_file_event(user_id, event: FileEvent, content: str | None):
        """Callback: create a note from a file change."""
        if event.event_type == "deleted":
            return
        if not content:
            return
        try:
            from src.models.note import Note
            from src.models.db import db

            # Truncate content for the note
            preview = content[:2000]
            note = Note(
                user_id=int(user_id),
                title=f"File: {event.filename}",
                content=f"**{event.event_type.title()}:** `{event.path}`\n\n```\n{preview}\n```",
                category="reference",
            )
            db.session.add(note)
            db.session.commit()
            logger.info("Created note from file event: %s", event.filename)
        except Exception as exc:
            logger.error("Failed to create note from file event: %s", exc)

    def _on_email(user_id, email_msg, rule: EmailRule):
        """Callback: create a task or note from an email."""
        try:
            from src.models.db import db

            if rule.action == "task":
                from src.models.task import Task

                task = Task(
                    user_id=int(user_id),
                    title=f"Email: {email_msg.subject}",
                    description=(
                        f"**From:** {email_msg.sender_name} <{email_msg.sender}>\n"
                        f"**Date:** {email_msg.date}\n\n"
                        f"{email_msg.body_text[:1000]}"
                    ),
                    priority=rule.priority,
                    status="todo",
                    board_column="todo",
                    board_position=0,
                )
                db.session.add(task)
                db.session.commit()
                logger.info("Created task from email: %s", email_msg.subject)

            elif rule.action == "note":
                from src.models.note import Note

                note = Note(
                    user_id=int(user_id),
                    title=f"Email: {email_msg.subject}",
                    content=(
                        f"**From:** {email_msg.sender_name} <{email_msg.sender}>\n"
                        f"**Date:** {email_msg.date}\n\n"
                        f"{email_msg.body_text[:2000]}"
                    ),
                    category=rule.category,
                )
                db.session.add(note)
                db.session.commit()
                logger.info("Created note from email: %s", email_msg.subject)

            elif rule.action == "ignore":
                pass

        except Exception as exc:
            logger.error("Failed to process email: %s", exc)

    _file_watcher = FileWatcherService(app=app, on_file_event=_on_file_event)
    _email_checker = EmailCheckerService(app=app, on_email=_on_email)

    logger.info("Background services initialised")


# ── File Watcher endpoints ─────────────────────────────────────────────

@services_bp.route("/services/file-watcher/status", methods=["GET"])
@jwt_required()
def file_watcher_status():
    if not _file_watcher:
        return jsonify({"success": False, "error": "File watcher not initialised"}), 503
    return jsonify({"success": True, "status": _file_watcher.get_status()}), 200


@services_bp.route("/services/file-watcher/watch", methods=["POST"])
@jwt_required()
def add_file_watch():
    user_id = str(get_jwt_identity())
    data = request.get_json() or {}
    directory = data.get("directory", "").strip()
    recursive = data.get("recursive", True)

    if not directory:
        return jsonify({"success": False, "error": "Directory path is required."}), 400

    if not _file_watcher:
        return jsonify({"success": False, "error": "File watcher not initialised"}), 503

    ok = _file_watcher.add_watch(user_id, directory, recursive=recursive)
    if ok:
        return jsonify({"success": True, "message": f"Now watching: {directory}"}), 200
    return jsonify({"success": False, "error": "Directory not found or not accessible."}), 400


@services_bp.route("/services/file-watcher/watch", methods=["DELETE"])
@jwt_required()
def remove_file_watch():
    user_id = str(get_jwt_identity())
    if _file_watcher and _file_watcher.remove_watch(user_id):
        return jsonify({"success": True, "message": "Watch removed."}), 200
    return jsonify({"success": False, "error": "No active watch found."}), 404


@services_bp.route("/services/file-watcher/start", methods=["POST"])
@jwt_required()
def start_file_watcher():
    if not _file_watcher:
        return jsonify({"success": False, "error": "File watcher not initialised"}), 503
    _file_watcher.start()
    return jsonify({"success": True, "message": "File watcher started."}), 200


@services_bp.route("/services/file-watcher/stop", methods=["POST"])
@jwt_required()
def stop_file_watcher():
    if not _file_watcher:
        return jsonify({"success": False, "error": "File watcher not initialised"}), 503
    _file_watcher.stop()
    return jsonify({"success": True, "message": "File watcher stopped."}), 200


# ── Email Checker endpoints ───────────────────────────────────────────

@services_bp.route("/services/email/status", methods=["GET"])
@jwt_required()
def email_checker_status():
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    return jsonify({"success": True, "status": _email_checker.get_status()}), 200


@services_bp.route("/services/email/account", methods=["POST"])
@jwt_required()
def add_email_account():
    user_id = str(get_jwt_identity())
    data = request.get_json() or {}

    email_address = data.get("email", "").strip()
    password = data.get("password", "").strip()
    provider = data.get("provider", "custom").strip().lower()
    imap_server = data.get("imap_server", "").strip()
    folder = data.get("folder", "INBOX").strip()

    if not email_address or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503

    ok = _email_checker.add_account(
        user_id,
        imap_server=imap_server,
        email_address=email_address,
        password=password,
        provider=provider,
        folder=folder,
    )
    if ok:
        return jsonify({"success": True, "message": "Email account configured."}), 200
    return jsonify({"success": False, "error": "Invalid email configuration."}), 400


@services_bp.route("/services/email/account", methods=["DELETE"])
@jwt_required()
def remove_email_account():
    user_id = str(get_jwt_identity())
    if _email_checker and _email_checker.remove_account(user_id):
        return jsonify({"success": True, "message": "Email account removed."}), 200
    return jsonify({"success": False, "error": "No email account found."}), 404


@services_bp.route("/services/email/test", methods=["POST"])
@jwt_required()
def test_email_connection():
    user_id = str(get_jwt_identity())
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    result = _email_checker.test_connection(user_id)
    status_code = 200 if result["success"] else 503
    return jsonify(result), status_code


@services_bp.route("/services/email/check-now", methods=["POST"])
@jwt_required()
def check_email_now():
    user_id = str(get_jwt_identity())
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    messages = _email_checker.check_now(user_id)
    return jsonify({
        "success": True,
        "new_messages": len(messages),
        "subjects": [m.subject for m in messages[:10]],
    }), 200


@services_bp.route("/services/email/rules", methods=["GET"])
@jwt_required()
def get_email_rules():
    user_id = str(get_jwt_identity())
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    rules = _email_checker._rules.get(user_id, [])
    return jsonify({
        "success": True,
        "rules": [
            {
                "name": r.name,
                "enabled": r.enabled,
                "from_contains": r.from_contains,
                "subject_contains": r.subject_contains,
                "body_contains": r.body_contains,
                "has_attachment": r.has_attachment,
                "action": r.action,
                "priority": r.priority,
                "category": r.category,
                "tags": r.tags,
            }
            for r in rules
        ],
    }), 200


@services_bp.route("/services/email/rules", methods=["PUT"])
@jwt_required()
def update_email_rules():
    user_id = str(get_jwt_identity())
    data = request.get_json() or {}
    rules_data = data.get("rules", [])

    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503

    rules = []
    for rd in rules_data:
        rules.append(EmailRule(
            name=rd.get("name", "Unnamed"),
            enabled=rd.get("enabled", True),
            from_contains=rd.get("from_contains"),
            subject_contains=rd.get("subject_contains"),
            body_contains=rd.get("body_contains"),
            has_attachment=rd.get("has_attachment"),
            action=rd.get("action", "note"),
            priority=rd.get("priority", "medium"),
            category=rd.get("category", "general"),
            tags=rd.get("tags", ""),
        ))

    _email_checker.set_rules(user_id, rules)
    return jsonify({"success": True, "message": f"{len(rules)} rule(s) updated."}), 200


@services_bp.route("/services/email/start", methods=["POST"])
@jwt_required()
def start_email_checker():
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    _email_checker.start()
    return jsonify({"success": True, "message": "Email checker started."}), 200


@services_bp.route("/services/email/stop", methods=["POST"])
@jwt_required()
def stop_email_checker():
    if not _email_checker:
        return jsonify({"success": False, "error": "Email checker not initialised"}), 503
    _email_checker.stop()
    return jsonify({"success": True, "message": "Email checker stopped."}), 200
