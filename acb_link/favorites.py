"""
ACB Link - Favorites and Bookmarks System
Manages favorite streams, podcasts, and episode bookmarks.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List

from .utils import get_app_data_dir


class FavoriteType(Enum):
    """Types of favorite items."""

    STREAM = "stream"
    PODCAST = "podcast"
    EPISODE = "episode"
    BOOKMARK = "bookmark"


@dataclass
class Favorite:
    """Represents a favorite item."""

    id: str
    type: FavoriteType
    name: str
    url: str = ""
    added_date: str = ""
    # Additional metadata
    category: str = ""
    podcast_id: str = ""
    episode_id: str = ""
    description: str = ""
    image_url: str = ""

    def __post_init__(self):
        if not self.added_date:
            self.added_date = datetime.now().isoformat()


@dataclass
class Bookmark:
    """Represents a position bookmark in an episode."""

    id: str
    episode_id: str
    podcast_id: str
    episode_name: str
    podcast_name: str
    position: float  # seconds
    note: str = ""
    created_date: str = ""

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

    def get_position_str(self) -> str:
        """Get formatted position string."""
        mins = int(self.position) // 60
        secs = int(self.position) % 60
        hours = mins // 60
        mins = mins % 60

        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


class FavoritesManager:
    """
    Manages favorites and bookmarks for ACB Link.
    Supports streams, podcasts, episodes, and position bookmarks.
    """

    def __init__(self):
        self._data_file = get_app_data_dir() / "favorites.json"
        self.favorites: Dict[str, Favorite] = {}
        self.bookmarks: Dict[str, Bookmark] = {}

        self._load()

    def _load(self):
        """Load favorites from disk."""
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for fav_data in data.get("favorites", []):
                    fav_data["type"] = FavoriteType(fav_data["type"])
                    fav = Favorite(**fav_data)
                    self.favorites[fav.id] = fav

                for bm_data in data.get("bookmarks", []):
                    bm = Bookmark(**bm_data)
                    self.bookmarks[bm.id] = bm

            except Exception:
                pass

    def _save(self):
        """Save favorites to disk."""
        try:
            data = {
                "favorites": [{**asdict(f), "type": f.type.value} for f in self.favorites.values()],
                "bookmarks": [asdict(b) for b in self.bookmarks.values()],
            }

            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # Favorite Streams

    def add_stream_favorite(self, stream_id: str, name: str, station_id: str = "") -> Favorite:
        """Add a stream to favorites."""
        fav = Favorite(
            id=f"stream_{stream_id}",
            type=FavoriteType.STREAM,
            name=name,
            url=f"https://streaming.live365.com/{station_id}" if station_id else "",
        )
        self.favorites[fav.id] = fav
        self._save()
        return fav

    def remove_stream_favorite(self, stream_id: str) -> bool:
        """Remove a stream from favorites."""
        fav_id = f"stream_{stream_id}"
        if fav_id in self.favorites:
            del self.favorites[fav_id]
            self._save()
            return True
        return False

    def is_stream_favorite(self, stream_id: str) -> bool:
        """Check if a stream is a favorite."""
        return f"stream_{stream_id}" in self.favorites

    def get_favorite_streams(self) -> List[Favorite]:
        """Get all favorite streams."""
        return [f for f in self.favorites.values() if f.type == FavoriteType.STREAM]

    # Favorite Podcasts

    def add_podcast_favorite(
        self,
        podcast_id: str,
        name: str,
        feed_url: str = "",
        category: str = "",
        image_url: str = "",
    ) -> Favorite:
        """Add a podcast to favorites."""
        fav = Favorite(
            id=f"podcast_{podcast_id}",
            type=FavoriteType.PODCAST,
            name=name,
            url=feed_url,
            category=category,
            podcast_id=podcast_id,
            image_url=image_url,
        )
        self.favorites[fav.id] = fav
        self._save()
        return fav

    def remove_podcast_favorite(self, podcast_id: str) -> bool:
        """Remove a podcast from favorites."""
        fav_id = f"podcast_{podcast_id}"
        if fav_id in self.favorites:
            del self.favorites[fav_id]
            self._save()
            return True
        return False

    def is_podcast_favorite(self, podcast_id: str) -> bool:
        """Check if a podcast is a favorite."""
        return f"podcast_{podcast_id}" in self.favorites

    def get_favorite_podcasts(self) -> List[Favorite]:
        """Get all favorite podcasts."""
        return [f for f in self.favorites.values() if f.type == FavoriteType.PODCAST]

    # Favorite Episodes

    def add_episode_favorite(
        self, episode_id: str, episode_name: str, podcast_id: str, podcast_name: str, url: str = ""
    ) -> Favorite:
        """Add an episode to favorites."""
        fav = Favorite(
            id=f"episode_{episode_id}",
            type=FavoriteType.EPISODE,
            name=episode_name,
            url=url,
            podcast_id=podcast_id,
            episode_id=episode_id,
            description=f"From: {podcast_name}",
        )
        self.favorites[fav.id] = fav
        self._save()
        return fav

    def remove_episode_favorite(self, episode_id: str) -> bool:
        """Remove an episode from favorites."""
        fav_id = f"episode_{episode_id}"
        if fav_id in self.favorites:
            del self.favorites[fav_id]
            self._save()
            return True
        return False

    def is_episode_favorite(self, episode_id: str) -> bool:
        """Check if an episode is a favorite."""
        return f"episode_{episode_id}" in self.favorites

    def get_favorite_episodes(self) -> List[Favorite]:
        """Get all favorite episodes."""
        return [f for f in self.favorites.values() if f.type == FavoriteType.EPISODE]

    # Bookmarks

    def add_bookmark(
        self,
        episode_id: str,
        podcast_id: str,
        episode_name: str,
        podcast_name: str,
        position: float,
        note: str = "",
    ) -> Bookmark:
        """Add a position bookmark."""
        bookmark_id = f"bm_{episode_id}_{int(position)}"
        bookmark = Bookmark(
            id=bookmark_id,
            episode_id=episode_id,
            podcast_id=podcast_id,
            episode_name=episode_name,
            podcast_name=podcast_name,
            position=position,
            note=note,
        )
        self.bookmarks[bookmark_id] = bookmark
        self._save()
        return bookmark

    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove a bookmark."""
        if bookmark_id in self.bookmarks:
            del self.bookmarks[bookmark_id]
            self._save()
            return True
        return False

    def get_bookmarks_for_episode(self, episode_id: str) -> List[Bookmark]:
        """Get all bookmarks for an episode."""
        return [b for b in self.bookmarks.values() if b.episode_id == episode_id]

    def get_all_bookmarks(self) -> List[Bookmark]:
        """Get all bookmarks sorted by date."""
        return sorted(self.bookmarks.values(), key=lambda b: b.created_date, reverse=True)

    # General

    def get_all_favorites(self) -> List[Favorite]:
        """Get all favorites sorted by date."""
        return sorted(self.favorites.values(), key=lambda f: f.added_date, reverse=True)

    def search_favorites(self, query: str) -> List[Favorite]:
        """Search favorites by name."""
        query = query.lower()
        return [
            f
            for f in self.favorites.values()
            if query in f.name.lower() or query in f.description.lower()
        ]

    def clear_all_favorites(self):
        """Clear all favorites (but not bookmarks)."""
        self.favorites.clear()
        self._save()

    def clear_all_bookmarks(self):
        """Clear all bookmarks."""
        self.bookmarks.clear()
        self._save()

    # Import/Export

    def export_to_file(self, filepath: str) -> bool:
        """Export favorites and bookmarks to a file."""
        try:
            data = {
                "version": "1.0",
                "exported_date": datetime.now().isoformat(),
                "favorites": [{**asdict(f), "type": f.type.value} for f in self.favorites.values()],
                "bookmarks": [asdict(b) for b in self.bookmarks.values()],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def import_from_file(self, filepath: str, merge: bool = True) -> bool:
        """
        Import favorites and bookmarks from a file.

        Args:
            filepath: Path to import file
            merge: If True, merge with existing; if False, replace

        Returns:
            True if import succeeded
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not merge:
                self.favorites.clear()
                self.bookmarks.clear()

            for fav_data in data.get("favorites", []):
                fav_data["type"] = FavoriteType(fav_data["type"])
                fav = Favorite(**fav_data)
                self.favorites[fav.id] = fav

            for bm_data in data.get("bookmarks", []):
                bm = Bookmark(**bm_data)
                self.bookmarks[bm.id] = bm

            self._save()
            return True
        except Exception:
            return False

    def get_quick_access_items(self, limit: int = 10) -> List[Favorite]:
        """Get items for quick access display on Home tab."""
        # Return a mix of recent favorites
        all_favs = self.get_all_favorites()
        return all_favs[:limit]
