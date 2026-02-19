import json
import logging
import os
from dataclasses import dataclass, field
from typing import List

OPTIONS_PATH = "/data/options.json"

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


@dataclass
class AppConfig:
    stremio_email: str
    stremio_password: str
    check_interval_hours: int = 6
    calendar_entity: str = "calendar.stremio_releases"
    days_ahead: int = 14
    content_types: List[str] = field(default_factory=lambda: ["series", "movies"])
    log_level: str = "info"
    supervisor_token: str = ""
    ha_base_url: str = "http://supervisor/core"

    @property
    def log_level_int(self) -> int:
        return LOG_LEVELS.get(self.log_level, logging.INFO)


def load_config() -> AppConfig:
    with open(OPTIONS_PATH, "r") as f:
        options = json.load(f)

    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", "")

    return AppConfig(
        stremio_email=options["stremio_email"],
        stremio_password=options["stremio_password"],
        check_interval_hours=options.get("check_interval_hours", 6),
        calendar_entity=options.get("calendar_entity", "calendar.stremio_releases"),
        days_ahead=options.get("days_ahead", 14),
        content_types=options.get("content_types", ["series", "movies"]),
        log_level=options.get("log_level", "info"),
        supervisor_token=supervisor_token,
    )
