"""
ACB Link - Enhanced Podcasts Panel
Full-featured podcast browser with OPML support, episode viewing, and sorting.
"""

import webbrowser
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

import wx

from .accessibility import announce, make_accessible, make_list_accessible
from .podcast_manager import Podcast, PodcastEpisode, PodcastManager


class EpisodeSortOrder(Enum):
    """Episode sort options."""

    DATE_NEWEST = "date_newest"
    DATE_OLDEST = "date_oldest"
    TITLE_AZ = "title_az"
    TITLE_ZA = "title_za"
    DURATION_LONGEST = "duration_longest"
    DURATION_SHORTEST = "duration_shortest"
    UNPLAYED_FIRST = "unplayed_first"
    DOWNLOADED_FIRST = "downloaded_first"


SORT_LABELS = {
    EpisodeSortOrder.DATE_NEWEST: "Newest First",
    EpisodeSortOrder.DATE_OLDEST: "Oldest First",
    EpisodeSortOrder.TITLE_AZ: "Title A-Z",
    EpisodeSortOrder.TITLE_ZA: "Title Z-A",
    EpisodeSortOrder.DURATION_LONGEST: "Longest First",
    EpisodeSortOrder.DURATION_SHORTEST: "Shortest First",
    EpisodeSortOrder.UNPLAYED_FIRST: "Unplayed First",
    EpisodeSortOrder.DOWNLOADED_FIRST: "Downloaded First",
}


@dataclass
class OPMLPodcast:
    """Represents a podcast from OPML file."""

    title: str
    feed_url: str
    website: str = ""


def parse_opml_file(filepath: str) -> List[OPMLPodcast]:
    """Parse an OPML file and return list of podcasts."""
    podcasts = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        for outline in root.findall(".//outline[@xmlUrl]"):
            title = outline.get("title") or outline.get("text", "Unknown")
            feed_url = outline.get("xmlUrl", "")
            website = outline.get("htmlUrl", "")

            if feed_url:
                podcasts.append(OPMLPodcast(title=title, feed_url=feed_url, website=website))
    except Exception:
        pass

    return podcasts


