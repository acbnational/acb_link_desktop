"""
ACB Link Desktop - Data Synchronization Module

Handles synchronization of data between live ACB sources and local
offline storage. Supports automatic and manual sync operations with
conflict detection and resolution.

Features:
- Download and cache live data from ACB servers
- Detect differences between live and offline data
- Merge and update offline data stores
- XML and OPML parsing for ACB data formats
- Sync status tracking and reporting
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SyncResult:
    """Result of a single data source sync operation."""
    source_name: str
    success: bool
    message: str
    items_added: int = 0
    items_updated: int = 0
    items_removed: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_changes(self) -> bool:
        """Check if sync resulted in any changes."""
        return self.items_added > 0 or self.items_updated > 0 or self.items_removed > 0


@dataclass
class SyncStatus:
    """Overall sync status for all data sources."""
    in_progress: bool = False
    last_sync: Optional[str] = None
    results: List[SyncResult] = field(default_factory=list)
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0
    
    @property
    def total_changes(self) -> int:
        """Get total number of changes across all sources."""
        return sum(r.items_added + r.items_updated + r.items_removed for r in self.results)


# =============================================================================
# XML/OPML Parsers
# =============================================================================

class StreamsParser:
    """Parser for ACB streams.xml format."""
    
    @staticmethod
    def parse(xml_content: str) -> List[Dict[str, str]]:
        """
        Parse streams XML content.
        
        Args:
            xml_content: Raw XML string.
            
        Returns:
            List of stream dictionaries.
        """
        streams = []
        try:
            root = ET.fromstring(xml_content)
            for stream in root.findall(".//Stream"):
                streams.append({
                    "name": stream.get("name", ""),
                    "website": stream.get("WebSiteAddress", ""),
                    "listen_url": stream.get("ListenURL", ""),
                })
        except ET.ParseError as e:
            logger.error(f"Failed to parse streams XML: {e}")
        return streams


class PodcastsParser:
    """Parser for ACB link.opml format."""
    
    @staticmethod
    def parse(opml_content: str) -> List[Dict[str, str]]:
        """
        Parse OPML podcast feed list.
        
        Args:
            opml_content: Raw OPML string.
            
        Returns:
            List of podcast dictionaries.
        """
        podcasts = []
        try:
            root = ET.fromstring(opml_content)
            for outline in root.findall(".//outline"):
                xml_url = outline.get("xmlUrl")
                if xml_url:
                    podcasts.append({
                        "name": outline.get("title", outline.get("text", "")),
                        "feed_url": xml_url,
                        "website": outline.get("htmlUrl", ""),
                        "type": outline.get("type", "rss"),
                    })
        except ET.ParseError as e:
            logger.error(f"Failed to parse OPML: {e}")
        return podcasts


class AffiliatesParser:
    """Parser for ACB affiliates XML (states.xml, sigs.xml)."""
    
    @staticmethod
    def parse(xml_content: str) -> List[Dict[str, str]]:
        """
        Parse affiliates XML content.
        
        Args:
            xml_content: Raw XML string.
            
        Returns:
            List of affiliate dictionaries.
        """
        affiliates = []
        try:
            root = ET.fromstring(xml_content)
            for affiliate in root.findall(".//Affiliate"):
                affiliates.append({
                    "name": affiliate.findtext("AffiliateName", ""),
                    "type": affiliate.findtext("AffiliateType", ""),
                    "state": affiliate.findtext("StateOfOrigin", ""),
                    "contact_name": affiliate.findtext("Name", ""),
                    "email": affiliate.findtext("EmailAddress", ""),
                    "phone": affiliate.findtext("PhoneNumber", ""),
                    "website": affiliate.findtext("WebSiteAddress", ""),
                    "twitter": affiliate.findtext("TwitterAddress", ""),
                    "facebook": affiliate.findtext("FacebookAddress", ""),
                })
        except ET.ParseError as e:
            logger.error(f"Failed to parse affiliates XML: {e}")
        return affiliates


class PublicationsParser:
    """Parser for ACB publications.xml format."""
    
    @staticmethod
    def parse(xml_content: str) -> List[Dict[str, str]]:
        """
        Parse publications XML content.
        
        Args:
            xml_content: Raw XML string.
            
        Returns:
            List of publication dictionaries.
        """
        publications = []
        try:
            root = ET.fromstring(xml_content)
            for pub in root.findall(".//Publication"):
                publications.append({
                    "name": pub.findtext("Name", pub.get("name", "")),
                    "url": pub.findtext("URL", pub.get("url", "")),
                    "description": pub.findtext("Description", ""),
                    "type": pub.findtext("Type", ""),
                })
        except ET.ParseError as e:
            logger.error(f"Failed to parse publications XML: {e}")
        return publications


# =============================================================================
# Data Sync Manager
# =============================================================================

class DataSyncManager:
    """
    Manages synchronization of ACB data between live sources and local cache.
    
    This class handles:
    - Downloading data from live ACB servers
    - Comparing live and cached data
    - Updating local cache files
    - Tracking sync status and history
    """
    
    def __init__(self, config=None):
        """
        Initialize the sync manager.
        
        Args:
            config: Optional AppConfig instance. Uses global config if not provided.
        """
        from .config import get_config
        self.config = config or get_config()
        self.status = SyncStatus()
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable[[str, int, int], None]] = None
        
        # Parser registry
        self._parsers = {
            "streams": StreamsParser(),
            "podcasts": PodcastsParser(),
            "state_affiliates": AffiliatesParser(),
            "special_interest_groups": AffiliatesParser(),
            "publications": PublicationsParser(),
        }
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """
        Set a callback for sync progress updates.
        
        Args:
            callback: Function(source_name, current, total) called during sync.
        """
        self._progress_callback = callback
    
    def _report_progress(self, source_name: str, current: int, total: int):
        """Report sync progress to callback if set."""
        if self._progress_callback:
            try:
                self._progress_callback(source_name, current, total)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _download_data(self, url: str) -> Optional[bytes]:
        """
        Download data from a URL.
        
        Args:
            url: The URL to download from.
            
        Returns:
            Raw bytes of the response, or None if download failed.
        """
        try:
            request = Request(
                url,
                headers={"User-Agent": self.config.network.user_agent}
            )
            
            with urlopen(request, timeout=self.config.network.timeout_seconds) as response:
                return response.read()
                
        except HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e.code} {e.reason}")
        except URLError as e:
            logger.error(f"URL error downloading {url}: {e.reason}")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
        
        return None
    
    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_offline_path(self, source_config) -> Optional[Path]:
        """Get the full path to offline data file."""
        # If no offline path configured, return None
        if not source_config.offline_path:
            return None
        
        # Check for bundled data first, then user cache
        bundled_path = self.config.get_bundled_data_path() / Path(source_config.offline_path).name
        
        if bundled_path.exists():
            return bundled_path
        
        # Fall back to cache directory
        return Path(self.config.paths.cache_dir) / Path(source_config.offline_path).name
    
    def _read_offline_data(self, source_config) -> Optional[bytes]:
        """Read offline data for a source."""
        path = self._get_offline_path(source_config)
        
        if path and path.exists():
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading offline data from {path}: {e}")
        
        return None
    
    def _write_offline_data(self, source_config, data: bytes) -> bool:
        """Write data to offline cache."""
        # If no offline path configured, store in cache with source name
        if source_config.offline_path:
            filename = Path(source_config.offline_path).name
        else:
            filename = f"{source_config.name}.xml"
        
        cache_path = Path(self.config.paths.cache_dir) / filename
        
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_path, "wb") as f:
                f.write(data)
            
            logger.info(f"Saved offline data to {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing offline data to {cache_path}: {e}")
            return False
    
    def _needs_sync(self, source_config) -> bool:
        """Check if a data source needs synchronization."""
        if source_config.last_sync is None:
            return True
        
        try:
            last_sync = datetime.fromisoformat(source_config.last_sync)
            cache_duration = timedelta(hours=source_config.cache_duration_hours)
            return datetime.now() - last_sync > cache_duration
        except (ValueError, TypeError):
            return True
    
    def sync_source(self, source_name: str, force: bool = False) -> SyncResult:
        """
        Synchronize a single data source.
        
        Args:
            source_name: Name of the data source to sync.
            force: If True, sync even if cache is fresh.
            
        Returns:
            SyncResult with details of the operation.
        """
        source_config = getattr(self.config.live_data, source_name, None)
        
        if source_config is None:
            return SyncResult(
                source_name=source_name,
                success=False,
                message=f"Unknown data source: {source_name}"
            )
        
        if not source_config.enabled:
            return SyncResult(
                source_name=source_name,
                success=True,
                message="Source is disabled"
            )
        
        if not force and not self._needs_sync(source_config):
            return SyncResult(
                source_name=source_name,
                success=True,
                message="Cache is fresh, no sync needed"
            )
        
        # Download live data
        logger.info(f"Syncing {source_name} from {source_config.live_url}")
        live_data = self._download_data(source_config.live_url)
        
        if live_data is None:
            return SyncResult(
                source_name=source_name,
                success=False,
                message="Failed to download live data"
            )
        
        # Compare with offline data
        offline_data = self._read_offline_data(source_config)
        
        if offline_data is not None:
            live_hash = self._compute_hash(live_data)
            offline_hash = self._compute_hash(offline_data)
            
            if live_hash == offline_hash:
                # Data is identical, just update timestamp
                source_config.last_sync = datetime.now().isoformat()
                return SyncResult(
                    source_name=source_name,
                    success=True,
                    message="Data is up to date"
                )
        
        # Data differs, save new version
        if self._write_offline_data(source_config, live_data):
            source_config.last_sync = datetime.now().isoformat()
            
            # Count changes if we have a parser
            items_added = 0
            items_updated = 0
            
            parser = self._parsers.get(source_name)
            if parser and offline_data:
                try:
                    old_items = parser.parse(offline_data.decode("utf-8"))
                    new_items = parser.parse(live_data.decode("utf-8"))
                    
                    old_names = {item.get("name", "") for item in old_items}
                    new_names = {item.get("name", "") for item in new_items}
                    
                    items_added = len(new_names - old_names)
                    items_updated = len(new_names & old_names)
                except Exception as e:
                    logger.warning(f"Could not count changes: {e}")
            elif not offline_data:
                # All items are new
                try:
                    parser = self._parsers.get(source_name)
                    if parser:
                        new_items = parser.parse(live_data.decode("utf-8"))
                        items_added = len(new_items)
                except Exception:
                    pass
            
            return SyncResult(
                source_name=source_name,
                success=True,
                message="Data synchronized successfully",
                items_added=items_added,
                items_updated=items_updated,
            )
        else:
            return SyncResult(
                source_name=source_name,
                success=False,
                message="Failed to save offline data"
            )
    
    def sync_all(self, force: bool = False) -> SyncStatus:
        """
        Synchronize all data sources.
        
        Args:
            force: If True, sync all sources regardless of cache freshness.
            
        Returns:
            SyncStatus with results for all sources.
        """
        with self._lock:
            if self.status.in_progress:
                logger.warning("Sync already in progress")
                return self.status
            
            self.status = SyncStatus(in_progress=True)
        
        try:
            sources = self.config.get_data_sources()
            self.status.total_sources = len(sources)
            
            for i, source in enumerate(sources):
                self._report_progress(source.name, i + 1, len(sources))
                
                result = self.sync_source(source.name, force=force)
                self.status.results.append(result)
                
                if result.success:
                    self.status.successful_sources += 1
                else:
                    self.status.failed_sources += 1
            
            self.status.last_sync = datetime.now().isoformat()
            
            # Save updated config with sync timestamps
            from .config import save_config
            save_config()
            
        finally:
            self.status.in_progress = False
        
        return self.status
    
    def get_streams(self) -> List[Dict[str, str]]:
        """Get parsed stream data from offline cache."""
        source_config = self.config.live_data.streams
        data = self._read_offline_data(source_config)
        
        if data:
            return StreamsParser.parse(data.decode("utf-8"))
        return []
    
    def get_podcasts(self) -> List[Dict[str, str]]:
        """Get parsed podcast data from offline cache."""
        source_config = self.config.live_data.podcasts
        data = self._read_offline_data(source_config)
        
        if data:
            return PodcastsParser.parse(data.decode("utf-8"))
        return []
    
    def get_state_affiliates(self) -> List[Dict[str, str]]:
        """Get parsed state affiliate data from offline cache."""
        source_config = self.config.live_data.state_affiliates
        data = self._read_offline_data(source_config)
        
        if data:
            return AffiliatesParser.parse(data.decode("utf-8"))
        return []
    
    def get_special_interest_groups(self) -> List[Dict[str, str]]:
        """Get parsed SIG data from offline cache."""
        source_config = self.config.live_data.special_interest_groups
        data = self._read_offline_data(source_config)
        
        if data:
            return AffiliatesParser.parse(data.decode("utf-8"))
        return []
    
    def is_online(self) -> bool:
        """Check if we can reach ACB servers."""
        try:
            request = Request(
                self.config.live_data.base_url,
                headers={"User-Agent": self.config.network.user_agent}
            )
            with urlopen(request, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False


# =============================================================================
# Singleton Instance
# =============================================================================

_sync_manager: Optional[DataSyncManager] = None


def get_sync_manager() -> DataSyncManager:
    """Get the global sync manager instance."""
    global _sync_manager
    
    if _sync_manager is None:
        _sync_manager = DataSyncManager()
    
    return _sync_manager


def sync_all_data(force: bool = False) -> SyncStatus:
    """Convenience function to sync all data sources."""
    return get_sync_manager().sync_all(force=force)


def sync_data_source(source_name: str, force: bool = False) -> SyncResult:
    """Convenience function to sync a single data source."""
    return get_sync_manager().sync_source(source_name, force=force)
