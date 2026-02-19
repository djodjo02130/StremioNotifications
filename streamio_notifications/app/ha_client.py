import logging
from datetime import timedelta

import requests

from models import VideoRelease

logger = logging.getLogger(__name__)


class HAClient:
    def __init__(self, base_url: str, supervisor_token: str, calendar_entity: str):
        self._base_url = base_url.rstrip("/")
        self._calendar_entity = calendar_entity
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {supervisor_token}",
            "Content-Type": "application/json",
        })

    def check_connection(self) -> None:
        logger.info("Checking Home Assistant API connection")
        resp = self._session.get(f"{self._base_url}/api/", timeout=10)
        resp.raise_for_status()
        logger.info("Home Assistant API is reachable")

    def create_calendar_event(self, release: VideoRelease) -> None:
        url = f"{self._base_url}/api/services/calendar/create_event"
        start_date = release.release_date.isoformat()
        end_date = (release.release_date + timedelta(days=1)).isoformat()

        payload = {
            "entity_id": self._calendar_entity,
            "summary": release.summary,
            "description": release.description,
            "start_date": start_date,
            "end_date": end_date,
        }

        logger.debug("Creating calendar event: %s on %s with payload: %s", release.summary, start_date, payload)
        resp = self._session.post(url, json=payload, timeout=10)
        logger.debug("HA API response: %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
        logger.info("Created calendar event: %s", release.summary)

    def close(self) -> None:
        self._session.close()
