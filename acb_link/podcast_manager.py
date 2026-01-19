"""
ACB Link - Podcast Manager Module
Full RSS feed parsing, episode management, and download functionality.
"""

import os
import json
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Callable
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .utils import (
    get_app_data_dir, get_downloads_dir, sanitize_filename,
    format_duration, format_file_size
)


@dataclass
class PodcastEpisode:
    """Represents a podcast episode."""
    id: str
    title: str
    description: str = ""
    url: str = ""
    duration: int = 0  # seconds
    pub_date: str = ""
    file_size: int = 0
    episode_type: str = "full"  # full, trailer, bonus
    season: int = 0
    episode_number: int = 0
    image_url: str = ""
    # Local state
    downloaded: bool = False
    download_path: str = ""
    played: bool = False
    play_position: float = 0.0  # seconds
    
    def get_duration_str(self) -> str:
        """Get formatted duration string."""
        return format_duration(self.duration)
    
    def get_file_size_str(self) -> str:
        """Get formatted file size string."""
        return format_file_size(self.file_size)


@dataclass
class Podcast:
    """Represents a podcast feed."""
    id: str
    name: str
    feed_url: str
    description: str = ""
    author: str = ""
    image_url: str = ""
    website: str = ""
    category: str = ""
    last_updated: str = ""
    episodes: List[PodcastEpisode] = field(default_factory=list)
    # User state
    subscribed: bool = True
    is_favorite: bool = False
    
    @staticmethod
    def generate_id(feed_url: str) -> str:
        """Generate a unique ID from the feed URL."""
        return hashlib.md5(feed_url.encode()).hexdigest()[:12]


