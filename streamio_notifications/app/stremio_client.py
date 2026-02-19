import logging
from typing import List, Optional

import requests

from models import LibraryItem

logger = logging.getLogger(__name__)

STREMIO_API_BASE = "https://api.strem.io/api"
LOGIN_URL = f"{STREMIO_API_BASE}/login"
DATASTORE_URL = f"{STREMIO_API_BASE}/datastoreGet"


class StremioClient:
    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._auth_key: Optional[str] = None
        self._session = requests.Session()

    def login(self) -> None:
        logger.info("Logging in to Stremio as %s", self._email)
        resp = self._session.post(LOGIN_URL, json={
            "type": "Login",
            "email": self._email,
            "password": self._password,
            "facebook": False,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "result" not in data or "authKey" not in data["result"]:
            error_msg = data.get("error", "Unknown error")
            raise RuntimeError(f"Stremio login failed: {error_msg}")

        self._auth_key = data["result"]["authKey"]
        logger.info("Stremio login successful")

    def get_library(self, content_types: List[str]) -> List[LibraryItem]:
        if not self._auth_key:
            raise RuntimeError("Not logged in to Stremio")

        logger.info("Fetching Stremio library")
        resp = self._session.post(DATASTORE_URL, json={
            "authKey": self._auth_key,
            "collection": "libraryItem",
            "all": True,
            "ids": [],
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "result" not in data:
            raise RuntimeError("Unexpected Stremio API response for library")

        items = []
        type_map = {"movies": "movie"}
        allowed_types = set()
        for ct in content_types:
            allowed_types.add(type_map.get(ct, ct))

        for raw in data["result"]:
            item_type = raw.get("type", "")
            if item_type not in allowed_types:
                continue
            imdb_id = raw.get("_id", "")
            name = raw.get("name", "Unknown")
            if not imdb_id.startswith("tt"):
                continue
            items.append(LibraryItem(imdb_id=imdb_id, name=name, item_type=item_type))

        logger.info("Found %d library items matching content types %s", len(items), content_types)
        return items

    def close(self) -> None:
        self._session.close()
