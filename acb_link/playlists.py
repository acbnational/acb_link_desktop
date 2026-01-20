"""
ACB Link - Playlist Management
Create, manage, and play custom playlists mixing streams and episodes.
"""

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from .utils import get_app_data_dir


class PlaylistItemType(Enum):
    """Types of items in a playlist."""

    STREAM = "stream"
    EPISODE = "episode"
    LOCAL_FILE = "local_file"


class RepeatMode(Enum):
    """Playlist repeat modes."""

    NONE = "none"
    ONE = "one"  # Repeat current item
    ALL = "all"  # Repeat entire playlist


@dataclass
class PlaylistItem:
    """Represents an item in a playlist."""

    id: str
    type: PlaylistItemType
    name: str
    url: str
    duration: int = 0  # seconds
    # Source info
    source_id: str = ""  # stream_id, episode_id, or file path
    podcast_id: str = ""
    podcast_name: str = ""
    # Playback state
    played: bool = False
    play_count: int = 0
    last_played: str = ""

    @staticmethod
    def create_id() -> str:
        """Generate a unique item ID."""
        return uuid.uuid4().hex[:12]


@dataclass
class Playlist:
    """Represents a playlist."""

    id: str
    name: str
    description: str = ""
    items: List[PlaylistItem] = field(default_factory=list)
    created_date: str = ""
    modified_date: str = ""
    # Settings
    is_smart: bool = False  # Auto-playlist
    smart_type: str = ""  # "recent", "most_played", "unplayed"
    shuffle: bool = False
    repeat: RepeatMode = RepeatMode.NONE

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.modified_date:
            self.modified_date = self.created_date

    @staticmethod
    def create_id() -> str:
        """Generate a unique playlist ID."""
        return uuid.uuid4().hex[:12]

    @property
    def total_duration(self) -> int:
        """Get total playlist duration in seconds."""
        return sum(item.duration for item in self.items)

    @property
    def item_count(self) -> int:
        """Get number of items in playlist."""
        return len(self.items)

    def get_duration_str(self) -> str:
        """Get formatted total duration."""
        total = self.total_duration
        hours = total // 3600
        mins = (total % 3600) // 60

        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins} min"


class PlaylistPlayer:
    """
    Handles playlist playback logic.
    """

    def __init__(self, on_item_change: Optional[Callable] = None):
        self.current_playlist: Optional[Playlist] = None
        self.current_index: int = 0
        self._shuffled_indices: List[int] = []
        self._is_shuffled: bool = False
        self.on_item_change = on_item_change

    def load_playlist(self, playlist: Playlist):
        """Load a playlist for playback."""
        self.current_playlist = playlist
        self.current_index = 0
        self._is_shuffled = playlist.shuffle

        if self._is_shuffled:
            self._generate_shuffle_order()

    def _generate_shuffle_order(self):
        """Generate shuffled playback order."""
        if self.current_playlist:
            self._shuffled_indices = list(range(len(self.current_playlist.items)))
            random.shuffle(self._shuffled_indices)

    def _get_actual_index(self, logical_index: int) -> int:
        """Get actual item index from logical index."""
        if self._is_shuffled and self._shuffled_indices:
            if 0 <= logical_index < len(self._shuffled_indices):
                return self._shuffled_indices[logical_index]
        return logical_index

    @property
    def current_item(self) -> Optional[PlaylistItem]:
        """Get current playlist item."""
        if not self.current_playlist or not self.current_playlist.items:
            return None

        actual_idx = self._get_actual_index(self.current_index)
        if 0 <= actual_idx < len(self.current_playlist.items):
            return self.current_playlist.items[actual_idx]
        return None

    def next_item(self) -> Optional[PlaylistItem]:
        """Move to and return next item."""
        if not self.current_playlist:
            return None

        items = self.current_playlist.items
        if not items:
            return None

        # Handle repeat one
        if self.current_playlist.repeat == RepeatMode.ONE:
            return self.current_item

        # Move to next
        self.current_index += 1

        # Handle end of playlist
        if self.current_index >= len(items):
            if self.current_playlist.repeat == RepeatMode.ALL:
                self.current_index = 0
                if self._is_shuffled:
                    self._generate_shuffle_order()
            else:
                self.current_index = len(items) - 1
                return None

        item = self.current_item
        if self.on_item_change and item:
            self.on_item_change(item)
        return item

    def previous_item(self) -> Optional[PlaylistItem]:
        """Move to and return previous item."""
        if not self.current_playlist or not self.current_playlist.items:
            return None

        self.current_index = max(0, self.current_index - 1)

        item = self.current_item
        if self.on_item_change and item:
            self.on_item_change(item)
        return item

    def jump_to(self, index: int) -> Optional[PlaylistItem]:
        """Jump to specific index."""
        if not self.current_playlist or not self.current_playlist.items:
            return None

        if 0 <= index < len(self.current_playlist.items):
            self.current_index = index
            item = self.current_item
            if self.on_item_change and item:
                self.on_item_change(item)
            return item
        return None

    def set_shuffle(self, enabled: bool):
        """Enable or disable shuffle."""
        self._is_shuffled = enabled
        if self.current_playlist:
            self.current_playlist.shuffle = enabled

        if enabled:
            self._generate_shuffle_order()

    def set_repeat(self, mode: RepeatMode):
        """Set repeat mode."""
        if self.current_playlist:
            self.current_playlist.repeat = mode

    def has_next(self) -> bool:
        """Check if there's a next item."""
        if not self.current_playlist:
            return False

        if self.current_playlist.repeat in [RepeatMode.ONE, RepeatMode.ALL]:
            return True

        return self.current_index < len(self.current_playlist.items) - 1

    def has_previous(self) -> bool:
        """Check if there's a previous item."""
        return self.current_index > 0