class RSSParser:
    """Parse RSS/Atom feeds for podcast information."""
    
    NAMESPACES = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'atom': 'http://www.w3.org/2005/Atom',
        'media': 'http://search.yahoo.com/mrss/',
    }
    
    @classmethod
    def parse_feed(cls, xml_content: str) -> Optional[Podcast]:
        """Parse RSS feed XML and return Podcast object."""
        try:
            root = ET.fromstring(xml_content)
            channel = root.find('channel')
            
            if channel is None:
                return None
            
            # Get feed info
            title = cls._get_text(channel, 'title') or "Unknown Podcast"
            description = cls._get_text(channel, 'description') or ""
            link = cls._get_text(channel, 'link') or ""
            author = cls._get_text(channel, 'itunes:author', cls.NAMESPACES) or ""
            
            # Get image
            image_url = ""
            itunes_image = channel.find('itunes:image', cls.NAMESPACES)
            if itunes_image is not None:
                image_url = itunes_image.get('href', '')
            elif channel.find('image/url') is not None:
                image_url = cls._get_text(channel.find('image'), 'url')
            
            # Parse episodes
            episodes = []
            for item in channel.findall('item'):
                episode = cls._parse_episode(item)
                if episode:
                    episodes.append(episode)
            
            return Podcast(
                id=Podcast.generate_id(link or title),
                name=title,
                feed_url="",  # Will be set by caller
                description=description,
                author=author,
                image_url=image_url,
                website=link,
                last_updated=datetime.now().isoformat(),
                episodes=episodes
            )
            
        except ET.ParseError:
            return None
    
    @classmethod
    def _get_text(cls, element, path: str, namespaces: Optional[dict] = None) -> str:
        """Get text content from an element."""
        if namespaces:
            child = element.find(path, namespaces)
        else:
            child = element.find(path)
        
        if child is not None and child.text:
            return child.text.strip()
        return ""
    
    @classmethod
    def _parse_episode(cls, item: ET.Element) -> Optional[PodcastEpisode]:
        """Parse an RSS item into a PodcastEpisode."""
        title = cls._get_text(item, 'title')
        if not title:
            return None
        
        # Get enclosure (audio file)
        enclosure = item.find('enclosure')
        url = ""
        file_size = 0
        if enclosure is not None:
            url = enclosure.get('url', '')
            try:
                file_size = int(enclosure.get('length', 0))
            except ValueError:
                pass
        
        # Get description
        description = cls._get_text(item, 'description')
        if not description:
            description = cls._get_text(item, 'content:encoded', cls.NAMESPACES)
        
        # Get duration
        duration = 0
        duration_str = cls._get_text(item, 'itunes:duration', cls.NAMESPACES)
        if duration_str:
            duration = cls._parse_duration(duration_str)
        
        # Get pub date
        pub_date = cls._get_text(item, 'pubDate') or ""
        
        # Get episode info
        season = 0
        episode_num = 0
        try:
            season_str = cls._get_text(item, 'itunes:season', cls.NAMESPACES)
            if season_str:
                season = int(season_str)
            episode_str = cls._get_text(item, 'itunes:episode', cls.NAMESPACES)
            if episode_str:
                episode_num = int(episode_str)
        except ValueError:
            pass
        
        # Get episode type
        episode_type = cls._get_text(item, 'itunes:episodeType', cls.NAMESPACES) or "full"
        
        # Get image
        image_url = ""
        itunes_image = item.find('itunes:image', cls.NAMESPACES)
        if itunes_image is not None:
            image_url = itunes_image.get('href', '')
        
        # Generate unique ID
        guid = cls._get_text(item, 'guid')
        if not guid:
            guid = url or title
        episode_id = hashlib.md5(guid.encode()).hexdigest()[:12]
        
        return PodcastEpisode(
            id=episode_id,
            title=title,
            description=description,
            url=url,
            duration=duration,
            pub_date=pub_date,
            file_size=file_size,
            episode_type=episode_type,
            season=season,
            episode_number=episode_num,
            image_url=image_url
        )
    
    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse duration string to seconds."""
        try:
            # Handle HH:MM:SS or MM:SS format
            parts = duration_str.split(':')
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(duration_str)
        except ValueError:
            return 0


class DownloadManager:
    """Manages podcast episode downloads."""
    
    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or get_downloads_dir()
        self.active_downloads: Dict[str, threading.Thread] = {}
        self.download_queue: List[tuple] = []  # (episode_id, url, path)
        self.progress_callbacks: Dict[str, Callable[[int, int], None]] = {}
        self.complete_callbacks: Dict[str, Callable[[str], None]] = {}
        self.error_callbacks: Dict[str, Callable[[str], None]] = {}
        self._lock = threading.Lock()
    
    def download_episode(
        self,
        episode: PodcastEpisode,
        podcast_name: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ) -> bool:
        """Start downloading an episode."""
        if not HAS_REQUESTS:
            if on_error:
                on_error("requests library not installed")
            return False
        
        if not episode.url:
            if on_error:
                on_error("Episode has no download URL")
            return False
        
        # Check if already downloading
        if episode.id in self.active_downloads:
            return False
        
        # Create podcast folder
        podcast_dir = self.download_dir / sanitize_filename(podcast_name)
        podcast_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        ext = self._get_extension(episode.url)
        filename = sanitize_filename(episode.title) + ext
        filepath = podcast_dir / filename
        
        # Handle duplicates
        counter = 1
        while filepath.exists():
            filename = f"{sanitize_filename(episode.title)}_{counter}{ext}"
            filepath = podcast_dir / filename
            counter += 1
        
        # Store callbacks
        if on_progress:
            self.progress_callbacks[episode.id] = on_progress
        if on_complete:
            self.complete_callbacks[episode.id] = on_complete
        if on_error:
            self.error_callbacks[episode.id] = on_error
        
        # Start download thread
        thread = threading.Thread(
            target=self._download_thread,
            args=(episode, str(filepath)),
            daemon=True,
            name=f"Download-{episode.id}"
        )
        self.active_downloads[episode.id] = thread
        thread.start()
        
        return True
    
    def _download_thread(self, episode: PodcastEpisode, filepath: str):
        """Background download thread."""
        try:
            response = requests.get(episode.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Report progress
                        if episode.id in self.progress_callbacks:
                            self.progress_callbacks[episode.id](downloaded, total_size)
            
            # Update episode
            episode.downloaded = True
            episode.download_path = filepath
            
            # Call completion callback
            if episode.id in self.complete_callbacks:
                self.complete_callbacks[episode.id](filepath)
                
        except Exception as e:
            if episode.id in self.error_callbacks:
                self.error_callbacks[episode.id](str(e))
            
            # Clean up partial file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
        finally:
            # Clean up
            with self._lock:
                self.active_downloads.pop(episode.id, None)
                self.progress_callbacks.pop(episode.id, None)
                self.complete_callbacks.pop(episode.id, None)
                self.error_callbacks.pop(episode.id, None)
    
    def cancel_download(self, episode_id: str):
        """Cancel an active download."""
        # Note: In a full implementation, we'd need a stop event
        with self._lock:
            self.active_downloads.pop(episode_id, None)
    
    def is_downloading(self, episode_id: str) -> bool:
        """Check if an episode is currently downloading."""
        return episode_id in self.active_downloads
    
    @staticmethod
    def _get_extension(url: str) -> str:
        """Get file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.mp3', '.m4a', '.ogg', '.wav', '.aac']:
            return ext
        return '.mp3'  # Default


