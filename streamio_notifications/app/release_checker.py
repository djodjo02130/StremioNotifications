import logging
import time
from datetime import date, datetime, timedelta
from typing import List

import requests

from models import LibraryItem, VideoRelease

logger = logging.getLogger(__name__)

CINEMETA_BASE = "https://v3-cinemeta.strem.io/meta"
REQUEST_DELAY = 0.5  # seconds between requests


class ReleaseChecker:
    def __init__(self, days_ahead: int):
        self._days_ahead = days_ahead
        self._session = requests.Session()

    def check_releases(self, items: List[LibraryItem]) -> List[VideoRelease]:
        releases = []
        today = date.today()
        end_date = today + timedelta(days=self._days_ahead)

        for i, item in enumerate(items):
            if i > 0:
                time.sleep(REQUEST_DELAY)
            try:
                if item.item_type == "series":
                    found = self._check_series(item, today, end_date)
                elif item.item_type == "movie":
                    found = self._check_movie(item, today, end_date)
                else:
                    continue
                releases.extend(found)
            except Exception as e:
                logger.warning("Failed to check releases for %s (%s): %s", item.name, item.imdb_id, e)

        logger.info("Found %d upcoming releases across %d items", len(releases), len(items))
        return releases

    def _check_series(self, item: LibraryItem, today: date, end_date: date) -> List[VideoRelease]:
        url = f"{CINEMETA_BASE}/series/{item.imdb_id}.json"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        meta = data.get("meta", {})
        videos = meta.get("videos", [])
        releases = []

        for video in videos:
            released_str = video.get("released")
            if not released_str:
                continue
            try:
                released_date = datetime.fromisoformat(released_str.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                continue

            if today <= released_date <= end_date:
                season = video.get("season")
                episode = video.get("number") or video.get("episode")
                if season is None or episode is None:
                    continue
                releases.append(VideoRelease(
                    imdb_id=item.imdb_id,
                    name=item.name,
                    item_type="series",
                    release_date=released_date,
                    season=int(season),
                    episode=int(episode),
                    episode_name=video.get("name") or video.get("title"),
                ))

        return releases

    def _check_movie(self, item: LibraryItem, today: date, end_date: date) -> List[VideoRelease]:
        url = f"{CINEMETA_BASE}/movie/{item.imdb_id}.json"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        meta = data.get("meta", {})
        released_str = meta.get("released")
        if not released_str:
            return []

        try:
            released_date = datetime.fromisoformat(released_str.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            return []

        if today <= released_date <= end_date:
            return [VideoRelease(
                imdb_id=item.imdb_id,
                name=item.name,
                item_type="movie",
                release_date=released_date,
            )]
        return []

    def close(self) -> None:
        self._session.close()
