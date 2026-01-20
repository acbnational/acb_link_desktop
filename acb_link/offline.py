"""
ACB Link - Offline Mode and Connectivity
Detects network connectivity and manages offline content.
"""

import json
import socket
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .utils import get_app_data_dir, get_downloads_dir


class ConnectionStatus(Enum):
    """Network connection status."""

    ONLINE = "online"
    OFFLINE = "offline"
    LIMITED = "limited"  # Connected but specific services unavailable


@dataclass
class OfflineContent:
    """Represents offline-available content."""

    id: str
    type: str  # "episode", "recording"
    name: str
    file_path: str
    size_bytes: int = 0
    duration_seconds: int = 0
    downloaded_date: str = ""
    last_played: str = ""
    # Source info
    podcast_id: str = ""
    podcast_name: str = ""


class ConnectivityMonitor:
    """
    Monitors network connectivity status.
    """

    # Test hosts
    TEST_HOSTS = [
        ("8.8.8.8", 53),  # Google DNS
        ("1.1.1.1", 53),  # Cloudflare DNS
    ]

    # ACB-specific hosts
    ACB_HOSTS = [
        ("live365.com", 80),
        ("pinecast.com", 80),
    ]

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._status = ConnectionStatus.ONLINE
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_check = datetime.now()

        # Callbacks
        self.on_status_change: Optional[Callable[[ConnectionStatus], None]] = None
        self.on_connection_lost: Optional[Callable[[], None]] = None
        self.on_connection_restored: Optional[Callable[[], None]] = None

    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status

    @property
    def is_online(self) -> bool:
        """Check if currently online."""
        return self._status == ConnectionStatus.ONLINE

    @property
    def is_offline(self) -> bool:
        """Check if currently offline."""
        return self._status == ConnectionStatus.OFFLINE

    def start_monitoring(self):
        """Start background connectivity monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="ConnectivityMonitor"
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

    def check_connection(self) -> ConnectionStatus:
        """Perform immediate connectivity check."""
        # Check general internet
        internet_ok = self._check_hosts(self.TEST_HOSTS)

        if not internet_ok:
            return ConnectionStatus.OFFLINE

        # Check ACB-specific services
        acb_ok = self._check_hosts(self.ACB_HOSTS)

        if not acb_ok:
            return ConnectionStatus.LIMITED

        return ConnectionStatus.ONLINE

    def _check_hosts(self, hosts: List[tuple]) -> bool:
        """Check if any of the hosts are reachable."""
        for host, port in hosts:
            if self._check_host(host, port):
                return True
        return False

    def _check_host(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """Check if a specific host is reachable."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except (socket.error, socket.timeout, OSError):
            return False

    def _monitor_loop(self):
        """Background monitoring loop."""
        while not self._stop_event.is_set():
            new_status = self.check_connection()
            old_status = self._status

            if new_status != old_status:
                self._status = new_status
                self._last_check = datetime.now()

                # Fire callbacks
                if self.on_status_change:
                    self.on_status_change(new_status)

                if old_status == ConnectionStatus.ONLINE and new_status == ConnectionStatus.OFFLINE:
                    if self.on_connection_lost:
                        self.on_connection_lost()
                elif (
                    old_status == ConnectionStatus.OFFLINE and new_status == ConnectionStatus.ONLINE
                ):
                    if self.on_connection_restored:
                        self.on_connection_restored()

            self._stop_event.wait(self.check_interval)