class PlaylistManager:
    """
    Manages playlists for ACB Link.
    """

    def __init__(self):
        self._data_file = get_app_data_dir() / "playlists.json"
        self.playlists: Dict[str, Playlist] = {}
        self.player = PlaylistPlayer()

        self._load()
        self._ensure_smart_playlists()

    def _load(self):
        """Load playlists from disk."""
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for pl_data in data.get("playlists", []):
                    items = []
                    for item_data in pl_data.pop("items", []):
                        item_data["type"] = PlaylistItemType(item_data["type"])
                        items.append(PlaylistItem(**item_data))

                    pl_data["repeat"] = RepeatMode(pl_data.get("repeat", "none"))
                    playlist = Playlist(**pl_data, items=items)
                    self.playlists[playlist.id] = playlist

            except Exception:
                pass

    def _save(self):
        """Save playlists to disk."""
        try:
            data = {
                "playlists": [
                    {
                        **{k: v for k, v in asdict(pl).items() if k != "items"},
                        "repeat": pl.repeat.value,
                        "items": [{**asdict(item), "type": item.type.value} for item in pl.items],
                    }
                    for pl in self.playlists.values()
                ]
            }

            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _ensure_smart_playlists(self):
        """Ensure smart playlists exist."""
        smart_playlists = [
            ("recent", "Recently Played", "Your recently played items"),
            ("most_played", "Most Played", "Your most frequently played items"),
            ("unplayed", "Unplayed Episodes", "Episodes you haven't listened to yet"),
        ]

        for smart_type, name, desc in smart_playlists:
            pl_id = f"smart_{smart_type}"
            if pl_id not in self.playlists:
                self.playlists[pl_id] = Playlist(
                    id=pl_id, name=name, description=desc, is_smart=True, smart_type=smart_type
                )
        self._save()

    def create_playlist(self, name: str, description: str = "") -> Playlist:
        """Create a new playlist."""
        playlist = Playlist(id=Playlist.create_id(), name=name, description=description)
        self.playlists[playlist.id] = playlist
        self._save()
        return playlist

    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        if playlist_id in self.playlists and not playlist_id.startswith("smart_"):
            del self.playlists[playlist_id]
            self._save()
            return True
        return False

    def rename_playlist(self, playlist_id: str, new_name: str) -> bool:
        """Rename a playlist."""
        if playlist_id in self.playlists:
            self.playlists[playlist_id].name = new_name
            self.playlists[playlist_id].modified_date = datetime.now().isoformat()
            self._save()
            return True
        return False

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get a playlist by ID."""
        return self.playlists.get(playlist_id)

    def get_all_playlists(self) -> List[Playlist]:
        """Get all playlists (excluding smart playlists)."""
        return [pl for pl in self.playlists.values() if not pl.is_smart]

    def get_smart_playlists(self) -> List[Playlist]:
        """Get all smart playlists."""
        return [pl for pl in self.playlists.values() if pl.is_smart]

    # Item Management

    def add_stream_to_playlist(
        self, playlist_id: str, stream_name: str, stream_url: str, stream_id: str = ""
    ) -> Optional[PlaylistItem]:
        """Add a stream to a playlist."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return None

        item = PlaylistItem(
            id=PlaylistItem.create_id(),
            type=PlaylistItemType.STREAM,
            name=stream_name,
            url=stream_url,
            source_id=stream_id,
        )
        playlist.items.append(item)
        playlist.modified_date = datetime.now().isoformat()
        self._save()
        return item

    def add_episode_to_playlist(
        self,
        playlist_id: str,
        episode_name: str,
        episode_url: str,
        episode_id: str,
        podcast_id: str,
        podcast_name: str,
        duration: int = 0,
    ) -> Optional[PlaylistItem]:
        """Add a podcast episode to a playlist."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return None

        item = PlaylistItem(
            id=PlaylistItem.create_id(),
            type=PlaylistItemType.EPISODE,
            name=episode_name,
            url=episode_url,
            duration=duration,
            source_id=episode_id,
            podcast_id=podcast_id,
            podcast_name=podcast_name,
        )
        playlist.items.append(item)
        playlist.modified_date = datetime.now().isoformat()
        self._save()
        return item

    def add_local_file_to_playlist(
        self, playlist_id: str, file_path: str, name: str = "", duration: int = 0
    ) -> Optional[PlaylistItem]:
        """Add a local file to a playlist."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return None

        import os

        if not name:
            name = os.path.basename(file_path)

        item = PlaylistItem(
            id=PlaylistItem.create_id(),
            type=PlaylistItemType.LOCAL_FILE,
            name=name,
            url=file_path,
            duration=duration,
            source_id=file_path,
        )
        playlist.items.append(item)
        playlist.modified_date = datetime.now().isoformat()
        self._save()
        return item

    def remove_item_from_playlist(self, playlist_id: str, item_id: str) -> bool:
        """Remove an item from a playlist."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return False

        for i, item in enumerate(playlist.items):
            if item.id == item_id:
                playlist.items.pop(i)
                playlist.modified_date = datetime.now().isoformat()
                self._save()
                return True
        return False

    def move_item(self, playlist_id: str, item_id: str, new_index: int) -> bool:
        """Move an item to a new position."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return False

        for i, item in enumerate(playlist.items):
            if item.id == item_id:
                playlist.items.pop(i)
                playlist.items.insert(new_index, item)
                playlist.modified_date = datetime.now().isoformat()
                self._save()
                return True
        return False

    def clear_playlist(self, playlist_id: str) -> bool:
        """Remove all items from a playlist."""
        playlist = self.playlists.get(playlist_id)
        if not playlist or playlist.is_smart:
            return False

        playlist.items.clear()
        playlist.modified_date = datetime.now().isoformat()
        self._save()
        return True

    # Smart Playlist Updates

    def update_recently_played(self, item: PlaylistItem):
        """Update the recently played smart playlist."""
        playlist = self.playlists.get("smart_recent")
        if not playlist:
            return

        # Remove if already exists
        playlist.items = [i for i in playlist.items if i.source_id != item.source_id]

        # Add to front
        item.last_played = datetime.now().isoformat()
        item.play_count += 1
        playlist.items.insert(0, item)

        # Keep only last 50
        playlist.items = playlist.items[:50]
        self._save()

    def update_most_played(self, item: PlaylistItem):
        """Update the most played smart playlist."""
        playlist = self.playlists.get("smart_most_played")
        if not playlist:
            return

        # Find existing or add
        existing = None
        for i in playlist.items:
            if i.source_id == item.source_id:
                existing = i
                break

        if existing:
            existing.play_count += 1
        else:
            item.play_count = 1
            playlist.items.append(item)

        # Sort by play count
        playlist.items.sort(key=lambda x: x.play_count, reverse=True)

        # Keep top 50
        playlist.items = playlist.items[:50]
        self._save()

    # Import/Export

    def export_playlist(self, playlist_id: str, filepath: str) -> bool:
        """Export a playlist to a file."""
        playlist = self.playlists.get(playlist_id)
        if not playlist:
            return False

        try:
            data = {
                "version": "1.0",
                "name": playlist.name,
                "description": playlist.description,
                "exported_date": datetime.now().isoformat(),
                "items": [{**asdict(item), "type": item.type.value} for item in playlist.items],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def import_playlist(self, filepath: str, name: str = "") -> Optional[Playlist]:
        """Import a playlist from a file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            playlist = self.create_playlist(
                name=name or data.get("name", "Imported Playlist"),
                description=data.get("description", ""),
            )

            for item_data in data.get("items", []):
                item_data["type"] = PlaylistItemType(item_data["type"])
                item_data["id"] = PlaylistItem.create_id()  # New ID
                playlist.items.append(PlaylistItem(**item_data))

            self._save()
            return playlist
        except Exception:
            return None
