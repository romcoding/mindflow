"""
File Watcher Service for MindFlow/Rovot.

Monitors user-specified directories for new or modified files and
automatically creates notes or tasks based on the file content.

Uses the ``watchdog`` library for cross-platform file system monitoring.
For cloud deployments, this service can also poll a configured directory
at a fixed interval instead of using OS-level events.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Supported file extensions for content extraction
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log",
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css", ".xml", ".yaml", ".yml",
    ".env", ".ini", ".cfg", ".conf", ".toml",
}

# Maximum file size to process (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


class FileEvent:
    """Represents a file system event."""

    def __init__(self, path: str, event_type: str, timestamp: Optional[datetime] = None):
        self.path = path
        self.event_type = event_type  # "created", "modified", "deleted"
        self.timestamp = timestamp or datetime.utcnow()
        self.filename = os.path.basename(path)
        self.extension = os.path.splitext(path)[1].lower()

    def __repr__(self):
        return f"FileEvent({self.event_type}: {self.path})"


class FileWatcherService:
    """
    Watches directories for file changes and triggers callbacks.

    This service can operate in two modes:

    1. **Event-based** (desktop/local): Uses ``watchdog`` for real-time
       file system event monitoring.
    2. **Polling** (cloud/fallback): Periodically scans directories and
       detects changes by comparing file modification times and hashes.

    Parameters
    ----------
    app : Flask
        The Flask application instance (needed for app context).
    on_file_event : callable
        Callback invoked with ``(user_id, FileEvent, content)`` when a
        relevant file change is detected.
    poll_interval : int
        Seconds between polls in polling mode (default: 30).
    """

    def __init__(
        self,
        app=None,
        on_file_event: Optional[Callable] = None,
        poll_interval: int = 30,
    ):
        self._app = app
        self._on_file_event = on_file_event
        self._poll_interval = poll_interval
        self._watched_dirs: Dict[str, dict] = {}  # user_id -> {path, recursive, ...}
        self._file_hashes: Dict[str, str] = {}  # path -> hash
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._observer = None  # watchdog observer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_watch(self, user_id: str, directory: str, *, recursive: bool = True) -> bool:
        """Add a directory to watch for a specific user."""
        directory = os.path.expanduser(directory)
        if not os.path.isdir(directory):
            logger.warning("Directory does not exist: %s", directory)
            return False

        self._watched_dirs[user_id] = {
            "path": directory,
            "recursive": recursive,
            "added_at": datetime.utcnow().isoformat(),
        }
        logger.info("Added watch for user %s: %s (recursive=%s)", user_id, directory, recursive)

        # Index existing files
        self._index_directory(directory, recursive)
        return True

    def remove_watch(self, user_id: str) -> bool:
        """Remove a watched directory for a user."""
        if user_id in self._watched_dirs:
            del self._watched_dirs[user_id]
            logger.info("Removed watch for user %s", user_id)
            return True
        return False

    def start(self) -> None:
        """Start the file watcher in a background thread."""
        if self._running:
            return

        self._running = True

        # Try watchdog first, fall back to polling
        try:
            self._start_watchdog()
            logger.info("File watcher started (watchdog mode)")
        except ImportError:
            logger.info("watchdog not available, using polling mode")
            self._start_polling()

    def stop(self) -> None:
        """Stop the file watcher."""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("File watcher stopped")

    def get_status(self) -> dict:
        """Return the current status of the file watcher."""
        return {
            "running": self._running,
            "watched_directories": {
                uid: info["path"] for uid, info in self._watched_dirs.items()
            },
            "indexed_files": len(self._file_hashes),
            "mode": "watchdog" if self._observer else "polling",
        }

    # ------------------------------------------------------------------
    # Internal: Watchdog mode
    # ------------------------------------------------------------------

    def _start_watchdog(self) -> None:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        service = self

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    service._handle_file_change(event.src_path, "created")

            def on_modified(self, event):
                if not event.is_directory:
                    service._handle_file_change(event.src_path, "modified")

            def on_deleted(self, event):
                if not event.is_directory:
                    service._handle_file_change(event.src_path, "deleted")

        self._observer = Observer()
        handler = _Handler()

        for user_id, info in self._watched_dirs.items():
            self._observer.schedule(handler, info["path"], recursive=info.get("recursive", True))

        self._observer.daemon = True
        self._observer.start()

    # ------------------------------------------------------------------
    # Internal: Polling mode
    # ------------------------------------------------------------------

    def _start_polling(self) -> None:
        def _poll_loop():
            while self._running:
                try:
                    self._poll_once()
                except Exception as exc:
                    logger.error("File watcher poll error: %s", exc)
                time.sleep(self._poll_interval)

        self._thread = threading.Thread(target=_poll_loop, daemon=True)
        self._thread.start()

    def _poll_once(self) -> None:
        for user_id, info in list(self._watched_dirs.items()):
            directory = info["path"]
            recursive = info.get("recursive", True)

            if not os.path.isdir(directory):
                continue

            current_files: Set[str] = set()

            if recursive:
                for root, _dirs, files in os.walk(directory):
                    for f in files:
                        current_files.add(os.path.join(root, f))
            else:
                for f in os.listdir(directory):
                    fp = os.path.join(directory, f)
                    if os.path.isfile(fp):
                        current_files.add(fp)

            # Detect new or modified files
            for fp in current_files:
                ext = os.path.splitext(fp)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                try:
                    new_hash = self._file_hash(fp)
                except Exception:
                    continue

                old_hash = self._file_hashes.get(fp)
                if old_hash is None:
                    self._file_hashes[fp] = new_hash
                    self._handle_file_change(fp, "created")
                elif old_hash != new_hash:
                    self._file_hashes[fp] = new_hash
                    self._handle_file_change(fp, "modified")

            # Detect deleted files
            known = {fp for fp in self._file_hashes if fp.startswith(directory)}
            for fp in known - current_files:
                del self._file_hashes[fp]
                self._handle_file_change(fp, "deleted")

    # ------------------------------------------------------------------
    # Internal: Shared helpers
    # ------------------------------------------------------------------

    def _handle_file_change(self, path: str, event_type: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        event = FileEvent(path, event_type)
        content = None

        if event_type != "deleted":
            try:
                size = os.path.getsize(path)
                if size > MAX_FILE_SIZE:
                    logger.info("Skipping large file: %s (%d bytes)", path, size)
                    return
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except Exception as exc:
                logger.warning("Could not read file %s: %s", path, exc)
                return

        # Find the user_id for this path
        user_id = None
        for uid, info in self._watched_dirs.items():
            if path.startswith(info["path"]):
                user_id = uid
                break

        if self._on_file_event and user_id:
            try:
                if self._app:
                    with self._app.app_context():
                        self._on_file_event(user_id, event, content)
                else:
                    self._on_file_event(user_id, event, content)
            except Exception as exc:
                logger.error("File event callback error: %s", exc)

    def _index_directory(self, directory: str, recursive: bool) -> None:
        """Build initial hash index of files in a directory."""
        try:
            if recursive:
                for root, _dirs, files in os.walk(directory):
                    for f in files:
                        fp = os.path.join(root, f)
                        ext = os.path.splitext(fp)[1].lower()
                        if ext in SUPPORTED_EXTENSIONS:
                            try:
                                self._file_hashes[fp] = self._file_hash(fp)
                            except Exception:
                                pass
            else:
                for f in os.listdir(directory):
                    fp = os.path.join(directory, f)
                    if os.path.isfile(fp):
                        ext = os.path.splitext(fp)[1].lower()
                        if ext in SUPPORTED_EXTENSIONS:
                            try:
                                self._file_hashes[fp] = self._file_hash(fp)
                            except Exception:
                                pass
            logger.info("Indexed %d files in %s", len(self._file_hashes), directory)
        except Exception as exc:
            logger.error("Error indexing directory %s: %s", directory, exc)

    @staticmethod
    def _file_hash(path: str) -> str:
        """Compute a fast hash of a file's content."""
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