class DownloadQueue:
    """
    Smart download queue for offline content.
    Automatically downloads when online and pauses when offline.
    """

    @dataclass
    class QueueItem:
        id: str
        url: str
        output_path: str
        name: str
        priority: int = 0  # Higher = more important
        podcast_id: str = ""
        episode_id: str = ""
        status: str = "pending"  # pending, downloading, paused, completed, failed
        progress: float = 0.0
        error: str = ""

    def __init__(self, connectivity_monitor: Optional[ConnectivityMonitor] = None):
        self.connectivity = connectivity_monitor or ConnectivityMonitor()
        self._queue: List[DownloadQueue.QueueItem] = []
        self._current: Optional[DownloadQueue.QueueItem] = None
        self._queue_file = get_app_data_dir() / "download_queue.json"
        self._download_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Callbacks - use string forward reference for nested class
        self.on_item_complete: Optional[Callable[["DownloadQueue.QueueItem"], None]] = None
        self.on_item_error: Optional[Callable[["DownloadQueue.QueueItem", str], None]] = None
        self.on_progress: Optional[Callable[["DownloadQueue.QueueItem", float], None]] = None
        self.on_queue_complete: Optional[Callable[[], None]] = None

        self._load()

        # Connect to connectivity monitor
        self.connectivity.on_connection_restored = self._on_connection_restored
        self.connectivity.on_connection_lost = self._on_connection_lost

    def _load(self):
        """Load queue from disk."""
        if self._queue_file.exists():
            try:
                with open(self._queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for item_data in data.get("queue", []):
                    self._queue.append(DownloadQueue.QueueItem(**item_data))
            except Exception:
                pass

    def _save(self):
        """Save queue to disk."""
        try:
            data = {"queue": [asdict(item) for item in self._queue]}
            with open(self._queue_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def add(
        self,
        url: str,
        output_path: str,
        name: str,
        priority: int = 0,
        podcast_id: str = "",
        episode_id: str = "",
    ) -> QueueItem:
        """Add item to download queue."""
        import uuid

        item = DownloadQueue.QueueItem(
            id=uuid.uuid4().hex[:12],
            url=url,
            output_path=output_path,
            name=name,
            priority=priority,
            podcast_id=podcast_id,
            episode_id=episode_id,
        )

        # Insert by priority
        inserted = False
        for i, existing in enumerate(self._queue):
            if item.priority > existing.priority:
                self._queue.insert(i, item)
                inserted = True
                break

        if not inserted:
            self._queue.append(item)

        self._save()

        # Start processing if online
        if self.connectivity.is_online:
            self._start_processing()

        return item

    def remove(self, item_id: str) -> bool:
        """Remove item from queue."""
        for i, item in enumerate(self._queue):
            if item.id == item_id:
                self._queue.pop(i)
                self._save()
                return True
        return False

    def get_queue(self) -> List[QueueItem]:
        """Get all items in queue."""
        return self._queue.copy()

    def clear(self):
        """Clear the queue."""
        self._queue.clear()
        self._save()

    def _start_processing(self):
        """Start processing the queue."""
        if self._download_thread and self._download_thread.is_alive():
            return

        if not self._queue:
            return

        self._stop_event.clear()
        self._download_thread = threading.Thread(
            target=self._process_queue, daemon=True, name="DownloadQueueProcessor"
        )
        self._download_thread.start()

    def _stop_processing(self):
        """Stop processing (pause downloads)."""
        self._stop_event.set()
        if self._current:
            self._current.status = "paused"

    def _process_queue(self):
        """Process queue in background."""
        try:
            import requests
        except ImportError:
            return

        while not self._stop_event.is_set() and self._queue:
            if not self.connectivity.is_online:
                time.sleep(5)
                continue

            # Get next item
            pending = [i for i in self._queue if i.status in ["pending", "paused"]]
            if not pending:
                break

            item = pending[0]
            self._current = item
            item.status = "downloading"

            try:
                # Ensure directory exists
                Path(item.output_path).parent.mkdir(parents=True, exist_ok=True)

                # Download with progress
                response = requests.get(item.url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(item.output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            item.status = "paused"
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                item.progress = downloaded / total_size
                                if self.on_progress:
                                    self.on_progress(item, item.progress)

                item.status = "completed"
                item.progress = 1.0

                # Remove from queue
                self._queue.remove(item)
                self._save()

                if self.on_item_complete:
                    self.on_item_complete(item)

            except Exception as e:
                item.status = "failed"
                item.error = str(e)

                if self.on_item_error:
                    self.on_item_error(item, str(e))

            finally:
                self._current = None

        # Queue complete
        if not self._queue and self.on_queue_complete:
            self.on_queue_complete()

    def _on_connection_restored(self):
        """Handle connection restored."""
        self._start_processing()

    def _on_connection_lost(self):
        """Handle connection lost."""
        self._stop_processing()


class OfflineManager:
    """
    Manages offline content and synchronization.
    """

    def __init__(self):
        self._data_file = get_app_data_dir() / "offline_content.json"
        self.content: Dict[str, OfflineContent] = {}
        self.connectivity = ConnectivityMonitor()
        self.download_queue = DownloadQueue(self.connectivity)

        # Sync queue for when back online
        self._sync_queue: List[Dict[str, Any]] = []

        # Callbacks
        self.on_offline_mode_entered: Optional[Callable[[], None]] = None
        self.on_online_mode_entered: Optional[Callable[[], None]] = None

        self._load()

        # Set up connectivity callbacks
        self.connectivity.on_connection_lost = self._on_connection_lost
        self.connectivity.on_connection_restored = self._on_connection_restored

    def _load(self):
        """Load offline content registry."""
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for item_data in data.get("content", []):
                    item = OfflineContent(**item_data)
                    self.content[item.id] = item
            except Exception:
                pass

    def _save(self):
        """Save offline content registry."""
        try:
            data = {"content": [asdict(c) for c in self.content.values()]}
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def start(self):
        """Start offline manager."""
        self.connectivity.start_monitoring()

    def stop(self):
        """Stop offline manager."""
        self.connectivity.stop_monitoring()

    @property
    def is_offline(self) -> bool:
        """Check if currently offline."""
        return self.connectivity.is_offline

    @property
    def is_online(self) -> bool:
        """Check if currently online."""
        return self.connectivity.is_online

    def register_content(
        self,
        content_id: str,
        content_type: str,
        name: str,
        file_path: str,
        podcast_id: str = "",
        podcast_name: str = "",
        duration_seconds: int = 0,
    ):
        """Register content as available offline."""
        import os

        size_bytes = 0
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)

        self.content[content_id] = OfflineContent(
            id=content_id,
            type=content_type,
            name=name,
            file_path=file_path,
            size_bytes=size_bytes,
            duration_seconds=duration_seconds,
            downloaded_date=datetime.now().isoformat(),
            podcast_id=podcast_id,
            podcast_name=podcast_name,
        )
        self._save()

    def unregister_content(self, content_id: str) -> bool:
        """Remove content from offline registry."""
        if content_id in self.content:
            del self.content[content_id]
            self._save()
            return True
        return False

    def is_available_offline(self, content_id: str) -> bool:
        """Check if content is available offline."""
        if content_id not in self.content:
            return False

        # Verify file exists
        import os

        return os.path.exists(self.content[content_id].file_path)

    def get_offline_content(self) -> List[OfflineContent]:
        """Get all offline content."""
        # Verify files still exist
        valid_content = []
        import os

        for content in self.content.values():
            if os.path.exists(content.file_path):
                valid_content.append(content)

        return valid_content

    def get_offline_path(self, content_id: str) -> Optional[str]:
        """Get file path for offline content."""
        if content_id in self.content:
            return self.content[content_id].file_path
        return None

    def get_total_offline_size(self) -> int:
        """Get total size of offline content in bytes."""
        return sum(c.size_bytes for c in self.content.values())

    def cleanup_orphaned_files(self):
        """Remove registry entries for files that no longer exist."""
        import os

        to_remove = []

        for content_id, content in self.content.items():
            if not os.path.exists(content.file_path):
                to_remove.append(content_id)

        for content_id in to_remove:
            del self.content[content_id]

        if to_remove:
            self._save()

    def queue_for_sync(self, action: str, data: Dict[str, Any]):
        """Queue an action to sync when back online."""
        self._sync_queue.append(
            {"action": action, "data": data, "queued_at": datetime.now().isoformat()}
        )

    def _on_connection_lost(self):
        """Handle connection lost."""
        if self.on_offline_mode_entered:
            self.on_offline_mode_entered()

    def _on_connection_restored(self):
        """Handle connection restored."""
        # Process sync queue
        self._process_sync_queue()

        if self.on_online_mode_entered:
            self.on_online_mode_entered()

    def _process_sync_queue(self):
        """Process queued sync actions."""
        while self._sync_queue:
            _item = self._sync_queue.pop(0)
            # Process based on action type
            # This would be implemented based on what needs syncing
            pass


class StorageManager:
    """
    Manages storage space for offline content.
    """

    def __init__(self, max_storage_mb: int = 2000):
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        self._storage_dir = get_downloads_dir()

    def get_used_storage(self) -> int:
        """Get used storage in bytes."""
        total = 0
        for file in self._storage_dir.rglob("*"):
            if file.is_file():
                total += file.stat().st_size
        return total

    def get_available_storage(self) -> int:
        """Get available storage in bytes."""
        return max(0, self.max_storage_bytes - self.get_used_storage())

    def get_storage_percentage(self) -> float:
        """Get storage usage as percentage."""
        used = self.get_used_storage()
        return (used / self.max_storage_bytes) * 100 if self.max_storage_bytes > 0 else 0

    def can_store(self, size_bytes: int) -> bool:
        """Check if there's room for a file."""
        return self.get_available_storage() >= size_bytes

    def cleanup_old_content(self, target_free_bytes: Optional[int] = None) -> int:
        """
        Remove oldest content to free space.

        Returns:
            Number of bytes freed
        """
        if target_free_bytes is None:
            target_free_bytes = self.max_storage_bytes // 4  # Free 25%

        # Get all files sorted by modification time
        files = []
        for file in self._storage_dir.rglob("*"):
            if file.is_file():
                files.append((file, file.stat().st_mtime, file.stat().st_size))

        # Sort oldest first
        files.sort(key=lambda x: x[1])

        freed = 0
        for file, _, size in files:
            if freed >= target_free_bytes:
                break

            try:
                file.unlink()
                freed += size
            except Exception:
                pass

        return freed
