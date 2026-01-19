"""
ACB Link - Global Search Module
Search across all content types: streams, podcasts, episodes, and transcripts.
"""

import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .utils import get_app_data_dir


class SearchResultType(Enum):
    """Types of search results."""

    STREAM = "stream"
    PODCAST = "podcast"
    EPISODE = "episode"
    TRANSCRIPT = "transcript"
    BOOKMARK = "bookmark"
    FAVORITE = "favorite"


@dataclass
class SearchResult:
    """Represents a single search result."""

    type: SearchResultType
    id: str
    title: str
    description: str = ""
    url: str = ""
    relevance_score: float = 0.0
    # Additional context
    parent_id: str = ""  # podcast_id for episodes
    parent_name: str = ""  # podcast name for episodes
    matched_text: str = ""  # Text that matched the query
    position: float = 0.0  # Position in episode for transcript matches

    def __lt__(self, other):
        """Sort by relevance score descending."""
        return self.relevance_score > other.relevance_score


@dataclass
class SearchQuery:
    """Represents a search query with filters."""

    text: str
    # Filters
    types: List[SearchResultType] = field(default_factory=list)  # Empty = all
    podcast_id: str = ""  # Filter to specific podcast
    date_from: str = ""
    date_to: str = ""
    # Options
    case_sensitive: bool = False
    whole_word: bool = False
    max_results: int = 50


class SearchHistory:
    """Manages search history."""

    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self._history_file = get_app_data_dir() / "search_history.json"
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load history from disk."""
        import json

        if self._history_file.exists():
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                pass

    def _save(self):
        """Save history to disk."""
        import json

        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def add(self, query: str, result_count: int):
        """Add a search to history."""
        entry = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": result_count,
        }

        # Remove duplicate if exists
        self.history = [h for h in self.history if h["query"] != query]

        # Add to front
        self.history.insert(0, entry)

        # Trim
        self.history = self.history[: self.max_items]
        self._save()

    def get_recent(self, limit: int = 10) -> List[str]:
        """Get recent search queries."""
        return [h["query"] for h in self.history[:limit]]

    def clear(self):
        """Clear search history."""
        self.history.clear()
        self._save()

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on prefix."""
        prefix = prefix.lower()
        suggestions = []

        for entry in self.history:
            query = entry["query"]
            if query.lower().startswith(prefix) and query not in suggestions:
                suggestions.append(query)
                if len(suggestions) >= limit:
                    break

        return suggestions


