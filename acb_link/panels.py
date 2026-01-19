"""
ACB Link - UI Panels
Home, Streams, Podcasts, Favorites, Playlists, Search, and Calendar panels.
Modern, accessible design with consistent styling.
WCAG 2.2 AA compliant.
"""

import wx
import wx.html2
import webbrowser
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from .data import STREAMS, PODCASTS, AFFILIATES, RESOURCES
from .accessibility import announce, make_accessible, make_list_accessible


# Modern color constants for panels
ACCENT_COLOR = "#0078D4"
ACCENT_COLOR_LIGHT = "#4CC2FF"
CARD_BG_COLOR = "#FAFAFA"
BORDER_COLOR = "#E0E0E0"
TEXT_SECONDARY = "#666666"


class HomePanel(wx.Panel):
    """Home tab panel with customizable content sections and modern design."""
    
    def __init__(self, parent, settings, on_play_stream: Callable, on_play_podcast: Callable):
        super().__init__(parent)
        self.settings = settings
        self.on_play_stream = on_play_stream
        self.on_play_podcast = on_play_podcast
        self.announcement_widget = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the home panel UI with modern styling."""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Hero header section
        header_panel = wx.Panel(self)
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Welcome header with accent color
        header = wx.StaticText(header_panel, label="Welcome to ACB Link")
        header_font = header.GetFont()
        header_font.SetPointSize(24)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        header.SetForegroundColour(wx.Colour(0, 120, 212))  # Accent blue
        header_sizer.Add(header, 0, wx.ALL, 5)
        
        subtitle = wx.StaticText(header_panel, label="Your gateway to ACB media content")
        sub_font = subtitle.GetFont()
        sub_font.SetPointSize(12)
        subtitle.SetFont(sub_font)
        subtitle.SetForegroundColour(wx.Colour(102, 102, 102))  # Secondary text
        header_sizer.Add(subtitle, 0, wx.LEFT | wx.BOTTOM, 5)
        
        header_panel.SetSizer(header_sizer)
        self.main_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 20)
        
        # Announcement widget - always first when there are unread announcements
        self._add_announcement_widget()
        
        # Separator line
        separator = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        self.main_sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        # Scrolled window for content cards
        self.scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll.SetScrollRate(0, 20)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._add_sections()
        
        self.scroll.SetSizer(self.scroll_sizer)
        self.main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(self.main_sizer)
    
    def _add_announcement_widget(self):
        """Add the announcement widget if there are unread announcements."""
        try:
            from .announcements import get_announcement_manager
            from .announcement_ui import AnnouncementWidget
            
            manager = get_announcement_manager()
            settings = manager.settings
            
            # Only show if enabled and there are unread announcements
            if settings.show_widget and manager.get_unread_count() > 0:
                self.announcement_widget = AnnouncementWidget(
                    self,
                    manager=manager,
                    max_items=settings.widget_max_items,
                )
                self.main_sizer.Insert(1, self.announcement_widget, 0, wx.EXPAND | wx.ALL, 15)
        except Exception as e:
            # Announcement system not available, skip widget
            pass
    
    def refresh_announcements(self):
        """Refresh the announcement widget."""
        if self.announcement_widget:
            self.announcement_widget.refresh()
            # Show/hide based on unread status
            self.announcement_widget.Show(self.announcement_widget.has_unread())
            self.Layout()
    
    def _add_sections(self):
        """Add content sections based on settings."""
        home_settings = self.settings.home_tab
        
        if home_settings.show_streams:
            self._add_streams_section()
        
        if home_settings.show_podcasts:
            self._add_podcasts_section()
        
        if home_settings.show_affiliates:
            self._add_affiliates_section()
        
        if home_settings.show_recent:
            self._add_recent_section()
    
    def _create_card_panel(self) -> wx.Panel:
        """Create a card-style panel with border and background."""
        card = wx.Panel(self.scroll)
        card.SetBackgroundColour(wx.Colour(250, 250, 250))
        return card
    
    def _add_streams_section(self):
        """Add streams quick access section with card styling."""
        # Section header
        section = self._create_section_header("🎵 Quick Access - Streams")
        self.scroll_sizer.Add(section, 0, wx.EXPAND | wx.ALL, 15)
        
        # Card container
        card = self._create_card_panel()
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Stream buttons in a wrap sizer
        streams_sizer = wx.WrapSizer(wx.HORIZONTAL)
        for name, _ in list(STREAMS.items())[:5]:
            btn = wx.Button(card, label=name, size=(-1, 36))
            btn.SetBackgroundColour(wx.Colour(0, 120, 212))
            btn.SetForegroundColour(wx.WHITE)
            btn.Bind(wx.EVT_BUTTON, lambda e, n=name: self.on_play_stream(n))
            streams_sizer.Add(btn, 0, wx.ALL, 5)
        
        card_sizer.Add(streams_sizer, 0, wx.ALL, 10)
        card.SetSizer(card_sizer)
        self.scroll_sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
    
    def _add_podcasts_section(self):
        """Add podcasts quick access section with modern styling."""
        section = self._create_section_header("🎙️ Featured Podcasts")
        self.scroll_sizer.Add(section, 0, wx.EXPAND | wx.ALL, 15)
        
        # Card container
        card = self._create_card_panel()
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        
        podcasts_sizer = wx.FlexGridSizer(cols=3, gap=(10, 10))
        count = 0
        max_podcasts = self.settings.home_tab.max_podcasts
        
        for category, pods in PODCASTS.items():
            if count >= max_podcasts:
                break
            for podcast_name in pods.keys():
                if count >= max_podcasts:
                    break
                display_name = podcast_name[:25] + "..." if len(podcast_name) > 25 else podcast_name
                btn = wx.Button(card, label=display_name, size=(-1, 36))
                btn.SetToolTip(podcast_name)
                btn.Bind(wx.EVT_BUTTON, lambda e, c=category, p=podcast_name: self.on_play_podcast(c, p))
                podcasts_sizer.Add(btn, 0, wx.EXPAND)
                count += 1
        
        card_sizer.Add(podcasts_sizer, 0, wx.ALL, 10)
        card.SetSizer(card_sizer)
        self.scroll_sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
    
    def _add_affiliates_section(self):
        """Add affiliates section with card styling."""
        section = self._create_section_header("🔗 Affiliates")
        self.scroll_sizer.Add(section, 0, wx.EXPAND | wx.ALL, 15)
        
        # Card container
        card = self._create_card_panel()
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        
        affiliates_sizer = wx.FlexGridSizer(cols=4, gap=(10, 10))
        for name, url in AFFILIATES.items():
            btn = wx.Button(card, label=name, size=(-1, 36))
            btn.Bind(wx.EVT_BUTTON, lambda e, u=url: webbrowser.open(u))
            affiliates_sizer.Add(btn, 0, wx.EXPAND)
        
        card_sizer.Add(affiliates_sizer, 0, wx.ALL, 10)
        card.SetSizer(card_sizer)
        self.scroll_sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
    
    def _add_recent_section(self):
        """Add recently played section with modern styling."""
        section = self._create_section_header("🕐 Recently Played")
        self.scroll_sizer.Add(section, 0, wx.EXPAND | wx.ALL, 15)
        
        # Card container
        card = self._create_card_panel()
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Recent items list with modern styling
        self.recent_list = wx.ListBox(card, style=wx.LB_SINGLE | wx.BORDER_NONE)
        self.recent_list.SetMinSize((-1, 120))
        card_sizer.Add(self.recent_list, 1, wx.EXPAND | wx.ALL, 10)
        
        card.SetSizer(card_sizer)
        self.scroll_sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
    
    def _create_section_header(self, title: str) -> wx.StaticText:
        """Create a section header with modern consistent styling."""
        header = wx.StaticText(self.scroll, label=title)
        font = header.GetFont()
        font.SetPointSize(14)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        header.SetForegroundColour(wx.Colour(26, 26, 26))  # Near black
        return header
    
    def update_recent(self, recent_items: List[str]):
        """Update the recently played list."""
        if hasattr(self, 'recent_list'):
            self.recent_list.Clear()
            self.recent_list.Append(recent_items)
    
    def refresh(self):
        """Refresh the home panel with current settings."""
        self.scroll_sizer.Clear(True)
        self._add_sections()
        self.scroll.Layout()


class StreamsPanel(wx.Panel):
    """Streams panel with modern list view and context menu."""
    
    def __init__(self, parent, on_play: Callable, on_record: Callable, on_stop_record: Callable):
        super().__init__(parent)
        self.on_play = on_play
        self.on_record = on_record
        self.on_stop_record = on_stop_record
        self.recording_stream: Optional[str] = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the streams panel UI with modern styling."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header panel
        header_panel = wx.Panel(self)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        header = wx.StaticText(header_panel, label="🎵 ACB Media Streams")
        header_font = header.GetFont()
        header_font.SetPointSize(18)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        header.SetForegroundColour(wx.Colour(0, 120, 212))
        header_sizer.Add(header, 0, wx.ALIGN_CENTER_VERTICAL)
        
        header_sizer.AddStretchSpacer()
        
        # Status indicator
        self.status_label = wx.StaticText(header_panel, label="10 streams available")
        self.status_label.SetForegroundColour(wx.Colour(102, 102, 102))
        header_sizer.Add(self.status_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        header_panel.SetSizer(header_sizer)
        sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 20)
        
        # Separator
        separator = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        # List control with modern styling
        self.list_ctrl = wx.ListCtrl(
            self, 
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE
        )
        self.list_ctrl.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        make_list_accessible(self.list_ctrl, "ACB Media Streams list", "Select a stream and press Enter to play")
        
        self.list_ctrl.InsertColumn(0, "Stream Name", width=280)
        self.list_ctrl.InsertColumn(1, "Status", width=120)
        self.list_ctrl.InsertColumn(2, "Description", width=350)
        
        # Populate streams
        for i, (name, station_id) in enumerate(STREAMS.items()):
            idx = self.list_ctrl.InsertItem(i, name)
            self.list_ctrl.SetItem(idx, 1, "● Available")
            self.list_ctrl.SetItem(idx, 2, f"Live365 Station: {station_id}")
        
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 20)
        
        # Action button panel with modern styling
        btn_panel = wx.Panel(self)
        btn_panel.SetBackgroundColour(wx.Colour(250, 250, 250))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Primary action button
        self.btn_play = wx.Button(btn_panel, label="▶  Play Stream", size=(140, 36))
        self.btn_play.SetBackgroundColour(wx.Colour(0, 120, 212))
        self.btn_play.SetForegroundColour(wx.WHITE)
        self.btn_play.Bind(wx.EVT_BUTTON, self._on_play)
        make_accessible(self.btn_play, "Play Stream", "Play the selected stream")
        btn_sizer.Add(self.btn_play, 0, wx.ALL, 10)
        
        # Secondary buttons
        self.btn_record = wx.Button(btn_panel, label="⏺  Record", size=(120, 36))
        self.btn_record.Bind(wx.EVT_BUTTON, self._on_record)
        make_accessible(self.btn_record, "Record Stream", "Start or stop recording the selected stream")
        btn_sizer.Add(self.btn_record, 0, wx.ALL, 10)
        
        self.btn_open_browser = wx.Button(btn_panel, label="🌐  Open in Browser", size=(160, 36))
        self.btn_open_browser.Bind(wx.EVT_BUTTON, self._on_open_browser)
        make_accessible(self.btn_open_browser, "Open in Browser", "Open stream page in web browser")
        btn_sizer.Add(self.btn_open_browser, 0, wx.ALL, 10)
        
        btn_panel.SetSizer(btn_sizer)
        sizer.Add(btn_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.SetSizer(sizer)
        
        # Bind events
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_play)
        self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._on_right_click)
    
    def _get_selected_stream(self) -> Optional[str]:
        """Get the currently selected stream name."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx == -1:
            return None
        return self.list_ctrl.GetItemText(idx)
    
    def _on_play(self, event):
        """Handle play button/double-click."""
        stream = self._get_selected_stream()
        if stream:
            announce(f"Playing {stream}")
            self.on_play(stream)
    
    def _on_record(self, event):
        """Handle record button."""
        stream = self._get_selected_stream()
        if not stream:
            return
        
        if self.recording_stream:
            self.on_stop_record()
            self.recording_stream = None
            self.btn_record.SetLabel("Start Recording")
        else:
            self.on_record(stream)
            self.recording_stream = stream
            self.btn_record.SetLabel("Stop Recording")
    
    def _on_open_browser(self, event):
        """Open stream in browser."""
        stream = self._get_selected_stream()
        if stream and stream in STREAMS:
            station_id = STREAMS[stream]
            url = f"https://live365.com/station/{station_id}"
            webbrowser.open(url)
    
    def _on_right_click(self, event):
        """Store the item clicked for context menu."""
        self._right_click_item = event.GetIndex()
        event.Skip()
    
    def _on_context_menu(self, event):
        """Show context menu for streams."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx == -1:
            return
        
        menu = wx.Menu()
        
        play_item = menu.Append(wx.ID_ANY, "Play Stream\tEnter")
        menu.Bind(wx.EVT_MENU, self._on_play, play_item)
        
        menu.AppendSeparator()
        
        if self.recording_stream == self.list_ctrl.GetItemText(idx):
            record_item = menu.Append(wx.ID_ANY, "Stop Recording\tCtrl+R")
        else:
            record_item = menu.Append(wx.ID_ANY, "Start Recording\tCtrl+R")
        menu.Bind(wx.EVT_MENU, self._on_record, record_item)
        
        menu.AppendSeparator()
        
        browser_item = menu.Append(wx.ID_ANY, "Open in Browser\tCtrl+B")
        menu.Bind(wx.EVT_MENU, self._on_open_browser, browser_item)
        
        copy_url = menu.Append(wx.ID_ANY, "Copy Stream URL\tCtrl+C")
        menu.Bind(wx.EVT_MENU, self._on_copy_url, copy_url)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _on_copy_url(self, event):
        """Copy stream URL to clipboard."""
        stream = self._get_selected_stream()
        if stream and stream in STREAMS:
            station_id = STREAMS[stream]
            url = f"https://live365.com/station/{station_id}"
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(url))
                wx.TheClipboard.Close()
    
    def set_stream_status(self, stream_name: str, status: str):
        """Update the status column for a stream."""
        for i in range(self.list_ctrl.GetItemCount()):
            if self.list_ctrl.GetItemText(i) == stream_name:
                self.list_ctrl.SetItem(i, 1, status)
                break
    
    def set_recording_state(self, stream_name: Optional[str]):
        """Update recording state UI."""
        self.recording_stream = stream_name
        self.btn_record.SetLabel("Stop Recording" if stream_name else "Start Recording")


class PodcastsPanel(wx.Panel):
    """Podcasts panel with tree view and episode list."""
    
    def __init__(self, parent, on_play_episode: Callable):
        super().__init__(parent)
        self.on_play_episode = on_play_episode
        self.episodes: Dict[str, List[Dict[str, Any]]] = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the podcasts panel UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(self, label="Podcasts")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        main_sizer.Add(header, 0, wx.ALL, 10)
        
        # Splitter for tree and episodes
        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        
        # Left panel - Podcast tree
        left_panel = wx.Panel(splitter)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        tree_label = wx.StaticText(left_panel, label="Browse Podcasts:")
        left_sizer.Add(tree_label, 0, wx.ALL, 5)
        
        self.tree = wx.TreeCtrl(left_panel, style=wx.TR_HAS_BUTTONS | wx.TR_SINGLE | wx.BORDER_SUNKEN)
        make_accessible(self.tree, "Podcast categories tree", "Browse podcast categories and shows")
        self._populate_tree()
        left_sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 5)
        
        left_panel.SetSizer(left_sizer)
        
        # Right panel - Episodes
        right_panel = wx.Panel(splitter)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.episode_label = wx.StaticText(right_panel, label="Select a podcast to view episodes")
        right_sizer.Add(self.episode_label, 0, wx.ALL, 5)
        
        self.episode_list = wx.ListCtrl(
            right_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        make_list_accessible(self.episode_list, "Podcast episodes list", "Select an episode and press Enter to play")
        self.episode_list.InsertColumn(0, "Episode Title", width=300)
        self.episode_list.InsertColumn(1, "Date", width=100)
        self.episode_list.InsertColumn(2, "Duration", width=80)
        right_sizer.Add(self.episode_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Episode buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_play_episode = wx.Button(right_panel, label="Play Episode")
        self.btn_play_episode.Bind(wx.EVT_BUTTON, self._on_play_episode)
        make_accessible(self.btn_play_episode, "Play Episode", "Play the selected podcast episode")
        btn_sizer.Add(self.btn_play_episode, 0, wx.RIGHT, 5)
        
        self.btn_download = wx.Button(right_panel, label="Download")
        self.btn_download.Bind(wx.EVT_BUTTON, self._on_download)
        make_accessible(self.btn_download, "Download Episode", "Download the selected episode for offline listening")
        btn_sizer.Add(self.btn_download, 0, wx.RIGHT, 5)
        
        self.btn_refresh = wx.Button(right_panel, label="Refresh Feed")
        self.btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        make_accessible(self.btn_refresh, "Refresh Feed", "Refresh the podcast feed to check for new episodes")
        btn_sizer.Add(self.btn_refresh, 0)
        
        right_sizer.Add(btn_sizer, 0, wx.ALL, 5)
        
        right_panel.SetSizer(right_sizer)
        
        # Configure splitter
        splitter.SplitVertically(left_panel, right_panel, 250)
        splitter.SetMinimumPaneSize(200)
        
        main_sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
        # Bind events
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_tree_select)
        self.tree.Bind(wx.EVT_CONTEXT_MENU, self._on_tree_context_menu)
        self.episode_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_play_episode)
        self.episode_list.Bind(wx.EVT_CONTEXT_MENU, self._on_episode_context_menu)
    
    def _populate_tree(self):
        """Populate the podcast tree control."""
        root = self.tree.AddRoot("All Podcasts")
        
        for category, podcasts in PODCASTS.items():
            category_item = self.tree.AppendItem(root, category)
            for podcast_name, feed_url in podcasts.items():
                podcast_item = self.tree.AppendItem(category_item, podcast_name)
                self.tree.SetItemData(podcast_item, {"name": podcast_name, "url": feed_url})
        
        self.tree.Expand(root)
    
    def _on_tree_select(self, event):
        """Handle podcast selection in tree."""
        item = event.GetItem()
        data = self.tree.GetItemData(item)
        
        if data and isinstance(data, dict) and "name" in data:
            self.episode_label.SetLabel(f"Episodes for: {data['name']}")
            # Load episodes (placeholder - would fetch from RSS)
            self._load_episodes(data['name'], data.get('url', ''))
    
    def _load_episodes(self, podcast_name: str, feed_url: str):
        """Load episodes for a podcast (placeholder)."""
        self.episode_list.DeleteAllItems()
        
        # Placeholder episodes
        episodes = [
            {"title": "Latest Episode", "date": "2025-01-15", "duration": "45:00"},
            {"title": "Previous Episode", "date": "2025-01-08", "duration": "38:00"},
            {"title": "Episode 3", "date": "2025-01-01", "duration": "42:00"},
        ]
        
        for i, ep in enumerate(episodes):
            idx = self.episode_list.InsertItem(i, ep["title"])
            self.episode_list.SetItem(idx, 1, ep["date"])
            self.episode_list.SetItem(idx, 2, ep["duration"])
        
        self.episodes[podcast_name] = episodes
    
    def _get_selected_podcast(self) -> Optional[Dict]:
        """Get currently selected podcast data."""
        item = self.tree.GetSelection()
        if item.IsOk():
            return self.tree.GetItemData(item)
        return None
    
    def _get_selected_episode(self) -> Optional[int]:
        """Get index of selected episode."""
        return self.episode_list.GetFirstSelected()
    
    def _on_play_episode(self, event):
        """Handle play episode button/double-click."""
        podcast = self._get_selected_podcast()
        episode_idx = self._get_selected_episode()
        
        if podcast and episode_idx != -1:
            self.on_play_episode(podcast['name'], episode_idx)
    
    def _on_download(self, event):
        """Handle download button."""
        episode_idx = self._get_selected_episode()
        if episode_idx != -1:
            # TODO: Implement download
            wx.MessageBox("Download feature coming soon!", "Download", wx.OK | wx.ICON_INFORMATION)
    
    def _on_refresh(self, event):
        """Handle refresh feed button."""
        podcast = self._get_selected_podcast()
        if podcast:
            # TODO: Implement RSS refresh
            wx.MessageBox(f"Refreshing feed for {podcast['name']}...", "Refresh", wx.OK | wx.ICON_INFORMATION)
    
    def _on_tree_context_menu(self, event):
        """Show context menu for podcast tree."""
        item = self.tree.GetSelection()
        if not item.IsOk():
            return
        
        data = self.tree.GetItemData(item)
        if not data:
            return
        
        menu = wx.Menu()
        
        play_item = menu.Append(wx.ID_ANY, "Play Latest Episode")
        menu.Bind(wx.EVT_MENU, lambda e: self._on_play_latest(), play_item)
        
        menu.AppendSeparator()
        
        refresh_item = menu.Append(wx.ID_ANY, "Refresh Feed")
        menu.Bind(wx.EVT_MENU, self._on_refresh, refresh_item)
        
        copy_item = menu.Append(wx.ID_ANY, "Copy Feed URL")
        menu.Bind(wx.EVT_MENU, self._on_copy_feed_url, copy_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _on_episode_context_menu(self, event):
        """Show context menu for episode list."""
        idx = self.episode_list.GetFirstSelected()
        if idx == -1:
            return
        
        menu = wx.Menu()
        
        play_item = menu.Append(wx.ID_ANY, "Play Episode\tEnter")
        menu.Bind(wx.EVT_MENU, self._on_play_episode, play_item)
        
        menu.AppendSeparator()
        
        download_item = menu.Append(wx.ID_ANY, "Download Episode\tCtrl+D")
        menu.Bind(wx.EVT_MENU, self._on_download, download_item)
        
        mark_item = menu.Append(wx.ID_ANY, "Mark as Played")
        menu.Bind(wx.EVT_MENU, lambda e: self._mark_played(idx), mark_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _on_play_latest(self):
        """Play the latest episode of selected podcast."""
        podcast = self._get_selected_podcast()
        if podcast:
            self.on_play_episode(podcast['name'], 0)
    
    def _on_copy_feed_url(self, event):
        """Copy feed URL to clipboard."""
        podcast = self._get_selected_podcast()
        if podcast and 'url' in podcast:
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(podcast['url']))
                wx.TheClipboard.Close()
    
    def _mark_played(self, idx: int):
        """Mark an episode as played."""
        # TODO: Implement mark as played
        pass


class ResourcesPanel(wx.Panel):
    """Resources panel with links to ACB resources."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """Build the resources panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(self, label="ACB Resources")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)
        
        # Resource list
        self.list_ctrl = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        make_list_accessible(self.list_ctrl, "ACB Resources list", "Select a resource and press Enter to open in browser")
        self.list_ctrl.InsertColumn(0, "Resource", width=200)
        self.list_ctrl.InsertColumn(1, "URL", width=400)
        
        for i, (name, url) in enumerate(RESOURCES.items()):
            idx = self.list_ctrl.InsertItem(i, name)
            self.list_ctrl.SetItem(idx, 1, url)
        
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # Button
        btn_open = wx.Button(self, label="Open in Browser")
        btn_open.Bind(wx.EVT_BUTTON, self._on_open)
        sizer.Add(btn_open, 0, wx.ALL, 10)
        
        self.SetSizer(sizer)
        
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_open)
        self.list_ctrl.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
    
    def _on_open(self, event):
        """Open selected resource in browser."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx != -1:
            url = self.list_ctrl.GetItem(idx, 1).GetText()
            webbrowser.open(url)
    
    def _on_context_menu(self, event):
        """Show context menu."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx == -1:
            return
        
        menu = wx.Menu()
        
        open_item = menu.Append(wx.ID_ANY, "Open in Browser\tEnter")
        menu.Bind(wx.EVT_MENU, self._on_open, open_item)
        
        copy_item = menu.Append(wx.ID_ANY, "Copy URL\tCtrl+C")
        menu.Bind(wx.EVT_MENU, self._on_copy_url, copy_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _on_copy_url(self, event):
        """Copy URL to clipboard."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx != -1:
            url = self.list_ctrl.GetItem(idx, 1).GetText()
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(url))
                wx.TheClipboard.Close()


class AffiliatesPanel(wx.Panel):
    """
    Enhanced Affiliates panel with State and SIG organizations.
    
    Displays detailed affiliate information from XML data sources with
    full context menu support, copy functionality, and correction suggestions.
    """
    
    def __init__(self, parent, on_suggest_correction: Optional[Callable] = None):
        """
        Initialize the affiliates panel.
        
        Args:
            parent: Parent window
            on_suggest_correction: Callback for suggest correction action
        """
        super().__init__(parent)
        self.on_suggest_correction = on_suggest_correction
        self.state_affiliates: List[Dict[str, str]] = []
        self.sig_affiliates: List[Dict[str, str]] = []
        self._build_ui()
        self._load_affiliates()
    
    def _build_ui(self):
        """Build the affiliates panel UI with tabs for States and SIGs."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(self, label="ACB Affiliates")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)
        
        description = wx.StaticText(
            self,
            label="Connect with ACB affiliate organizations. "
                  "Right-click for options or use the buttons below."
        )
        sizer.Add(description, 0, wx.LEFT | wx.BOTTOM, 10)
        
        # Notebook for State Affiliates and SIGs
        self.notebook = wx.Notebook(self)
        
        # State Affiliates tab
        self.states_panel = wx.Panel(self.notebook)
        self._build_states_tab()
        self.notebook.AddPage(self.states_panel, "State Affiliates")
        
        # Special Interest Groups tab
        self.sigs_panel = wx.Panel(self.notebook)
        self._build_sigs_tab()
        self.notebook.AddPage(self.sigs_panel, "Special Interest Groups")
        
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Button panel
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_visit = wx.Button(self, label="&Visit Website")
        self.btn_visit.SetToolTip("Open the affiliate's website in your browser")
        make_accessible(self.btn_visit, "Visit Website", "Open selected affiliate's website")
        btn_sizer.Add(self.btn_visit, 0, wx.RIGHT, 5)
        
        self.btn_copy = wx.Button(self, label="&Copy Info")
        self.btn_copy.SetToolTip("Copy all affiliate information to clipboard")
        make_accessible(self.btn_copy, "Copy Info", "Copy all information about the selected affiliate")
        btn_sizer.Add(self.btn_copy, 0, wx.RIGHT, 5)
        
        self.btn_email = wx.Button(self, label="Send &Email")
        self.btn_email.SetToolTip("Open email to the affiliate contact")
        make_accessible(self.btn_email, "Send Email", "Open your email client to contact the affiliate")
        btn_sizer.Add(self.btn_email, 0, wx.RIGHT, 5)
        
        btn_sizer.AddStretchSpacer()
        
        self.btn_correct = wx.Button(self, label="Suggest &Correction...")
        self.btn_correct.SetToolTip("Suggest a correction to this affiliate's information")
        make_accessible(
            self.btn_correct,
            "Suggest Correction",
            "Submit a correction if any information is outdated or incorrect"
        )
        btn_sizer.Add(self.btn_correct, 0)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.SetSizer(sizer)
        
        # Bind button events
        self.btn_visit.Bind(wx.EVT_BUTTON, self._on_visit_website)
        self.btn_copy.Bind(wx.EVT_BUTTON, self._on_copy_info)
        self.btn_email.Bind(wx.EVT_BUTTON, self._on_send_email)
        self.btn_correct.Bind(wx.EVT_BUTTON, self._on_suggest_correction)
    
    def _build_states_tab(self):
        """Build the State Affiliates tab."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.states_list = wx.ListCtrl(
            self.states_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        make_list_accessible(
            self.states_list,
            "State Affiliates list",
            "Select an affiliate and press Enter to visit website, or right-click for more options"
        )
        
        # Columns
        self.states_list.InsertColumn(0, "Organization", width=280)
        self.states_list.InsertColumn(1, "State", width=50)
        self.states_list.InsertColumn(2, "Contact", width=150)
        self.states_list.InsertColumn(3, "Website", width=200)
        
        sizer.Add(self.states_list, 1, wx.EXPAND | wx.ALL, 5)
        self.states_panel.SetSizer(sizer)
        
        # Bind events
        self.states_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_visit_website)
        self.states_list.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        self.states_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection_changed)
    
    def _build_sigs_tab(self):
        """Build the Special Interest Groups tab."""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sigs_list = wx.ListCtrl(
            self.sigs_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        make_list_accessible(
            self.sigs_list,
            "Special Interest Groups list",
            "Select a group and press Enter to visit website, or right-click for more options"
        )
        
        # Columns
        self.sigs_list.InsertColumn(0, "Organization", width=300)
        self.sigs_list.InsertColumn(1, "Contact", width=150)
        self.sigs_list.InsertColumn(2, "Website", width=230)
        
        sizer.Add(self.sigs_list, 1, wx.EXPAND | wx.ALL, 5)
        self.sigs_panel.SetSizer(sizer)
        
        # Bind events
        self.sigs_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_visit_website)
        self.sigs_list.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        self.sigs_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection_changed)
    
    def _load_affiliates(self):
        """Load affiliate data from XML files."""
        try:
            from .data_sync import AffiliatesParser
            from .config import get_config
            import os
            
            config = get_config()
            
            # Load state affiliates
            states_path = config.data_sources.state_affiliates.offline_path
            if os.path.exists(states_path):
                with open(states_path, 'r', encoding='utf-8') as f:
                    self.state_affiliates = AffiliatesParser.parse(f.read())
            
            # Load SIG affiliates
            sigs_path = config.data_sources.special_interest_groups.offline_path
            if os.path.exists(sigs_path):
                with open(sigs_path, 'r', encoding='utf-8') as f:
                    self.sig_affiliates = AffiliatesParser.parse(f.read())
            
            self._populate_lists()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load affiliates: {e}")
            # Fall back to basic display
            self._show_fallback_message()
    
    def _populate_lists(self):
        """Populate the list controls with affiliate data."""
        # Populate states list
        self.states_list.DeleteAllItems()
        for i, aff in enumerate(self.state_affiliates):
            idx = self.states_list.InsertItem(i, aff.get('name', ''))
            self.states_list.SetItem(idx, 1, aff.get('state', ''))
            self.states_list.SetItem(idx, 2, aff.get('contact_name', ''))
            self.states_list.SetItem(idx, 3, aff.get('website', ''))
        
        # Populate SIGs list
        self.sigs_list.DeleteAllItems()
        for i, aff in enumerate(self.sig_affiliates):
            idx = self.sigs_list.InsertItem(i, aff.get('name', ''))
            self.sigs_list.SetItem(idx, 1, aff.get('contact_name', ''))
            self.sigs_list.SetItem(idx, 2, aff.get('website', ''))
    
    def _show_fallback_message(self):
        """Show fallback message if data cannot be loaded."""
        self.states_list.DeleteAllItems()
        idx = self.states_list.InsertItem(0, "Unable to load affiliate data")
        self.states_list.SetItem(idx, 3, "https://www.acb.org/state-affiliates")
        
        self.sigs_list.DeleteAllItems()
        idx = self.sigs_list.InsertItem(0, "Unable to load affiliate data")
        self.sigs_list.SetItem(idx, 2, "https://www.acb.org/special-interest-affiliates")
    
    def _get_current_list(self) -> wx.ListCtrl:
        """Get the currently active list control."""
        if self.notebook.GetSelection() == 0:
            return self.states_list
        return self.sigs_list
    
    def _get_current_affiliates(self) -> List[Dict[str, str]]:
        """Get the affiliates list for the current tab."""
        if self.notebook.GetSelection() == 0:
            return self.state_affiliates
        return self.sig_affiliates
    
    def _get_selected_affiliate(self) -> Optional[Dict[str, str]]:
        """Get the currently selected affiliate data."""
        list_ctrl = self._get_current_list()
        affiliates = self._get_current_affiliates()
        
        idx = list_ctrl.GetFirstSelected()
        if idx == -1 or idx >= len(affiliates):
            return None
        return affiliates[idx]
    
    def _on_selection_changed(self, event):
        """Handle selection change in list."""
        affiliate = self._get_selected_affiliate()
        has_selection = affiliate is not None
        has_website = has_selection and affiliate.get('website')
        has_email = has_selection and affiliate.get('email')
        
        self.btn_visit.Enable(bool(has_website))
        self.btn_email.Enable(bool(has_email))
        self.btn_copy.Enable(has_selection)
        self.btn_correct.Enable(has_selection)
        
        event.Skip()
    
    def _on_visit_website(self, event):
        """Open affiliate website in browser."""
        affiliate = self._get_selected_affiliate()
        if affiliate and affiliate.get('website'):
            url = affiliate['website']
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
    
    def _on_send_email(self, event):
        """Open email client to contact affiliate."""
        affiliate = self._get_selected_affiliate()
        if affiliate and affiliate.get('email'):
            email = affiliate['email'].strip()
            # Handle multiple emails (take first one)
            if ' or ' in email:
                email = email.split(' or ')[0].strip()
            webbrowser.open(f"mailto:{email}")
    
    def _on_copy_info(self, event):
        """Copy all affiliate information to clipboard."""
        affiliate = self._get_selected_affiliate()
        if not affiliate:
            return
        
        # Format affiliate info for clipboard
        lines = [f"Organization: {affiliate.get('name', '')}"]
        
        if affiliate.get('type'):
            lines.append(f"Type: {affiliate['type']}")
        if affiliate.get('state'):
            lines.append(f"State: {affiliate['state']}")
        if affiliate.get('contact_name'):
            lines.append(f"Contact: {affiliate['contact_name']}")
        if affiliate.get('email'):
            lines.append(f"Email: {affiliate['email']}")
        if affiliate.get('phone'):
            lines.append(f"Phone: {affiliate['phone']}")
        if affiliate.get('website'):
            lines.append(f"Website: {affiliate['website']}")
        if affiliate.get('twitter'):
            lines.append(f"X (Twitter): {affiliate['twitter']}")
        if affiliate.get('facebook'):
            lines.append(f"Facebook: {affiliate['facebook']}")
        
        text = "\n".join(lines)
        
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            announce("Affiliate information copied to clipboard")
    
    def _on_copy_url(self, event):
        """Copy website URL to clipboard."""
        affiliate = self._get_selected_affiliate()
        if affiliate and affiliate.get('website'):
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(affiliate['website']))
                wx.TheClipboard.Close()
                announce("Website URL copied to clipboard")
    
    def _on_copy_email(self, event):
        """Copy email address to clipboard."""
        affiliate = self._get_selected_affiliate()
        if affiliate and affiliate.get('email'):
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(affiliate['email']))
                wx.TheClipboard.Close()
                announce("Email address copied to clipboard")
    
    def _on_copy_phone(self, event):
        """Copy phone number to clipboard."""
        affiliate = self._get_selected_affiliate()
        if affiliate and affiliate.get('phone'):
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(affiliate['phone']))
                wx.TheClipboard.Close()
                announce("Phone number copied to clipboard")
    
    def _on_suggest_correction(self, event):
        """Open the suggest correction dialog."""
        if self.on_suggest_correction:
            affiliate = self._get_selected_affiliate()
            self.on_suggest_correction(affiliate)
        else:
            # Fallback: show the dialog directly
            self._show_correction_dialog()
    
    def _show_correction_dialog(self):
        """Show the affiliate correction dialog."""
        try:
            from .affiliate_feedback import (
                AffiliateInfo, show_affiliate_correction_dialog
            )
            
            # Convert all affiliates to AffiliateInfo objects
            all_affiliates = []
            for aff in self.state_affiliates:
                all_affiliates.append(AffiliateInfo.from_dict(aff))
            for aff in self.sig_affiliates:
                all_affiliates.append(AffiliateInfo.from_dict(aff))
            
            # Get selected affiliate
            selected = self._get_selected_affiliate()
            selected_info = AffiliateInfo.from_dict(selected) if selected else None
            
            show_affiliate_correction_dialog(self, all_affiliates, selected_info)
            
        except ImportError as e:
            wx.MessageBox(
                f"Could not open correction dialog: {e}",
                "Error",
                wx.OK | wx.ICON_ERROR,
                self
            )
    
    def _on_context_menu(self, event):
        """Show context menu with all available actions."""
        affiliate = self._get_selected_affiliate()
        if not affiliate:
            return
        
        menu = wx.Menu()
        
        # Visit website
        if affiliate.get('website'):
            visit_item = menu.Append(wx.ID_ANY, "Visit &Website\tEnter")
            menu.Bind(wx.EVT_MENU, self._on_visit_website, visit_item)
        
        # Send email
        if affiliate.get('email'):
            email_item = menu.Append(wx.ID_ANY, "Send &Email")
            menu.Bind(wx.EVT_MENU, self._on_send_email, email_item)
        
        menu.AppendSeparator()
        
        # Copy submenu
        copy_menu = wx.Menu()
        
        copy_all = copy_menu.Append(wx.ID_ANY, "Copy &All Info\tCtrl+C")
        menu.Bind(wx.EVT_MENU, self._on_copy_info, copy_all)
        
        if affiliate.get('website'):
            copy_url = copy_menu.Append(wx.ID_ANY, "Copy &Website URL")
            menu.Bind(wx.EVT_MENU, self._on_copy_url, copy_url)
        
        if affiliate.get('email'):
            copy_email = copy_menu.Append(wx.ID_ANY, "Copy &Email Address")
            menu.Bind(wx.EVT_MENU, self._on_copy_email, copy_email)
        
        if affiliate.get('phone'):
            copy_phone = copy_menu.Append(wx.ID_ANY, "Copy &Phone Number")
            menu.Bind(wx.EVT_MENU, self._on_copy_phone, copy_phone)
        
        menu.AppendSubMenu(copy_menu, "&Copy")
        
        menu.AppendSeparator()
        
        # Social media
        if affiliate.get('twitter') or affiliate.get('facebook'):
            social_menu = wx.Menu()
            
            if affiliate.get('twitter'):
                twitter_item = social_menu.Append(wx.ID_ANY, "Open &X (Twitter)")
                menu.Bind(
                    wx.EVT_MENU,
                    lambda e: self._open_social('twitter', affiliate),
                    twitter_item
                )
            
            if affiliate.get('facebook'):
                fb_item = social_menu.Append(wx.ID_ANY, "Open &Facebook")
                menu.Bind(
                    wx.EVT_MENU,
                    lambda e: self._open_social('facebook', affiliate),
                    fb_item
                )
            
            menu.AppendSubMenu(social_menu, "&Social Media")
            menu.AppendSeparator()
        
        # Suggest correction
        correct_item = menu.Append(wx.ID_ANY, "Suggest &Correction...\tCtrl+Shift+E")
        menu.Bind(wx.EVT_MENU, self._on_suggest_correction, correct_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _open_social(self, platform: str, affiliate: Dict[str, str]):
        """Open social media link."""
        url = affiliate.get(platform, '')
        if url:
            # Handle twitter handles vs full URLs
            if platform == 'twitter' and not url.startswith('http'):
                url = f"https://x.com/{url.lstrip('@')}"
            elif platform == 'facebook' and not url.startswith('http'):
                url = f"https://facebook.com/{url}"
            webbrowser.open(url)
    
    def refresh(self):
        """Refresh the affiliate data from XML files."""
        self._load_affiliates()
    
    def get_all_affiliates_as_info(self) -> List:
        """Get all affiliates as AffiliateInfo objects for the correction dialog."""
        try:
            from .affiliate_feedback import AffiliateInfo
            
            all_affiliates = []
            for aff in self.state_affiliates:
                all_affiliates.append(AffiliateInfo.from_dict(aff))
            for aff in self.sig_affiliates:
                all_affiliates.append(AffiliateInfo.from_dict(aff))
            return all_affiliates
        except ImportError:
            return []
    
    def get_selected_affiliate_as_info(self):
        """Get the selected affiliate as an AffiliateInfo object."""
        try:
            from .affiliate_feedback import AffiliateInfo
            
            selected = self._get_selected_affiliate()
            if selected:
                return AffiliateInfo.from_dict(selected)
            return None
        except ImportError:
            return None