class PodcastManager:
    """
    Main podcast management class.
    Handles feed fetching, caching, and episode tracking.
    """
    
    def __init__(self):
        self.podcasts: Dict[str, Podcast] = {}
        self.download_manager = DownloadManager()
        self._cache_dir = get_app_data_dir() / "podcast_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = get_app_data_dir() / "podcast_state.json"
        
        # Load saved state
        self._load_state()
    
    def _load_state(self):
        """Load podcast state from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for podcast_data in data.get('podcasts', []):
                    episodes = []
                    for ep_data in podcast_data.pop('episodes', []):
                        episodes.append(PodcastEpisode(**ep_data))
                    podcast = Podcast(**podcast_data, episodes=episodes)
                    self.podcasts[podcast.id] = podcast
            except Exception:
                pass
    
    def _save_state(self):
        """Save podcast state to disk."""
        try:
            data = {
                'podcasts': [
                    {
                        **asdict(podcast),
                        'episodes': [asdict(ep) for ep in podcast.episodes]
                    }
                    for podcast in self.podcasts.values()
                ]
            }
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def fetch_feed(
        self,
        feed_url: str,
        category: str = "",
        on_complete: Optional[Callable[[Podcast], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """Fetch and parse a podcast feed (async)."""
        thread = threading.Thread(
            target=self._fetch_feed_thread,
            args=(feed_url, category, on_complete, on_error),
            daemon=True
        )
        thread.start()
    
    def _fetch_feed_thread(
        self,
        feed_url: str,
        category: str,
        on_complete: Callable[[Podcast], None],
        on_error: Callable[[str], None]
    ):
        """Background feed fetching."""
        if not HAS_REQUESTS:
            if on_error:
                on_error("requests library not installed")
            return
        
        try:
            response = requests.get(feed_url, timeout=30, headers={
                'User-Agent': 'ACB Link Podcast Client/1.0'
            })
            response.raise_for_status()
            
            podcast = RSSParser.parse_feed(response.text)
            if podcast:
                podcast.feed_url = feed_url
                podcast.category = category
                podcast.id = Podcast.generate_id(feed_url)
                
                # Merge with existing state (preserve play positions, etc.)
                if podcast.id in self.podcasts:
                    existing = self.podcasts[podcast.id]
                    existing_episodes = {ep.id: ep for ep in existing.episodes}
                    
                    for ep in podcast.episodes:
                        if ep.id in existing_episodes:
                            old_ep = existing_episodes[ep.id]
                            ep.downloaded = old_ep.downloaded
                            ep.download_path = old_ep.download_path
                            ep.played = old_ep.played
                            ep.play_position = old_ep.play_position
                    
                    podcast.is_favorite = existing.is_favorite
                
                self.podcasts[podcast.id] = podcast
                self._save_state()
                
                # Cache feed content
                cache_file = self._cache_dir / f"{podcast.id}.xml"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                if on_complete:
                    on_complete(podcast)
            else:
                if on_error:
                    on_error("Failed to parse feed")
                    
        except requests.RequestException as e:
            if on_error:
                on_error(str(e))
    
    def get_podcast(self, podcast_id: str) -> Optional[Podcast]:
        """Get a podcast by ID."""
        return self.podcasts.get(podcast_id)
    
    def get_podcast_by_url(self, feed_url: str) -> Optional[Podcast]:
        """Get a podcast by feed URL."""
        podcast_id = Podcast.generate_id(feed_url)
        return self.podcasts.get(podcast_id)
    
    def get_episode(self, podcast_id: str, episode_id: str) -> Optional[PodcastEpisode]:
        """Get a specific episode."""
        podcast = self.podcasts.get(podcast_id)
        if podcast:
            for ep in podcast.episodes:
                if ep.id == episode_id:
                    return ep
        return None
    
    def mark_episode_played(self, podcast_id: str, episode_id: str):
        """Mark an episode as played."""
        episode = self.get_episode(podcast_id, episode_id)
        if episode:
            episode.played = True
            episode.play_position = 0
            self._save_state()
    
    def save_play_position(self, podcast_id: str, episode_id: str, position: float):
        """Save the current play position for an episode."""
        episode = self.get_episode(podcast_id, episode_id)
        if episode:
            episode.play_position = position
            self._save_state()
    
    def toggle_favorite(self, podcast_id: str) -> bool:
        """Toggle favorite status for a podcast."""
        podcast = self.podcasts.get(podcast_id)
        if podcast:
            podcast.is_favorite = not podcast.is_favorite
            self._save_state()
            return podcast.is_favorite
        return False
    
    def get_favorites(self) -> List[Podcast]:
        """Get all favorite podcasts."""
        return [p for p in self.podcasts.values() if p.is_favorite]
    
    def get_unplayed_episodes(self, podcast_id: Optional[str] = None) -> List[tuple]:
        """Get unplayed episodes, optionally for a specific podcast."""
        episodes = []
        podcasts = [self.podcasts[podcast_id]] if podcast_id else self.podcasts.values()
        
        for podcast in podcasts:
            if podcast_id is None or podcast.id == podcast_id:
                for ep in podcast.episodes:
                    if not ep.played:
                        episodes.append((podcast, ep))
        
        return episodes
    
    def get_downloaded_episodes(self) -> List[tuple]:
        """Get all downloaded episodes."""
        episodes = []
        for podcast in self.podcasts.values():
            for ep in podcast.episodes:
                if ep.downloaded and ep.download_path:
                    if os.path.exists(ep.download_path):
                        episodes.append((podcast, ep))
        return episodes
    
    def delete_download(self, podcast_id: str, episode_id: str) -> bool:
        """Delete a downloaded episode file."""
        episode = self.get_episode(podcast_id, episode_id)
        if episode and episode.downloaded and episode.download_path:
            try:
                if os.path.exists(episode.download_path):
                    os.remove(episode.download_path)
                episode.downloaded = False
                episode.download_path = ""
                self._save_state()
                return True
            except Exception:
                pass
        return False
    
    def cleanup_orphaned_downloads(self):
        """Remove download entries for files that no longer exist."""
        for podcast in self.podcasts.values():
            for ep in podcast.episodes:
                if ep.downloaded and ep.download_path:
                    if not os.path.exists(ep.download_path):
                        ep.downloaded = False
                        ep.download_path = ""
        self._save_state()
