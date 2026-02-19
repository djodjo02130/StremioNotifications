from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class LibraryItem:
    imdb_id: str
    name: str
    item_type: str  # "series" or "movie"


@dataclass
class VideoRelease:
    imdb_id: str
    name: str
    item_type: str
    release_date: date
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_name: Optional[str] = None

    @property
    def event_key(self) -> str:
        if self.item_type == "series" and self.season is not None and self.episode is not None:
            return f"{self.imdb_id}:S{self.season:02d}E{self.episode:02d}"
        return self.imdb_id

    @property
    def summary(self) -> str:
        if self.item_type == "series" and self.season is not None and self.episode is not None:
            title = f"{self.name} S{self.season:02d}E{self.episode:02d}"
            if self.episode_name:
                title += f" - {self.episode_name}"
            return f"New Episode: {title}"
        return f"New Movie: {self.name}"

    @property
    def description(self) -> str:
        lines = [f"Type: {'Series' if self.item_type == 'series' else 'Movie'}"]
        if self.item_type == "series" and self.season is not None and self.episode is not None:
            lines.append(f"Season {self.season}, Episode {self.episode}")
        lines.append(f"IMDb: https://www.imdb.com/title/{self.imdb_id}/")
        return "\n".join(lines)


@dataclass
class CreatedEvent:
    event_key: str
    created_date: str  # ISO format date string
