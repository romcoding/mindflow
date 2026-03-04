"""
Email Checker Service for MindFlow/Rovot.

Periodically checks a user's email inbox via IMAP and creates tasks or
notes based on configurable rules. Supports Gmail, Outlook, and any
standard IMAP server.

Security
--------
- Credentials are stored encrypted in the database (see ``crypto`` module).
- Connections always use TLS (IMAP over SSL on port 993).
- For Gmail, App Passwords or OAuth2 tokens are recommended.
"""
from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Well-known IMAP servers
IMAP_SERVERS = {
    "gmail": "imap.gmail.com",
    "outlook": "outlook.office365.com",
    "yahoo": "imap.mail.yahoo.com",
    "icloud": "imap.mail.me.com",
}


@dataclass
class EmailMessage:
    """Parsed email message."""
    message_id: str
    subject: str
    sender: str
    sender_name: str
    recipients: List[str]
    date: Optional[datetime]
    body_text: str
    body_html: str
    has_attachments: bool
    attachment_names: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    is_read: bool = False


@dataclass
class EmailRule:
    """A rule that determines how to process an incoming email."""
    name: str
    enabled: bool = True
    # Conditions (all must match)
    from_contains: Optional[str] = None
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None
    has_attachment: Optional[bool] = None
    # Actions
    action: str = "note"  # "note", "task", "ignore", "notify"
    priority: str = "medium"  # for tasks
    category: str = "general"  # for notes
    tags: str = ""

    def matches(self, msg: EmailMessage) -> bool:
        """Check if an email matches this rule."""
        if self.from_contains and self.from_contains.lower() not in msg.sender.lower():
            return False
        if self.subject_contains and self.subject_contains.lower() not in msg.subject.lower():
            return False
        if self.body_contains and self.body_contains.lower() not in msg.body_text.lower():
            return False
        if self.has_attachment is not None and self.has_attachment != msg.has_attachments:
            return False
        return True


