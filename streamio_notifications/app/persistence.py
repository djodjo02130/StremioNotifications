import json
import logging
import os
import tempfile
from datetime import date, timedelta
from typing import Dict, Set

logger = logging.getLogger(__name__)

DATA_FILE = "/data/created_events.json"
CLEANUP_DAYS = 90


class Persistence:
    def __init__(self, path: str = DATA_FILE):
        self._path = path
        self._events: Dict[str, str] = {}  # event_key -> created_date (ISO)

    def load(self) -> None:
        if not os.path.exists(self._path):
            logger.info("No persistence file found, starting fresh")
            return
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._events = data
                logger.info("Loaded %d tracked events from persistence", len(self._events))
            else:
                logger.warning("Persistence file has unexpected format, starting fresh")
                self._events = {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Persistence file corrupted (%s), starting fresh", e)
            self._events = {}

    def save(self) -> None:
        dir_name = os.path.dirname(self._path)
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            with os.fdopen(fd, "w") as f:
                json.dump(self._events, f, indent=2)
            os.replace(tmp_path, self._path)
        except OSError as e:
            logger.error("Failed to save persistence file: %s", e)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def is_created(self, event_key: str) -> bool:
        return event_key in self._events

    def mark_created(self, event_key: str) -> None:
        self._events[event_key] = date.today().isoformat()

    def clear(self) -> None:
        self._events = {}

    def get_created_keys(self) -> Set[str]:
        return set(self._events.keys())

    def cleanup_old_entries(self) -> None:
        cutoff = (date.today() - timedelta(days=CLEANUP_DAYS)).isoformat()
        old_count = len(self._events)
        self._events = {k: v for k, v in self._events.items() if v >= cutoff}
        removed = old_count - len(self._events)
        if removed > 0:
            logger.info("Cleaned up %d old entries from persistence", removed)