class EnhancedPodcastsPanel(wx.Panel):
    """
    Enhanced podcasts panel with:
    - OPML podcast browsing
    - Episode listing with details
    - Download and stream options
    - Sortable episode list
    - Context menus
    - Accessibility features
    """

    def __init__(
        self,
        parent: wx.Window,
        podcast_manager: PodcastManager,
        on_play_episode: Callable[[str, PodcastEpisode], None],
        on_download_episode: Callable[[str, PodcastEpisode], None],
        opml_path: Optional[str] = None,
    ):
        super().__init__(parent)

        self.podcast_manager = podcast_manager
        self.on_play_episode = on_play_episode
        self.on_download_episode = on_download_episode
        self.opml_path = opml_path

        # State
        self.podcasts: List[OPMLPodcast] = []
        self.selected_podcast: Optional[OPMLPodcast] = None
        self.current_podcast: Optional[Podcast] = None
        self.current_sort = EpisodeSortOrder.DATE_NEWEST
        self.episodes_data: List[PodcastEpisode] = []

        self._build_ui()
        self._load_opml()

    def _build_ui(self):
        """Build the enhanced podcasts UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header section
        header_panel = self._create_header()
        main_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Main content - splitter
        self.splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)

        # Left panel - Podcast list
        left_panel = self._create_podcast_list_panel(self.splitter)

        # Right panel - Episodes
        right_panel = self._create_episodes_panel(self.splitter)

        self.splitter.SplitVertically(left_panel, right_panel, 280)
        self.splitter.SetMinimumPaneSize(200)

        main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)

    def _create_header(self) -> wx.Panel:
        """Create the header panel."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Title
        title = wx.StaticText(panel, label="🎙️ Podcasts")
        title_font = title.GetFont()
        title_font.SetPointSize(18)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(0, 120, 212))
        sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()

        # Status
        self.status_label = wx.StaticText(panel, label="")
        self.status_label.SetForegroundColour(wx.Colour(102, 102, 102))
        sizer.Add(self.status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Refresh button
        self.refresh_btn = wx.Button(panel, label="🔄 Refresh", size=(90, 28))
        self.refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_all)
        make_accessible(self.refresh_btn, "Refresh podcasts", "Reload podcast list")
        sizer.Add(self.refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        panel.SetSizer(sizer)
        return panel

    def _create_podcast_list_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the podcast list panel (left side)."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Search box
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        search_label = wx.StaticText(panel, label="&Search:")
        search_sizer.Add(search_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetDescriptiveText("Filter podcasts...")
        self.search_ctrl.SetName("Search podcasts")
        self.search_ctrl.Bind(wx.EVT_TEXT, self._on_search)
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_search_cancel)
        search_sizer.Add(self.search_ctrl, 1, wx.EXPAND)

        sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Podcast list
        list_label = wx.StaticText(panel, label="Available &Podcasts:")
        sizer.Add(list_label, 0, wx.LEFT | wx.TOP, 5)

        self.podcast_list = wx.ListCtrl(
            panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE
        )
        self.podcast_list.SetFont(
            wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )
        make_list_accessible(
            self.podcast_list,
            "Podcasts list",
            "Select a podcast to view its episodes. Press Enter to load episodes.",
        )

        self.podcast_list.InsertColumn(0, "Podcast Name", width=260)

        sizer.Add(self.podcast_list, 1, wx.EXPAND | wx.ALL, 5)

        # Podcast info
        self.podcast_info = wx.StaticText(panel, label="Select a podcast to view episodes")
        self.podcast_info.SetForegroundColour(wx.Colour(102, 102, 102))
        self.podcast_info.Wrap(250)
        sizer.Add(self.podcast_info, 0, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(sizer)

        # Bindings
        self.podcast_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_podcast_selected)
        self.podcast_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_podcast_activated)
        self.podcast_list.Bind(wx.EVT_CONTEXT_MENU, self._on_podcast_context_menu)

        return panel

    def _create_episodes_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the episodes panel (right side)."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Episode list header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.episodes_header = wx.StaticText(panel, label="&Episodes")
        header_font = self.episodes_header.GetFont()
        header_font.SetPointSize(12)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.episodes_header.SetFont(header_font)
        header_sizer.Add(self.episodes_header, 1, wx.ALIGN_CENTER_VERTICAL)

        # Sort dropdown
        sort_label = wx.StaticText(panel, label="Sort:")
        header_sizer.Add(sort_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.sort_choice = wx.Choice(panel, choices=[SORT_LABELS[s] for s in EpisodeSortOrder])
        self.sort_choice.SetSelection(0)
        self.sort_choice.SetName("Sort episodes by")
        self.sort_choice.Bind(wx.EVT_CHOICE, self._on_sort_changed)
        header_sizer.Add(self.sort_choice, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Episodes list
        self.episodes_list = wx.ListCtrl(
            panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE
        )
        self.episodes_list.SetFont(
            wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )
        make_list_accessible(
            self.episodes_list,
            "Episodes list",
            "Podcast episodes. Press Enter to play, or use context menu for more options.",
        )

        self.episodes_list.InsertColumn(0, "Title", width=280)
        self.episodes_list.InsertColumn(1, "Date", width=90)
        self.episodes_list.InsertColumn(2, "Duration", width=70)
        self.episodes_list.InsertColumn(3, "Status", width=80)

        sizer.Add(self.episodes_list, 1, wx.EXPAND | wx.ALL, 5)

        # Episode details panel
        self.details_panel = self._create_episode_details_panel(panel)
        sizer.Add(self.details_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Action buttons
        btn_panel = self._create_episode_buttons(panel)
        sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)

        # Bindings
        self.episodes_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_episode_selected)
        self.episodes_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_episode_activated)
        self.episodes_list.Bind(wx.EVT_CONTEXT_MENU, self._on_episode_context_menu)

        return panel

    def _create_episode_details_panel(self, parent: wx.Window) -> wx.Panel:
        """Create panel showing episode details."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(250, 250, 250))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.episode_title = wx.StaticText(panel, label="")
        title_font = self.episode_title.GetFont()
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.episode_title.SetFont(title_font)
        sizer.Add(self.episode_title, 0, wx.ALL, 5)

        self.episode_description = wx.StaticText(panel, label="")
        self.episode_description.SetForegroundColour(wx.Colour(80, 80, 80))
        self.episode_description.Wrap(400)
        sizer.Add(self.episode_description, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_episode_buttons(self, parent: wx.Window) -> wx.Panel:
        """Create action buttons panel."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(250, 250, 250))
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Stream button (primary)
        self.stream_btn = wx.Button(panel, label="▶ Stream Episode", size=(140, 32))
        self.stream_btn.SetBackgroundColour(wx.Colour(0, 120, 212))
        self.stream_btn.SetForegroundColour(wx.WHITE)
        self.stream_btn.Bind(wx.EVT_BUTTON, self._on_stream_episode)
        make_accessible(self.stream_btn, "Stream Episode", "Play this episode without downloading")
        sizer.Add(self.stream_btn, 0, wx.ALL, 5)

        # Download button
        self.download_btn = wx.Button(panel, label="⬇ Download", size=(110, 32))
        self.download_btn.Bind(wx.EVT_BUTTON, self._on_download_episode)
        make_accessible(self.download_btn, "Download Episode", "Download for offline listening")
        sizer.Add(self.download_btn, 0, wx.ALL, 5)

        # Add to favorites
        self.favorite_btn = wx.Button(panel, label="☆ Favorite", size=(100, 32))
        self.favorite_btn.Bind(wx.EVT_BUTTON, self._on_toggle_favorite)
        make_accessible(self.favorite_btn, "Toggle Favorite", "Add or remove from favorites")
        sizer.Add(self.favorite_btn, 0, wx.ALL, 5)

        sizer.AddStretchSpacer()

        # Mark played
        self.mark_played_btn = wx.Button(panel, label="✓ Mark Played", size=(110, 32))
        self.mark_played_btn.Bind(wx.EVT_BUTTON, self._on_mark_played)
        make_accessible(self.mark_played_btn, "Mark as Played", "Mark this episode as played")
        sizer.Add(self.mark_played_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _load_opml(self):
        """Load podcasts from OPML file."""
        if not self.opml_path:
            # Try default path
            default_path = Path(__file__).parent.parent / "data" / "s3" / "link.opml"
            if default_path.exists():
                self.opml_path = str(default_path)

        if self.opml_path and Path(self.opml_path).exists():
            self.podcasts = parse_opml_file(self.opml_path)
            self._populate_podcast_list()
            self.status_label.SetLabel(f"{len(self.podcasts)} podcasts")

    def _populate_podcast_list(self, filter_text: str = ""):
        """Populate the podcast list, optionally filtered."""
        self.podcast_list.DeleteAllItems()

        filter_lower = filter_text.lower().strip()

        for i, podcast in enumerate(self.podcasts):
            if filter_lower and filter_lower not in podcast.title.lower():
                continue

            idx = self.podcast_list.InsertItem(self.podcast_list.GetItemCount(), podcast.title)
            self.podcast_list.SetItemData(idx, i)

    def _on_search(self, event):
        """Handle search text change."""
        self._populate_podcast_list(self.search_ctrl.GetValue())

    def _on_search_cancel(self, event):
        """Handle search cancel."""
        self.search_ctrl.SetValue("")
        self._populate_podcast_list()

    def _on_podcast_selected(self, event):
        """Handle podcast selection."""
        idx = event.GetIndex()
        data_idx = self.podcast_list.GetItemData(idx)

        if 0 <= data_idx < len(self.podcasts):
            self.selected_podcast = self.podcasts[data_idx]
            self.podcast_info.SetLabel(
                f"Selected: {self.selected_podcast.title}\n"
                "Press Enter or double-click to load episodes"
            )

    def _on_podcast_activated(self, event):
        """Handle podcast double-click/Enter - load episodes."""
        if not self.selected_podcast:
            return

        self._load_podcast_episodes(self.selected_podcast)

    def _load_podcast_episodes(self, podcast: OPMLPodcast):
        """Load episodes for the selected podcast."""
        self.episodes_header.SetLabel(f"Loading: {podcast.title}...")
        self.episodes_list.DeleteAllItems()
        announce(f"Loading episodes for {podcast.title}")

        # Check if already cached
        cached = self.podcast_manager.get_podcast_by_url(podcast.feed_url)
        if cached and cached.episodes:
            self._display_episodes(cached)
        else:
            # Fetch feed
            self.podcast_manager.fetch_feed(
                podcast.feed_url,
                category="",
                on_complete=self._on_feed_loaded,
                on_error=self._on_feed_error,
            )

    def _on_feed_loaded(self, podcast: Podcast):
        """Handle successful feed load."""
        wx.CallAfter(self._display_episodes, podcast)

    def _on_feed_error(self, error: str):
        """Handle feed load error."""
        wx.CallAfter(self._show_feed_error, error)

    def _show_feed_error(self, error: str):
        """Display feed error."""
        self.episodes_header.SetLabel("Error loading feed")
        announce(f"Error loading podcast: {error}")
        wx.MessageBox(
            f"Could not load podcast feed:\n{error}", "Feed Error", wx.OK | wx.ICON_ERROR, self
        )

    def _display_episodes(self, podcast: Podcast):
        """Display episodes in the list."""
        self.current_podcast = podcast
        self.episodes_data = list(podcast.episodes)

        self.episodes_header.SetLabel(f"Episodes: {podcast.name}")
        self._sort_and_display_episodes()

        # Update favorite button
        if podcast.is_favorite:
            self.favorite_btn.SetLabel("★ Unfavorite")
        else:
            self.favorite_btn.SetLabel("☆ Favorite")

        # Announce
        count = len(podcast.episodes)
        announce(f"Loaded {count} episodes for {podcast.name}")

        # Select first episode
        if self.episodes_list.GetItemCount() > 0:
            self.episodes_list.Select(0)
            self.episodes_list.SetFocus()

    def _sort_and_display_episodes(self):
        """Sort and display episodes based on current sort order."""
        if not self.episodes_data:
            return

        # Sort episodes
        sorted_episodes = self._sort_episodes(self.episodes_data, self.current_sort)

        # Display
        self.episodes_list.DeleteAllItems()

        for i, ep in enumerate(sorted_episodes):
            idx = self.episodes_list.InsertItem(i, ep.title)

            # Format date
            date_str = ""
            if ep.pub_date:
                try:
                    # Try to parse and format date
                    date_str = ep.pub_date[:10] if len(ep.pub_date) >= 10 else ep.pub_date
                except Exception:
                    date_str = ep.pub_date[:16]

            self.episodes_list.SetItem(idx, 1, date_str)
            self.episodes_list.SetItem(idx, 2, ep.get_duration_str())

            # Status
            status = ""
            if ep.downloaded:
                status = "Downloaded"
            elif ep.played:
                status = "Played"
            elif ep.play_position > 0:
                status = "In Progress"
            else:
                status = "New"

            self.episodes_list.SetItem(idx, 3, status)
            self.episodes_list.SetItemData(idx, i)

        # Store sorted for reference
        self.episodes_data = sorted_episodes

    def _sort_episodes(
        self, episodes: List[PodcastEpisode], sort_order: EpisodeSortOrder
    ) -> List[PodcastEpisode]:
        """Sort episodes by the specified order."""
        if sort_order == EpisodeSortOrder.DATE_NEWEST:
            return sorted(episodes, key=lambda e: e.pub_date or "", reverse=True)
        elif sort_order == EpisodeSortOrder.DATE_OLDEST:
            return sorted(episodes, key=lambda e: e.pub_date or "")
        elif sort_order == EpisodeSortOrder.TITLE_AZ:
            return sorted(episodes, key=lambda e: e.title.lower())
        elif sort_order == EpisodeSortOrder.TITLE_ZA:
            return sorted(episodes, key=lambda e: e.title.lower(), reverse=True)
        elif sort_order == EpisodeSortOrder.DURATION_LONGEST:
            return sorted(episodes, key=lambda e: e.duration, reverse=True)
        elif sort_order == EpisodeSortOrder.DURATION_SHORTEST:
            return sorted(episodes, key=lambda e: e.duration)
        elif sort_order == EpisodeSortOrder.UNPLAYED_FIRST:
            return sorted(episodes, key=lambda e: (e.played, e.pub_date or ""), reverse=True)
        elif sort_order == EpisodeSortOrder.DOWNLOADED_FIRST:
            return sorted(
                episodes, key=lambda e: (not e.downloaded, e.pub_date or ""), reverse=True
            )

        return episodes

    def _on_sort_changed(self, event):
        """Handle sort order change."""
        sort_idx = self.sort_choice.GetSelection()
        self.current_sort = list(EpisodeSortOrder)[sort_idx]
        self._sort_and_display_episodes()
        announce(f"Sorted by {SORT_LABELS[self.current_sort]}")

    def _get_selected_episode(self) -> Optional[PodcastEpisode]:
        """Get the currently selected episode."""
        idx = self.episodes_list.GetFirstSelected()
        if idx == -1 or idx >= len(self.episodes_data):
            return None
        return self.episodes_data[idx]

    def _on_episode_selected(self, event):
        """Handle episode selection."""
        episode = self._get_selected_episode()
        if episode:
            self.episode_title.SetLabel(episode.title)

            # Truncate description
            desc = episode.description[:200]
            if len(episode.description) > 200:
                desc += "..."
            # Strip HTML tags (simple approach)
            import re

            desc = re.sub(r"<[^>]+>", "", desc)
            self.episode_description.SetLabel(desc)
            self.episode_description.Wrap(400)

            # Update buttons based on state
            if episode.downloaded:
                self.stream_btn.SetLabel("▶ Play Downloaded")
                self.download_btn.SetLabel("🗑 Delete Download")
            else:
                self.stream_btn.SetLabel("▶ Stream Episode")
                self.download_btn.SetLabel("⬇ Download")

            if episode.played:
                self.mark_played_btn.SetLabel("↩ Mark Unplayed")
            else:
                self.mark_played_btn.SetLabel("✓ Mark Played")

            self.details_panel.Layout()

    def _on_episode_activated(self, event):
        """Handle episode double-click - play/stream."""
        self._on_stream_episode(None)

    def _on_stream_episode(self, event):
        """Stream the selected episode."""
        episode = self._get_selected_episode()
        if not episode or not self.current_podcast:
            return

        announce(f"Playing {episode.title}")
        self.on_play_episode(self.current_podcast.name, episode)

    def _on_download_episode(self, event):
        """Download the selected episode."""
        episode = self._get_selected_episode()
        if not episode or not self.current_podcast:
            return

        if episode.downloaded:
            # Delete download
            result = wx.MessageBox(
                f"Delete downloaded file for '{episode.title}'?",
                "Delete Download",
                wx.YES_NO | wx.ICON_QUESTION,
                self,
            )
            if result == wx.YES:
                self.podcast_manager.delete_download(self.current_podcast.id, episode.id)
                self._sort_and_display_episodes()
                announce("Download deleted")
        else:
            # Start download
            announce(f"Downloading {episode.title}")
            self.on_download_episode(self.current_podcast.name, episode)

    def _on_toggle_favorite(self, event):
        """Toggle podcast favorite status."""
        if not self.current_podcast:
            return

        is_fav = self.podcast_manager.toggle_favorite(self.current_podcast.id)

        if is_fav:
            self.favorite_btn.SetLabel("★ Unfavorite")
            announce(f"Added {self.current_podcast.name} to favorites")
        else:
            self.favorite_btn.SetLabel("☆ Favorite")
            announce(f"Removed {self.current_podcast.name} from favorites")

    def _on_mark_played(self, event):
        """Toggle episode played status."""
        episode = self._get_selected_episode()
        if not episode or not self.current_podcast:
            return

        if episode.played:
            episode.played = False
            self.mark_played_btn.SetLabel("✓ Mark Played")
            announce("Marked as unplayed")
        else:
            self.podcast_manager.mark_episode_played(self.current_podcast.id, episode.id)
            self.mark_played_btn.SetLabel("↩ Mark Unplayed")
            announce("Marked as played")

        self._sort_and_display_episodes()

    def _on_refresh_all(self, event):
        """Refresh OPML and current podcast."""
        self._load_opml()

        if self.current_podcast:
            self._load_podcast_episodes(self.selected_podcast)

        announce("Refreshed podcast list")

    def _on_podcast_context_menu(self, event):
        """Show context menu for podcast list."""
        if not self.selected_podcast:
            return

        menu = wx.Menu()

        load_item = menu.Append(wx.ID_ANY, "Load Episodes")
        self.Bind(wx.EVT_MENU, lambda e: self._on_podcast_activated(None), load_item)

        menu.AppendSeparator()

        fav_item = menu.Append(wx.ID_ANY, "Add to Favorites")
        self.Bind(wx.EVT_MENU, self._on_add_podcast_favorite, fav_item)

        menu.AppendSeparator()

        website_item = menu.Append(wx.ID_ANY, "Visit Website")
        self.Bind(wx.EVT_MENU, self._on_visit_podcast_website, website_item)

        copy_item = menu.Append(wx.ID_ANY, "Copy Feed URL")
        self.Bind(wx.EVT_MENU, self._on_copy_feed_url, copy_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def _on_episode_context_menu(self, event):
        """Show context menu for episode list."""
        episode = self._get_selected_episode()
        if not episode:
            return

        menu = wx.Menu()

        # Play/Stream
        play_item = menu.Append(wx.ID_ANY, "Stream Episode")
        self.Bind(wx.EVT_MENU, lambda e: self._on_stream_episode(None), play_item)

        menu.AppendSeparator()

        # Download/Delete
        if episode.downloaded:
            dl_item = menu.Append(wx.ID_ANY, "Delete Download")
        else:
            dl_item = menu.Append(wx.ID_ANY, "Download Episode")
        self.Bind(wx.EVT_MENU, lambda e: self._on_download_episode(None), dl_item)

        menu.AppendSeparator()

        # Mark played/unplayed
        if episode.played:
            mark_item = menu.Append(wx.ID_ANY, "Mark as Unplayed")
        else:
            mark_item = menu.Append(wx.ID_ANY, "Mark as Played")
        self.Bind(wx.EVT_MENU, lambda e: self._on_mark_played(None), mark_item)

        # Add to favorites
        fav_item = menu.Append(wx.ID_ANY, "Add Episode to Favorites")
        self.Bind(wx.EVT_MENU, self._on_add_episode_favorite, fav_item)

        menu.AppendSeparator()

        # Copy URL
        copy_item = menu.Append(wx.ID_ANY, "Copy Episode URL")
        self.Bind(wx.EVT_MENU, self._on_copy_episode_url, copy_item)

        # Show details
        details_item = menu.Append(wx.ID_ANY, "Episode Details...")
        self.Bind(wx.EVT_MENU, self._on_show_episode_details, details_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def _on_add_podcast_favorite(self, event):
        """Add podcast to favorites."""
        if self.selected_podcast:
            # This would integrate with FavoritesManager
            announce(f"Added {self.selected_podcast.title} to favorites")

    def _on_visit_podcast_website(self, event):
        """Open podcast website."""
        if self.selected_podcast and self.selected_podcast.website:
            webbrowser.open(self.selected_podcast.website)

    def _on_copy_feed_url(self, event):
        """Copy feed URL to clipboard."""
        if self.selected_podcast:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(self.selected_podcast.feed_url))
                wx.TheClipboard.Close()
                announce("Feed URL copied")

    def _on_add_episode_favorite(self, event):
        """Add episode to favorites."""
        episode = self._get_selected_episode()
        if episode:
            announce(f"Added {episode.title} to favorites")

    def _on_copy_episode_url(self, event):
        """Copy episode URL to clipboard."""
        episode = self._get_selected_episode()
        if episode and episode.url:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(episode.url))
                wx.TheClipboard.Close()
                announce("Episode URL copied")

    def _on_show_episode_details(self, event):
        """Show detailed episode information."""
        episode = self._get_selected_episode()
        if not episode:
            return

        # Create details dialog
        import re

        desc = re.sub(r"<[^>]+>", "", episode.description)

        details = f"""Title: {episode.title}

Date Published: {episode.pub_date}

Duration: {episode.get_duration_str()}

File Size: {episode.get_file_size_str()}

Type: {episode.episode_type}

Season: {episode.season if episode.season else 'N/A'}
Episode: {episode.episode_number if episode.episode_number else 'N/A'}

Description:
{desc}
"""

        dlg = wx.MessageDialog(
            self, details, f"Episode Details - {episode.title[:50]}", wx.OK | wx.ICON_INFORMATION
        )
        dlg.ShowModal()
        dlg.Destroy()

    def set_sort_order(self, sort_order: EpisodeSortOrder):
        """Set the sort order (for View menu integration)."""
        self.current_sort = sort_order
        idx = list(EpisodeSortOrder).index(sort_order)
        self.sort_choice.SetSelection(idx)
        self._sort_and_display_episodes()

    def get_sort_order(self) -> EpisodeSortOrder:
        """Get current sort order."""
        return self.current_sort