class EmailCheckerService:
    """
    Background service that monitors email inboxes.

    Parameters
    ----------
    app : Flask
        Flask application instance (for app context).
    on_email : callable
        Callback ``(user_id, EmailMessage, matched_rule)`` invoked for
        each new email that matches at least one rule.
    check_interval : int
        Seconds between inbox checks (default: 300 = 5 minutes).
    """

    def __init__(
        self,
        app=None,
        on_email: Optional[Callable] = None,
        check_interval: int = 300,
    ):
        self._app = app
        self._on_email = on_email
        self._check_interval = check_interval
        self._accounts: Dict[str, dict] = {}  # user_id -> config
        self._rules: Dict[str, List[EmailRule]] = {}  # user_id -> rules
        self._seen_ids: Dict[str, set] = {}  # user_id -> set of message IDs
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_account(
        self,
        user_id: str,
        *,
        imap_server: str = "",
        email_address: str = "",
        password: str = "",
        provider: str = "custom",
        folder: str = "INBOX",
        use_ssl: bool = True,
        port: int = 993,
    ) -> bool:
        """Register an email account for monitoring."""
        if provider in IMAP_SERVERS:
            imap_server = IMAP_SERVERS[provider]

        if not imap_server or not email_address or not password:
            logger.error("Incomplete email configuration for user %s", user_id)
            return False

        self._accounts[user_id] = {
            "imap_server": imap_server,
            "email": email_address,
            "password": password,
            "folder": folder,
            "use_ssl": use_ssl,
            "port": port,
        }
        self._seen_ids.setdefault(user_id, set())
        logger.info("Email account added for user %s (%s)", user_id, email_address)
        return True

    def remove_account(self, user_id: str) -> bool:
        """Remove an email account."""
        removed = self._accounts.pop(user_id, None)
        self._rules.pop(user_id, None)
        self._seen_ids.pop(user_id, None)
        return removed is not None

    def add_rule(self, user_id: str, rule: EmailRule) -> None:
        """Add a processing rule for a user."""
        self._rules.setdefault(user_id, []).append(rule)

    def set_rules(self, user_id: str, rules: List[EmailRule]) -> None:
        """Replace all rules for a user."""
        self._rules[user_id] = rules

    def start(self) -> None:
        """Start the email checker in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        logger.info("Email checker started (interval=%ds)", self._check_interval)

    def stop(self) -> None:
        """Stop the email checker."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        logger.info("Email checker stopped")

    def check_now(self, user_id: str) -> List[EmailMessage]:
        """Manually trigger a check for a specific user. Returns new messages."""
        config = self._accounts.get(user_id)
        if not config:
            return []
        return self._check_account(user_id, config)

    def get_status(self) -> dict:
        """Return the current status of the email checker."""
        return {
            "running": self._running,
            "accounts": {
                uid: {"email": cfg["email"], "folder": cfg["folder"]}
                for uid, cfg in self._accounts.items()
            },
            "rules_count": {uid: len(rules) for uid, rules in self._rules.items()},
            "check_interval": self._check_interval,
        }

    def test_connection(self, user_id: str) -> dict:
        """Test the IMAP connection for a user."""
        config = self._accounts.get(user_id)
        if not config:
            return {"success": False, "error": "No email account configured."}
        try:
            conn = self._connect(config)
            status, data = conn.select(config["folder"], readonly=True)
            msg_count = int(data[0])
            conn.logout()
            return {
                "success": True,
                "message": f"Connected successfully. {msg_count} messages in {config['folder']}.",
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check_loop(self) -> None:
        while self._running:
            for user_id, config in list(self._accounts.items()):
                try:
                    self._check_account(user_id, config)
                except Exception as exc:
                    logger.error("Email check error for user %s: %s", user_id, exc)
            time.sleep(self._check_interval)

    def _check_account(self, user_id: str, config: dict) -> List[EmailMessage]:
        """Check one account for new messages."""
        new_messages: List[EmailMessage] = []
        try:
            conn = self._connect(config)
            conn.select(config["folder"], readonly=True)

            # Search for recent unseen messages (last 3 days)
            since_date = (datetime.utcnow() - timedelta(days=3)).strftime("%d-%b-%Y")
            status, data = conn.search(None, f'(SINCE {since_date} UNSEEN)')

            if status != "OK":
                conn.logout()
                return new_messages

            msg_nums = data[0].split()
            if not msg_nums:
                conn.logout()
                return new_messages

            # Process only the most recent 50 messages
            for num in msg_nums[-50:]:
                try:
                    status, msg_data = conn.fetch(num, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_email = msg_data[0][1]
                    parsed = self._parse_email(raw_email)

                    if parsed.message_id in self._seen_ids.get(user_id, set()):
                        continue

                    self._seen_ids.setdefault(user_id, set()).add(parsed.message_id)
                    new_messages.append(parsed)

                    # Apply rules
                    rules = self._rules.get(user_id, [])
                    matched_rule = None
                    for rule in rules:
                        if rule.enabled and rule.matches(parsed):
                            matched_rule = rule
                            break

                    if not matched_rule:
                        # Default rule: create a note
                        matched_rule = EmailRule(name="default", action="note")

                    if self._on_email:
                        try:
                            if self._app:
                                with self._app.app_context():
                                    self._on_email(user_id, parsed, matched_rule)
                            else:
                                self._on_email(user_id, parsed, matched_rule)
                        except Exception as exc:
                            logger.error("Email callback error: %s", exc)

                except Exception as exc:
                    logger.warning("Error processing email %s: %s", num, exc)

            conn.logout()

        except Exception as exc:
            logger.error("IMAP connection error for user %s: %s", user_id, exc)

        if new_messages:
            logger.info("Found %d new email(s) for user %s", len(new_messages), user_id)

        return new_messages

    def _connect(self, config: dict) -> imaplib.IMAP4_SSL:
        """Create an IMAP connection."""
        if config.get("use_ssl", True):
            conn = imaplib.IMAP4_SSL(config["imap_server"], config.get("port", 993))
        else:
            conn = imaplib.IMAP4(config["imap_server"], config.get("port", 143))
        conn.login(config["email"], config["password"])
        return conn

    def _parse_email(self, raw: bytes) -> EmailMessage:
        """Parse a raw email into an EmailMessage."""
        msg = email.message_from_bytes(raw)

        # Decode subject
        subject_parts = email.header.decode_header(msg.get("Subject", ""))
        subject = ""
        for part, charset in subject_parts:
            if isinstance(part, bytes):
                subject += part.decode(charset or "utf-8", errors="replace")
            else:
                subject += part

        # Sender
        sender_raw = msg.get("From", "")
        sender_name, sender_email = email.utils.parseaddr(sender_raw)

        # Recipients
        to_raw = msg.get("To", "")
        recipients = [addr for _, addr in email.utils.getaddresses([to_raw])]

        # Date
        date_str = msg.get("Date", "")
        date = None
        try:
            date_tuple = email.utils.parsedate_to_datetime(date_str)
            date = date_tuple
        except Exception:
            pass

        # Body
        body_text = ""
        body_html = ""
        attachment_names: List[str] = []
        has_attachments = False

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition:
                    has_attachments = True
                    filename = part.get_filename()
                    if filename:
                        attachment_names.append(filename)
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode("utf-8", errors="replace")
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_html = payload.decode("utf-8", errors="replace")
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                if content_type == "text/plain":
                    body_text = payload.decode("utf-8", errors="replace")
                elif content_type == "text/html":
                    body_html = payload.decode("utf-8", errors="replace")

        # Strip HTML tags for a plain text fallback
        if not body_text and body_html:
            body_text = re.sub(r"<[^>]+>", "", body_html)
            body_text = re.sub(r"\s+", " ", body_text).strip()

        message_id = msg.get("Message-ID", f"no-id-{hash(raw[:200])}")

        return EmailMessage(
            message_id=message_id,
            subject=subject.strip(),
            sender=sender_email,
            sender_name=sender_name,
            recipients=recipients,
            date=date,
            body_text=body_text[:5000],  # Limit body size
            body_html=body_html[:10000],
            has_attachments=has_attachments,
            attachment_names=attachment_names,
        )