class GlobalSearch:
    """
    Global search engine for ACB Link.
    Searches across streams, podcasts, episodes, and more.
    """

    def __init__(self):
        self.history = SearchHistory()

        # Search data sources (will be populated by app)
        self._streams: List[Dict] = []
        self._podcasts: Dict[str, Any] = {}  # PodcastManager podcasts
        self._favorites = None  # FavoritesManager

        # Search thread
        self._search_thread: Optional[threading.Thread] = None
        self._stop_search = threading.Event()

        # Callbacks
        self.on_search_progress: Optional[Callable[[int, int], None]] = None
        self.on_search_complete: Optional[Callable[[List[SearchResult]], None]] = None

    def set_data_sources(
        self, streams: Optional[List[Dict]] = None, podcast_manager=None, favorites_manager=None
    ):
        """Set the data sources for searching."""
        if streams:
            self._streams = streams
        if podcast_manager:
            self._podcasts = podcast_manager.podcasts
        if favorites_manager:
            self._favorites = favorites_manager

    def search(
        self, query: SearchQuery, async_search: bool = False
    ) -> Optional[List[SearchResult]]:
        """
        Perform a search.

        Args:
            query: Search query with filters
            async_search: If True, search runs in background and uses callbacks

        Returns:
            List of results if sync, None if async
        """
        if async_search:
            self._stop_search.clear()
            self._search_thread = threading.Thread(
                target=self._search_async, args=(query,), daemon=True
            )
            self._search_thread.start()
            return None
        else:
            return self._perform_search(query)

    def search_simple(self, text: str) -> List[SearchResult]:
        """Simple search with just text."""
        query = SearchQuery(text=text)
        return self._perform_search(query)

    def cancel_search(self):
        """Cancel an async search."""
        self._stop_search.set()

    def _search_async(self, query: SearchQuery):
        """Async search thread."""
        results = self._perform_search(query)

        if not self._stop_search.is_set() and self.on_search_complete:
            self.on_search_complete(results)

    def _perform_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform the actual search."""
        results: List[SearchResult] = []

        if not query.text.strip():
            return results

        search_text = query.text if query.case_sensitive else query.text.lower()

        # Build regex pattern
        if query.whole_word:
            pattern = rf"\b{re.escape(search_text)}\b"
        else:
            pattern = re.escape(search_text)

        flags = 0 if query.case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        total_items = self._count_searchable_items(query)
        searched = 0

        # Search streams
        if not query.types or SearchResultType.STREAM in query.types:
            for stream in self._streams:
                if self._stop_search.is_set():
                    break

                searched += 1
                self._report_progress(searched, total_items)

                name = stream.get("name", "")
                desc = stream.get("desc", "")

                if regex.search(name) or regex.search(desc):
                    match_text = name if regex.search(name) else desc
                    results.append(
                        SearchResult(
                            type=SearchResultType.STREAM,
                            id=str(stream.get("id", "")),
                            title=name,
                            description=desc,
                            url=f"stream://{stream.get('station', '')}",
                            relevance_score=self._calculate_relevance(search_text, name, desc),
                            matched_text=self._highlight_match(match_text, regex),
                        )
                    )

        # Search podcasts and episodes
        if (
            not query.types
            or SearchResultType.PODCAST in query.types
            or SearchResultType.EPISODE in query.types
        ):
            for podcast_id, podcast in self._podcasts.items():
                if self._stop_search.is_set():
                    break

                # Filter by podcast_id if specified
                if query.podcast_id and podcast_id != query.podcast_id:
                    continue

                searched += 1
                self._report_progress(searched, total_items)

                # Search podcast
                if not query.types or SearchResultType.PODCAST in query.types:
                    name = getattr(podcast, "name", "")
                    desc = getattr(podcast, "description", "")

                    if regex.search(name) or regex.search(desc):
                        match_text = name if regex.search(name) else desc
                        results.append(
                            SearchResult(
                                type=SearchResultType.PODCAST,
                                id=podcast_id,
                                title=name,
                                description=desc[:200] + "..." if len(desc) > 200 else desc,
                                url=getattr(podcast, "feed_url", ""),
                                relevance_score=self._calculate_relevance(search_text, name, desc),
                                matched_text=self._highlight_match(match_text, regex),
                            )
                        )

                # Search episodes
                if not query.types or SearchResultType.EPISODE in query.types:
                    for episode in getattr(podcast, "episodes", []):
                        if self._stop_search.is_set():
                            break

                        searched += 1
                        self._report_progress(searched, total_items)

                        ep_title = getattr(episode, "title", "")
                        ep_desc = getattr(episode, "description", "")

                        if regex.search(ep_title) or regex.search(ep_desc):
                            match_text = ep_title if regex.search(ep_title) else ep_desc
                            results.append(
                                SearchResult(
                                    type=SearchResultType.EPISODE,
                                    id=getattr(episode, "id", ""),
                                    title=ep_title,
                                    description=(
                                        ep_desc[:200] + "..." if len(ep_desc) > 200 else ep_desc
                                    ),
                                    url=getattr(episode, "url", ""),
                                    relevance_score=self._calculate_relevance(
                                        search_text, ep_title, ep_desc
                                    ),
                                    parent_id=podcast_id,
                                    parent_name=getattr(podcast, "name", ""),
                                    matched_text=self._highlight_match(match_text, regex),
                                )
                            )

        # Search favorites
        if self._favorites and (not query.types or SearchResultType.FAVORITE in query.types):
            for fav in self._favorites.get_all_favorites():
                if self._stop_search.is_set():
                    break

                searched += 1
                self._report_progress(searched, total_items)

                name = fav.name
                desc = fav.description

                if regex.search(name) or regex.search(desc):
                    match_text = name if regex.search(name) else desc
                    results.append(
                        SearchResult(
                            type=SearchResultType.FAVORITE,
                            id=fav.id,
                            title=name,
                            description=desc,
                            url=fav.url,
                            relevance_score=self._calculate_relevance(search_text, name, desc),
                            matched_text=self._highlight_match(match_text, regex),
                        )
                    )

        # Search bookmarks
        if self._favorites and (not query.types or SearchResultType.BOOKMARK in query.types):
            for bookmark in self._favorites.get_all_bookmarks():
                if self._stop_search.is_set():
                    break

                searched += 1
                self._report_progress(searched, total_items)

                name = f"{bookmark.episode_name} ({bookmark.podcast_name})"
                note = bookmark.note

                if regex.search(name) or regex.search(note):
                    match_text = note if regex.search(note) else name
                    results.append(
                        SearchResult(
                            type=SearchResultType.BOOKMARK,
                            id=bookmark.id,
                            title=name,
                            description=f"Position: {bookmark.get_position_str()} - {note}",
                            relevance_score=self._calculate_relevance(search_text, name, note),
                            parent_id=bookmark.podcast_id,
                            position=bookmark.position,
                            matched_text=self._highlight_match(match_text, regex),
                        )
                    )

        # Sort by relevance
        results.sort()

        # Limit results
        results = results[: query.max_results]

        # Add to history
        self.history.add(query.text, len(results))

        return results

    def _count_searchable_items(self, query: SearchQuery) -> int:
        """Count total items to search."""
        count = 0

        if not query.types or SearchResultType.STREAM in query.types:
            count += len(self._streams)

        if (
            not query.types
            or SearchResultType.PODCAST in query.types
            or SearchResultType.EPISODE in query.types
        ):
            for podcast in self._podcasts.values():
                count += 1  # Podcast itself
                count += len(getattr(podcast, "episodes", []))

        if self._favorites:
            if not query.types or SearchResultType.FAVORITE in query.types:
                count += len(self._favorites.favorites)
            if not query.types or SearchResultType.BOOKMARK in query.types:
                count += len(self._favorites.bookmarks)

        return count

    def _report_progress(self, current: int, total: int):
        """Report search progress."""
        if self.on_search_progress and total > 0:
            self.on_search_progress(current, total)

    def _calculate_relevance(self, query: str, title: str, description: str) -> float:
        """Calculate relevance score for a result."""
        query = query.lower()
        title = title.lower()
        description = description.lower()

        score = 0.0

        # Exact title match
        if query == title:
            score = 1.0
        # Title starts with query
        elif title.startswith(query):
            score = 0.9
        # Title contains query
        elif query in title:
            score = 0.8
        # Description contains query
        elif query in description:
            score = 0.5

        # Boost for word boundary matches
        if re.search(rf"\b{re.escape(query)}\b", title, re.IGNORECASE):
            score += 0.1

        return min(1.0, score)

    def _highlight_match(self, text: str, regex: re.Pattern, max_len: int = 100) -> str:
        """Extract and highlight the matched portion of text."""
        match = regex.search(text)
        if not match:
            return text[:max_len]

        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)

        excerpt = text[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."

        return excerpt

    # Voice Search Integration

    def voice_search(self, spoken_text: str) -> List[SearchResult]:
        """
        Handle voice search with natural language processing.
        Parses commands like "find episodes about accessibility"
        """
        text = spoken_text.lower().strip()

        # Remove common prefixes
        prefixes = ["search for", "find", "look for", "search", "show me", "play", "open"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
                break

        # Detect type filters
        types = []
        if "stream" in text:
            types.append(SearchResultType.STREAM)
            text = text.replace("stream", "").replace("streams", "")
        if "podcast" in text:
            types.append(SearchResultType.PODCAST)
            text = text.replace("podcast", "").replace("podcasts", "")
        if "episode" in text:
            types.append(SearchResultType.EPISODE)
            text = text.replace("episode", "").replace("episodes", "")

        # Clean up
        text = " ".join(text.split())  # Remove extra spaces

        if not text:
            return []

        query = SearchQuery(text=text, types=types)
        return self._perform_search(query)

    def get_suggestions(self, prefix: str) -> List[str]:
        """Get search suggestions for autocomplete."""
        return self.history.get_suggestions(prefix)
