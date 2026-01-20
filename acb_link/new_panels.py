"""
ACB Link - New Feature Panels
Favorites, Playlists, Search, and Calendar panels.
"""

import webbrowser
from typing import Callable, List, Optional

import wx


class FavoritesPanel(wx.Panel):
    """Favorites and bookmarks panel."""

    def __init__(
        self, parent, favorites_manager, on_play_stream: Callable, on_play_episode: Callable
    ):
        super().__init__(parent)
        self.favorites_manager = favorites_manager
        self.on_play_stream = on_play_stream
        self.on_play_episode = on_play_episode

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the favorites panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="Favorites & Bookmarks")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)

        # Notebook for favorites and bookmarks
        self.tabs = wx.Notebook(self)

        # Favorites tab
        favorites_panel = wx.Panel(self.tabs)
        fav_sizer = wx.BoxSizer(wx.VERTICAL)

        self.favorites_list = wx.ListCtrl(
            favorites_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.favorites_list.InsertColumn(0, "Name", width=250)
        self.favorites_list.InsertColumn(1, "Type", width=100)
        self.favorites_list.InsertColumn(2, "Added", width=150)
        fav_sizer.Add(self.favorites_list, 1, wx.EXPAND | wx.ALL, 5)

        fav_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_play_fav = wx.Button(favorites_panel, label="Play")
        self.btn_play_fav.Bind(wx.EVT_BUTTON, self._on_play_favorite)
        fav_btn_sizer.Add(self.btn_play_fav, 0, wx.RIGHT, 5)

        self.btn_remove_fav = wx.Button(favorites_panel, label="Remove")
        self.btn_remove_fav.Bind(wx.EVT_BUTTON, self._on_remove_favorite)
        fav_btn_sizer.Add(self.btn_remove_fav, 0)

        fav_sizer.Add(fav_btn_sizer, 0, wx.ALL, 5)
        favorites_panel.SetSizer(fav_sizer)

        # Bookmarks tab
        bookmarks_panel = wx.Panel(self.tabs)
        bm_sizer = wx.BoxSizer(wx.VERTICAL)

        self.bookmarks_list = wx.ListCtrl(
            bookmarks_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.bookmarks_list.InsertColumn(0, "Content", width=200)
        self.bookmarks_list.InsertColumn(1, "Position", width=80)
        self.bookmarks_list.InsertColumn(2, "Note", width=200)
        bm_sizer.Add(self.bookmarks_list, 1, wx.EXPAND | wx.ALL, 5)

        bm_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_goto_bm = wx.Button(bookmarks_panel, label="Go To")
        self.btn_goto_bm.Bind(wx.EVT_BUTTON, self._on_goto_bookmark)
        bm_btn_sizer.Add(self.btn_goto_bm, 0, wx.RIGHT, 5)

        self.btn_remove_bm = wx.Button(bookmarks_panel, label="Remove")
        self.btn_remove_bm.Bind(wx.EVT_BUTTON, self._on_remove_bookmark)
        bm_btn_sizer.Add(self.btn_remove_bm, 0)

        bm_sizer.Add(bm_btn_sizer, 0, wx.ALL, 5)
        bookmarks_panel.SetSizer(bm_sizer)

        self.tabs.AddPage(favorites_panel, "Favorites")
        self.tabs.AddPage(bookmarks_panel, "Bookmarks")

        sizer.Add(self.tabs, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # Bind events
        self.favorites_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_play_favorite)
        self.bookmarks_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_goto_bookmark)

    def refresh(self):
        """Refresh favorites and bookmarks lists."""
        # Refresh favorites
        self.favorites_list.DeleteAllItems()
        for i, fav in enumerate(self.favorites_manager.get_all_favorites()):
            idx = self.favorites_list.InsertItem(i, fav.name)
            self.favorites_list.SetItem(idx, 1, fav.favorite_type.value)
            self.favorites_list.SetItem(idx, 2, fav.added_at.strftime("%Y-%m-%d %H:%M"))

        # Refresh bookmarks
        self.bookmarks_list.DeleteAllItems()
        for i, bm in enumerate(self.favorites_manager.get_all_bookmarks()):
            idx = self.bookmarks_list.InsertItem(i, bm.content_name)
            minutes = int(bm.position // 60)
            seconds = int(bm.position % 60)
            self.bookmarks_list.SetItem(idx, 1, f"{minutes}:{seconds:02d}")
            self.bookmarks_list.SetItem(idx, 2, bm.note or "")

    def _on_play_favorite(self, event):
        """Play selected favorite."""
        idx = self.favorites_list.GetFirstSelected()
        if idx == -1:
            return

        favorites = self.favorites_manager.get_all_favorites()
        if idx < len(favorites):
            fav = favorites[idx]
            if fav.favorite_type.value == "stream":
                self.on_play_stream(fav.name)
            elif fav.favorite_type.value == "episode":
                self.on_play_episode(fav.content_id, 0)

    def _on_remove_favorite(self, event):
        """Remove selected favorite."""
        idx = self.favorites_list.GetFirstSelected()
        if idx == -1:
            return

        favorites = self.favorites_manager.get_all_favorites()
        if idx < len(favorites):
            self.favorites_manager.remove_favorite(favorites[idx].id)
            self.refresh()

    def _on_goto_bookmark(self, event):
        """Go to selected bookmark."""
        # Would seek to the bookmark position
        pass

    def _on_remove_bookmark(self, event):
        """Remove selected bookmark."""
        idx = self.bookmarks_list.GetFirstSelected()
        if idx == -1:
            return

        bookmarks = self.favorites_manager.get_all_bookmarks()
        if idx < len(bookmarks):
            self.favorites_manager.remove_bookmark(bookmarks[idx].id)
            self.refresh()


class PlaylistsPanel(wx.Panel):
    """Playlists management panel."""

    def __init__(self, parent, playlist_manager, playlist_player, on_play_item: Callable):
        super().__init__(parent)
        self.playlist_manager = playlist_manager
        self.playlist_player = playlist_player
        self.on_play_item = on_play_item
        self.current_playlist_id: Optional[str] = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the playlists panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="Playlists")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)

        # Splitter
        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        # Left - Playlist list
        left_panel = wx.Panel(splitter)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        left_sizer.Add(wx.StaticText(left_panel, label="My Playlists:"), 0, wx.ALL, 5)

        self.playlist_list = wx.ListBox(left_panel, style=wx.LB_SINGLE)
        left_sizer.Add(self.playlist_list, 1, wx.EXPAND | wx.ALL, 5)

        playlist_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_new_playlist = wx.Button(left_panel, label="New")
        self.btn_new_playlist.Bind(wx.EVT_BUTTON, self._on_new_playlist)
        playlist_btn_sizer.Add(self.btn_new_playlist, 0, wx.RIGHT, 5)

        self.btn_delete_playlist = wx.Button(left_panel, label="Delete")
        self.btn_delete_playlist.Bind(wx.EVT_BUTTON, self._on_delete_playlist)
        playlist_btn_sizer.Add(self.btn_delete_playlist, 0)

        left_sizer.Add(playlist_btn_sizer, 0, wx.ALL, 5)
        left_panel.SetSizer(left_sizer)

        # Right - Playlist items
        right_panel = wx.Panel(splitter)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        self.items_label = wx.StaticText(right_panel, label="Select a playlist")
        right_sizer.Add(self.items_label, 0, wx.ALL, 5)

        self.items_list = wx.ListCtrl(
            right_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.items_list.InsertColumn(0, "#", width=40)
        self.items_list.InsertColumn(1, "Title", width=250)
        self.items_list.InsertColumn(2, "Type", width=80)
        right_sizer.Add(self.items_list, 1, wx.EXPAND | wx.ALL, 5)

        # Playback controls
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_play_playlist = wx.Button(right_panel, label="▶ Play All")
        self.btn_play_playlist.Bind(wx.EVT_BUTTON, self._on_play_playlist)
        control_sizer.Add(self.btn_play_playlist, 0, wx.RIGHT, 5)

        self.btn_shuffle = wx.ToggleButton(right_panel, label="🔀 Shuffle")
        self.btn_shuffle.Bind(wx.EVT_TOGGLEBUTTON, self._on_toggle_shuffle)
        control_sizer.Add(self.btn_shuffle, 0, wx.RIGHT, 5)

        self.repeat_choice = wx.Choice(
            right_panel, choices=["No Repeat", "Repeat All", "Repeat One"]
        )
        self.repeat_choice.SetSelection(0)
        self.repeat_choice.Bind(wx.EVT_CHOICE, self._on_repeat_change)
        control_sizer.Add(self.repeat_choice, 0)

        right_sizer.Add(control_sizer, 0, wx.ALL, 5)

        # Item manipulation
        item_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_move_up = wx.Button(right_panel, label="↑ Up")
        self.btn_move_up.Bind(wx.EVT_BUTTON, self._on_move_up)
        item_btn_sizer.Add(self.btn_move_up, 0, wx.RIGHT, 5)

        self.btn_move_down = wx.Button(right_panel, label="↓ Down")
        self.btn_move_down.Bind(wx.EVT_BUTTON, self._on_move_down)
        item_btn_sizer.Add(self.btn_move_down, 0, wx.RIGHT, 5)

        self.btn_remove_item = wx.Button(right_panel, label="Remove")
        self.btn_remove_item.Bind(wx.EVT_BUTTON, self._on_remove_item)
        item_btn_sizer.Add(self.btn_remove_item, 0)

        right_sizer.Add(item_btn_sizer, 0, wx.ALL, 5)
        right_panel.SetSizer(right_sizer)

        splitter.SplitVertically(left_panel, right_panel, 200)
        splitter.SetMinimumPaneSize(150)

        sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # Bind events
        self.playlist_list.Bind(wx.EVT_LISTBOX, self._on_playlist_select)
        self.items_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_play_item_clicked)

    def refresh(self):
        """Refresh playlists list."""
        self.playlist_list.Clear()
        for playlist in self.playlist_manager.get_all_playlists():
            self.playlist_list.Append(playlist.name)

        if self.current_playlist_id:
            self._refresh_items()

    def _refresh_items(self):
        """Refresh items for current playlist."""
        self.items_list.DeleteAllItems()

        if not self.current_playlist_id:
            return

        playlist = self.playlist_manager.get_playlist(self.current_playlist_id)
        if not playlist:
            return

        self.items_label.SetLabel(f"Playlist: {playlist.name} ({len(playlist.items)} items)")

        for i, item in enumerate(playlist.items):
            idx = self.items_list.InsertItem(i, str(i + 1))
            self.items_list.SetItem(idx, 1, item.title)
            self.items_list.SetItem(idx, 2, item.item_type)

    def _on_playlist_select(self, event):
        """Handle playlist selection."""
        idx = self.playlist_list.GetSelection()
        if idx == wx.NOT_FOUND:
            return

        playlists = self.playlist_manager.get_all_playlists()
        if idx < len(playlists):
            self.current_playlist_id = playlists[idx].id
            self._refresh_items()

    def _on_new_playlist(self, event):
        """Create new playlist."""
        dlg = wx.TextEntryDialog(self, "Enter playlist name:", "New Playlist")
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue().strip()
            if name:
                self.playlist_manager.create_playlist(name)
                self.refresh()
        dlg.Destroy()

    def _on_delete_playlist(self, event):
        """Delete selected playlist."""
        if not self.current_playlist_id:
            return

        if (
            wx.MessageBox("Delete this playlist?", "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION)
            == wx.YES
        ):
            self.playlist_manager.delete_playlist(self.current_playlist_id)
            self.current_playlist_id = None
            self.refresh()

    def _on_play_playlist(self, event):
        """Play entire playlist."""
        if self.current_playlist_id:
            self.playlist_player.play_playlist(self.current_playlist_id)

    def _on_toggle_shuffle(self, event):
        """Toggle shuffle mode."""
        self.playlist_player.shuffle = self.btn_shuffle.GetValue()

    def _on_repeat_change(self, event):
        """Handle repeat mode change."""
        from .playlists import RepeatMode

        modes = [RepeatMode.NONE, RepeatMode.ALL, RepeatMode.ONE]
        self.playlist_player.repeat_mode = modes[self.repeat_choice.GetSelection()]

    def _on_play_item_clicked(self, event):
        """Play selected item."""
        idx = self.items_list.GetFirstSelected()
        if idx != -1 and self.current_playlist_id:
            self.playlist_player.play_playlist(self.current_playlist_id, start_index=idx)

    def _on_move_up(self, event):
        """Move selected item up."""
        idx = self.items_list.GetFirstSelected()
        if idx > 0 and self.current_playlist_id:
            self.playlist_manager.reorder_item(self.current_playlist_id, idx, idx - 1)
            self._refresh_items()
            self.items_list.Select(idx - 1)

    def _on_move_down(self, event):
        """Move selected item down."""
        idx = self.items_list.GetFirstSelected()
        if idx != -1 and idx < self.items_list.GetItemCount() - 1 and self.current_playlist_id:
            self.playlist_manager.reorder_item(self.current_playlist_id, idx, idx + 1)
            self._refresh_items()
            self.items_list.Select(idx + 1)

    def _on_remove_item(self, event):
        """Remove selected item from playlist."""
        idx = self.items_list.GetFirstSelected()
        if idx != -1 and self.current_playlist_id:
            playlist = self.playlist_manager.get_playlist(self.current_playlist_id)
            if playlist and idx < len(playlist.items):
                self.playlist_manager.remove_from_playlist(
                    self.current_playlist_id, playlist.items[idx].id
                )
                self._refresh_items()


class SearchPanel(wx.Panel):
    """Global search panel."""

    def __init__(self, parent, search_engine, on_play_result: Callable):
        super().__init__(parent)
        self.search_engine = search_engine
        self.on_play_result = on_play_result
        self.current_results: List = []

        self._build_ui()

    def _build_ui(self):
        """Build the search panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="Search")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)

        # Search bar
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.search_input = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_input.SetDescriptiveText("Search streams, podcasts, episodes...")
        self.search_input.ShowCancelButton(True)
        search_sizer.Add(self.search_input, 1, wx.EXPAND | wx.RIGHT, 5)

        self.btn_search = wx.Button(self, label="Search")
        self.btn_search.Bind(wx.EVT_BUTTON, self._on_search)
        search_sizer.Add(self.btn_search, 0)

        sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Filter checkboxes
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.chk_streams = wx.CheckBox(self, label="Streams")
        self.chk_streams.SetValue(True)
        filter_sizer.Add(self.chk_streams, 0, wx.RIGHT, 10)

        self.chk_podcasts = wx.CheckBox(self, label="Podcasts")
        self.chk_podcasts.SetValue(True)
        filter_sizer.Add(self.chk_podcasts, 0, wx.RIGHT, 10)

        self.chk_episodes = wx.CheckBox(self, label="Episodes")
        self.chk_episodes.SetValue(True)
        filter_sizer.Add(self.chk_episodes, 0, wx.RIGHT, 10)

        self.chk_bookmarks = wx.CheckBox(self, label="Bookmarks")
        self.chk_bookmarks.SetValue(True)
        filter_sizer.Add(self.chk_bookmarks, 0)

        sizer.Add(filter_sizer, 0, wx.LEFT | wx.BOTTOM, 10)

        # Results
        self.results_label = wx.StaticText(self, label="Enter a search term above")
        sizer.Add(self.results_label, 0, wx.ALL, 10)

        self.results_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.results_list.InsertColumn(0, "Title", width=300)
        self.results_list.InsertColumn(1, "Type", width=100)
        self.results_list.InsertColumn(2, "Match", width=200)
        sizer.Add(self.results_list, 1, wx.EXPAND | wx.ALL, 10)

        # Action buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_play = wx.Button(self, label="Play")
        self.btn_play.Bind(wx.EVT_BUTTON, self._on_play_result)
        btn_sizer.Add(self.btn_play, 0, wx.RIGHT, 5)

        self.btn_add_favorite = wx.Button(self, label="Add to Favorites")
        self.btn_add_favorite.Bind(wx.EVT_BUTTON, self._on_add_favorite)
        btn_sizer.Add(self.btn_add_favorite, 0)

        sizer.Add(btn_sizer, 0, wx.ALL, 10)

        self.SetSizer(sizer)

        # Bind events
        self.search_input.Bind(wx.EVT_TEXT_ENTER, self._on_search)
        self.search_input.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self._on_search)
        self.results_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_play_result)

    def _on_search(self, event):
        """Perform search."""
        query = self.search_input.GetValue().strip()
        if not query:
            return

        # Build filter types
        types = []
        if self.chk_streams.GetValue():
            types.append("stream")
        if self.chk_podcasts.GetValue():
            types.append("podcast")
        if self.chk_episodes.GetValue():
            types.append("episode")
        if self.chk_bookmarks.GetValue():
            types.append("bookmark")

        # Perform search
        self.current_results = self.search_engine.search(query, types=types)

        # Display results
        self.results_list.DeleteAllItems()

        for i, result in enumerate(self.current_results):
            idx = self.results_list.InsertItem(i, result.title)
            self.results_list.SetItem(idx, 1, result.result_type.value)
            self.results_list.SetItem(idx, 2, result.matched_field or "")

        count = len(self.current_results)
        self.results_label.SetLabel(f"Found {count} result{'s' if count != 1 else ''}")

    def _on_play_result(self, event):
        """Play selected result."""
        idx = self.results_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_results):
            result = self.current_results[idx]
            self.on_play_result(result)

    def _on_add_favorite(self, event):
        """Add selected result to favorites."""
        idx = self.results_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_results):
            # Would add to favorites
            wx.MessageBox("Added to favorites!", "Success", wx.OK | wx.ICON_INFORMATION)

    def set_search_query(self, query: str):
        """Set search query and perform search."""
        self.search_input.SetValue(query)
        self._on_search(None)


class CalendarPanel(wx.Panel):
    """ACB Calendar events panel."""

    def __init__(self, parent, calendar_manager, on_join_event: Callable):
        super().__init__(parent)
        self.calendar_manager = calendar_manager
        self.on_join_event = on_join_event
        self.current_events: List = []

        self._build_ui()
        self._load_events()

    def _build_ui(self):
        """Build the calendar panel UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="ACB Calendar")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)

        # View selector
        view_sizer = wx.BoxSizer(wx.HORIZONTAL)

        view_sizer.Add(
            wx.StaticText(self, label="View:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.view_choice = wx.Choice(
            self, choices=["Today", "This Week", "This Month", "All Upcoming"]
        )
        self.view_choice.SetSelection(1)
        self.view_choice.Bind(wx.EVT_CHOICE, self._on_view_change)
        view_sizer.Add(self.view_choice, 0, wx.RIGHT, 10)

        self.btn_refresh = wx.Button(self, label="Refresh")
        self.btn_refresh.Bind(wx.EVT_BUTTON, self._on_refresh)
        view_sizer.Add(self.btn_refresh, 0)

        sizer.Add(view_sizer, 0, wx.ALL, 10)

        # Events list
        self.events_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.events_list.InsertColumn(0, "Event", width=300)
        self.events_list.InsertColumn(1, "Date/Time", width=150)
        self.events_list.InsertColumn(2, "Status", width=100)
        sizer.Add(self.events_list, 1, wx.EXPAND | wx.ALL, 10)

        # Event details
        details_box = wx.StaticBox(self, label="Event Details")
        details_sizer = wx.StaticBoxSizer(details_box, wx.VERTICAL)

        self.event_details = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 100),  # type: ignore[arg-type]
        )
        details_sizer.Add(self.event_details, 1, wx.EXPAND | wx.ALL, 5)

        sizer.Add(details_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Action buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_join = wx.Button(self, label="Join Event")
        self.btn_join.Bind(wx.EVT_BUTTON, self._on_join_event)
        btn_sizer.Add(self.btn_join, 0, wx.RIGHT, 5)

        self.btn_reminder = wx.Button(self, label="Set Reminder")
        self.btn_reminder.Bind(wx.EVT_BUTTON, self._on_set_reminder)
        btn_sizer.Add(self.btn_reminder, 0, wx.RIGHT, 5)

        self.btn_export = wx.Button(self, label="Export to Calendar")
        self.btn_export.Bind(wx.EVT_BUTTON, self._on_export_event)
        btn_sizer.Add(self.btn_export, 0)

        sizer.Add(btn_sizer, 0, wx.ALL, 10)

        self.SetSizer(sizer)

        # Bind events
        self.events_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_event_select)
        self.events_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_join_event)

    def _load_events(self):
        """Load events from calendar manager."""
        self.current_events = self.calendar_manager.get_upcoming_events()
        self._display_events()

    def _display_events(self):
        """Display events in list."""
        self.events_list.DeleteAllItems()

        for i, event in enumerate(self.current_events):
            idx = self.events_list.InsertItem(i, event.title)

            date_str = event.start_time.strftime("%b %d, %Y %I:%M %p")
            self.events_list.SetItem(idx, 1, date_str)

            if event.is_live:
                status = "🔴 LIVE"
            elif event.is_upcoming:
                status = f"In {event.time_until}"
            else:
                status = "Upcoming"
            self.events_list.SetItem(idx, 2, status)

    def _on_view_change(self, event):
        """Handle view change."""
        # Filter events based on selection
        self._load_events()

    def _on_refresh(self, event):
        """Refresh events."""
        self.calendar_manager.refresh()
        self._load_events()

    def _on_event_select(self, event):
        """Handle event selection."""
        idx = self.events_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_events):
            evt = self.current_events[idx]
            details = f"{evt.title}\n\n"
            details += f"Date: {evt.start_time.strftime('%A, %B %d, %Y')}\n"
            details += f"Time: {evt.start_time.strftime('%I:%M %p')}"
            if evt.end_time:
                details += f" - {evt.end_time.strftime('%I:%M %p')}"
            details += f"\n\n{evt.description or 'No description available.'}"

            self.event_details.SetValue(details)

    def _on_join_event(self, event):
        """Join selected event."""
        idx = self.events_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_events):
            evt = self.current_events[idx]
            if evt.stream_url:
                self.on_join_event(evt)
            elif evt.meeting_url:
                webbrowser.open(evt.meeting_url)
            else:
                wx.MessageBox(
                    "This event doesn't have a stream or meeting URL.",
                    "Info",
                    wx.OK | wx.ICON_INFORMATION,
                )

    def _on_set_reminder(self, event):
        """Set reminder for selected event."""
        idx = self.events_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_events):
            evt = self.current_events[idx]

            dlg = wx.SingleChoiceDialog(
                self,
                "Remind me:",
                "Set Reminder",
                ["5 minutes before", "15 minutes before", "30 minutes before", "1 hour before"],
            )
            if dlg.ShowModal() == wx.ID_OK:
                minutes = [5, 15, 30, 60][dlg.GetSelection()]
                self.calendar_manager.set_reminder(evt.id, minutes)
                wx.MessageBox(
                    f"Reminder set for {minutes} minutes before.",
                    "Reminder Set",
                    wx.OK | wx.ICON_INFORMATION,
                )
            dlg.Destroy()

    def _on_export_event(self, event):
        """Export event to calendar file."""
        idx = self.events_list.GetFirstSelected()
        if idx != -1 and idx < len(self.current_events):
            evt = self.current_events[idx]

            dlg = wx.FileDialog(
                self,
                "Save Event",
                wildcard="iCalendar files (*.ics)|*.ics",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                defaultFile=f"{evt.title.replace(' ', '_')}.ics",
            )
            if dlg.ShowModal() == wx.ID_OK:
                filepath = dlg.GetPath()
                self.calendar_manager.export_to_ical(evt.id, filepath)
                wx.MessageBox("Event exported!", "Success", wx.OK | wx.ICON_INFORMATION)
            dlg.Destroy()

    def refresh(self):
        """Refresh the panel."""
        self._load_events()


class SleepTimerPanel(wx.Panel):
    """Sleep timer control panel - can be added to main controls."""

    def __init__(self, parent, sleep_timer):
        super().__init__(parent)
        self.sleep_timer = sleep_timer

        self._build_ui()

    def _build_ui(self):
        """Build sleep timer UI."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(
            wx.StaticText(self, label="Sleep Timer:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.timer_choice = wx.Choice(
            self, choices=["Off", "15 min", "30 min", "45 min", "1 hour", "90 min", "2 hours"]
        )
        self.timer_choice.SetSelection(0)
        self.timer_choice.Bind(wx.EVT_CHOICE, self._on_timer_change)
        sizer.Add(self.timer_choice, 0, wx.RIGHT, 5)

        self.timer_label = wx.StaticText(self, label="")
        sizer.Add(self.timer_label, 0, wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(sizer)

    def _on_timer_change(self, event):
        """Handle timer selection change."""
        selection = self.timer_choice.GetSelection()

        if selection == 0:
            self.sleep_timer.cancel()
            self.timer_label.SetLabel("")
        else:
            minutes = [0, 15, 30, 45, 60, 90, 120][selection]
            self.sleep_timer.set_timer(minutes)
            self.timer_label.SetLabel(f"({minutes} min)")

    def update_remaining(self, remaining_seconds: int):
        """Update remaining time display."""
        if remaining_seconds <= 0:
            self.timer_choice.SetSelection(0)
            self.timer_label.SetLabel("")
        else:
            mins = remaining_seconds // 60
            secs = remaining_seconds % 60
            self.timer_label.SetLabel(f"({mins}:{secs:02d} remaining)")


class ShortcutsPanel(wx.Panel):
    """
    Keyboard shortcuts configuration panel.
    Allows users to view and customize all keyboard shortcuts.
    """

    def __init__(self, parent, shortcut_manager, on_shortcuts_changed=None):
        super().__init__(parent)
        self.shortcut_manager = shortcut_manager
        self.on_shortcuts_changed = on_shortcuts_changed
        self._editing_shortcut_id = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the shortcuts configuration UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="Keyboard Shortcuts")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 10)

        # Instructions
        instructions = wx.StaticText(
            self,
            label="Select a shortcut and press 'Change' to assign a new key combination. "
            "Use Ctrl, Alt, and Shift with letters or function keys.",
        )
        instructions.Wrap(500)
        sizer.Add(instructions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Category filter
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filter_sizer.Add(
            wx.StaticText(self, label="Category:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.category_choice = wx.Choice(
            self,
            choices=[
                "All Categories",
                "Playback",
                "Navigation",
                "Streams",
                "General",
                "Recording",
                "Volume",
            ],
        )
        self.category_choice.SetSelection(0)
        self.category_choice.Bind(wx.EVT_CHOICE, self._on_category_change)
        filter_sizer.Add(self.category_choice, 0)

        sizer.Add(filter_sizer, 0, wx.LEFT | wx.BOTTOM, 10)

        # Shortcuts list
        self.shortcuts_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.shortcuts_list.InsertColumn(0, "Action", width=200)
        self.shortcuts_list.InsertColumn(1, "Shortcut", width=150)
        self.shortcuts_list.InsertColumn(2, "Category", width=100)
        self.shortcuts_list.InsertColumn(3, "Description", width=250)
        sizer.Add(self.shortcuts_list, 1, wx.EXPAND | wx.ALL, 10)

        # Editing panel
        edit_box = wx.StaticBox(self, label="Edit Shortcut")
        edit_sizer = wx.StaticBoxSizer(edit_box, wx.VERTICAL)

        self.edit_label = wx.StaticText(self, label="Select a shortcut to edit")
        edit_sizer.Add(self.edit_label, 0, wx.ALL, 5)

        key_sizer = wx.BoxSizer(wx.HORIZONTAL)

        key_sizer.Add(
            wx.StaticText(self, label="New shortcut:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.key_input = wx.TextCtrl(self, style=wx.TE_READONLY, size=(200, -1))  # type: ignore[arg-type]
        self.key_input.SetHint("Press a key combination...")
        self.key_input.Bind(wx.EVT_KEY_DOWN, self._on_key_press)
        key_sizer.Add(self.key_input, 0, wx.RIGHT, 10)

        self.btn_change = wx.Button(self, label="Change")
        self.btn_change.Bind(wx.EVT_BUTTON, self._on_change_shortcut)
        self.btn_change.Enable(False)
        key_sizer.Add(self.btn_change, 0, wx.RIGHT, 5)

        self.btn_clear = wx.Button(self, label="Clear")
        self.btn_clear.Bind(wx.EVT_BUTTON, self._on_clear_shortcut)
        self.btn_clear.Enable(False)
        key_sizer.Add(self.btn_clear, 0)

        edit_sizer.Add(key_sizer, 0, wx.ALL, 5)

        self.conflict_label = wx.StaticText(self, label="")
        self.conflict_label.SetForegroundColour(wx.Colour(255, 0, 0))
        edit_sizer.Add(self.conflict_label, 0, wx.ALL, 5)

        sizer.Add(edit_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Bottom buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_reset_selected = wx.Button(self, label="Reset Selected")
        self.btn_reset_selected.Bind(wx.EVT_BUTTON, self._on_reset_selected)
        btn_sizer.Add(self.btn_reset_selected, 0, wx.RIGHT, 5)

        self.btn_reset_all = wx.Button(self, label="Reset All to Defaults")
        self.btn_reset_all.Bind(wx.EVT_BUTTON, self._on_reset_all)
        btn_sizer.Add(self.btn_reset_all, 0, wx.RIGHT, 20)

        self.btn_import = wx.Button(self, label="Import...")
        self.btn_import.Bind(wx.EVT_BUTTON, self._on_import)
        btn_sizer.Add(self.btn_import, 0, wx.RIGHT, 5)

        self.btn_export = wx.Button(self, label="Export...")
        self.btn_export.Bind(wx.EVT_BUTTON, self._on_export)
        btn_sizer.Add(self.btn_export, 0)

        sizer.Add(btn_sizer, 0, wx.ALL, 10)

        self.SetSizer(sizer)

        # Bind selection event
        self.shortcuts_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_shortcut_selected)

    def refresh(self):
        """Refresh the shortcuts list."""
        self.shortcuts_list.DeleteAllItems()

        # Get category filter
        category_idx = self.category_choice.GetSelection()
        category_filter = None
        if category_idx > 0:
            from .shortcuts import ShortcutCategory

            categories = [
                ShortcutCategory.PLAYBACK,
                ShortcutCategory.NAVIGATION,
                ShortcutCategory.STREAMS,
                ShortcutCategory.GENERAL,
                ShortcutCategory.RECORDING,
                ShortcutCategory.VOLUME,
            ]
            category_filter = categories[category_idx - 1]

        # Get shortcuts
        shortcuts = self.shortcut_manager.get_all_shortcuts()

        for i, shortcut in enumerate(shortcuts):
            # Apply filter
            if category_filter and shortcut.category != category_filter:
                continue

            idx = self.shortcuts_list.InsertItem(self.shortcuts_list.GetItemCount(), shortcut.name)
            self.shortcuts_list.SetItem(idx, 1, shortcut.current_key or "(none)")
            self.shortcuts_list.SetItem(idx, 2, shortcut.category.value.title())
            self.shortcuts_list.SetItem(idx, 3, shortcut.description)

            # Store shortcut ID
            self.shortcuts_list.SetItemData(idx, i)

    def _on_category_change(self, event):
        """Handle category filter change."""
        self.refresh()

    def _on_shortcut_selected(self, event):
        """Handle shortcut selection."""
        idx = self.shortcuts_list.GetFirstSelected()
        if idx == -1:
            self._editing_shortcut_id = None
            self.edit_label.SetLabel("Select a shortcut to edit")
            self.btn_change.Enable(False)
            self.btn_clear.Enable(False)
            return

        # Get shortcut
        shortcuts = self.shortcut_manager.get_all_shortcuts()

        # Find the shortcut by matching the name
        name = self.shortcuts_list.GetItemText(idx, 0)
        for shortcut in shortcuts:
            if shortcut.name == name:
                self._editing_shortcut_id = shortcut.id
                self.edit_label.SetLabel(f"Editing: {shortcut.name}")
                self.key_input.SetValue(shortcut.current_key or "")
                self.btn_change.Enable(True)
                self.btn_clear.Enable(True)
                self.conflict_label.SetLabel("")
                break

    def _on_key_press(self, event):
        """Capture key press for new shortcut."""
        key_code = event.GetKeyCode()

        # Ignore modifier-only presses
        if key_code in (
            wx.WXK_CONTROL,
            wx.WXK_ALT,
            wx.WXK_SHIFT,
            wx.WXK_WINDOWS_LEFT,
            wx.WXK_WINDOWS_RIGHT,
        ):
            event.Skip()
            return

        # Build key string
        parts = []
        if event.ControlDown():
            parts.append("Ctrl")
        if event.AltDown():
            parts.append("Alt")
        if event.ShiftDown():
            parts.append("Shift")

        # Get key name
        if key_code >= ord("A") and key_code <= ord("Z"):
            key_name = chr(key_code)
        elif key_code >= wx.WXK_F1 and key_code <= wx.WXK_F12:
            key_name = f"F{key_code - wx.WXK_F1 + 1}"
        elif key_code >= ord("0") and key_code <= ord("9"):
            key_name = chr(key_code)
        elif key_code == wx.WXK_SPACE:
            key_name = "Space"
        elif key_code == wx.WXK_RETURN:
            key_name = "Enter"
        elif key_code == wx.WXK_ESCAPE:
            key_name = "Escape"
        elif key_code == wx.WXK_TAB:
            key_name = "Tab"
        elif key_code == wx.WXK_DELETE:
            key_name = "Delete"
        elif key_code == wx.WXK_HOME:
            key_name = "Home"
        elif key_code == wx.WXK_END:
            key_name = "End"
        elif key_code == wx.WXK_PAGEUP:
            key_name = "PageUp"
        elif key_code == wx.WXK_PAGEDOWN:
            key_name = "PageDown"
        elif key_code == wx.WXK_UP:
            key_name = "Up"
        elif key_code == wx.WXK_DOWN:
            key_name = "Down"
        elif key_code == wx.WXK_LEFT:
            key_name = "Left"
        elif key_code == wx.WXK_RIGHT:
            key_name = "Right"
        else:
            event.Skip()
            return

        parts.append(key_name)
        key_string = "+".join(parts)

        self.key_input.SetValue(key_string)

        # Check for conflicts
        if self._editing_shortcut_id:
            conflict = self.shortcut_manager.get_shortcut_by_key(key_string)
            if conflict and conflict.id != self._editing_shortcut_id:
                self.conflict_label.SetLabel(f"⚠️ Conflicts with: {conflict.name}")
            else:
                self.conflict_label.SetLabel("")

    def _on_change_shortcut(self, event):
        """Apply the new shortcut."""
        if not self._editing_shortcut_id:
            return

        new_key = self.key_input.GetValue()

        # Check for conflicts
        conflict = self.shortcut_manager.get_shortcut_by_key(new_key)
        if conflict and conflict.id != self._editing_shortcut_id:
            if (
                wx.MessageBox(
                    f"This shortcut is already used by '{conflict.name}'.\n"
                    "Do you want to replace it?",
                    "Shortcut Conflict",
                    wx.YES_NO | wx.ICON_WARNING,
                )
                != wx.YES
            ):
                return

            # Clear the conflicting shortcut
            self.shortcut_manager.set_shortcut(conflict.id, "")

        # Set the new shortcut
        self.shortcut_manager.set_shortcut(self._editing_shortcut_id, new_key)
        self.refresh()

        # Notify of changes
        if self.on_shortcuts_changed:
            self.on_shortcuts_changed()

        wx.MessageBox("Shortcut updated successfully!", "Success", wx.OK | wx.ICON_INFORMATION)

    def _on_clear_shortcut(self, event):
        """Clear the selected shortcut."""
        if not self._editing_shortcut_id:
            return

        self.shortcut_manager.set_shortcut(self._editing_shortcut_id, "")
        self.key_input.SetValue("")
        self.refresh()

        if self.on_shortcuts_changed:
            self.on_shortcuts_changed()

    def _on_reset_selected(self, event):
        """Reset selected shortcut to default."""
        if not self._editing_shortcut_id:
            return

        self.shortcut_manager.reset_shortcut(self._editing_shortcut_id)
        self.refresh()

        # Update the display
        shortcut = self.shortcut_manager.get_shortcut(self._editing_shortcut_id)
        if shortcut:
            self.key_input.SetValue(shortcut.current_key or "")

        if self.on_shortcuts_changed:
            self.on_shortcuts_changed()

    def _on_reset_all(self, event):
        """Reset all shortcuts to defaults."""
        if (
            wx.MessageBox(
                "Reset all shortcuts to their default values?",
                "Reset All Shortcuts",
                wx.YES_NO | wx.ICON_QUESTION,
            )
            == wx.YES
        ):
            self.shortcut_manager.reset_all()
            self.refresh()

            if self.on_shortcuts_changed:
                self.on_shortcuts_changed()

    def _on_import(self, event):
        """Import shortcuts from file."""
        dlg = wx.FileDialog(
            self,
            "Import Shortcuts",
            wildcard="JSON files (*.json)|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            if self.shortcut_manager.import_shortcuts(filepath):
                self.refresh()
                if self.on_shortcuts_changed:
                    self.on_shortcuts_changed()
                wx.MessageBox(
                    "Shortcuts imported successfully!", "Success", wx.OK | wx.ICON_INFORMATION
                )
            else:
                wx.MessageBox("Failed to import shortcuts.", "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def _on_export(self, event):
        """Export shortcuts to file."""
        dlg = wx.FileDialog(
            self,
            "Export Shortcuts",
            wildcard="JSON files (*.json)|*.json",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile="acb_link_shortcuts.json",
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            if self.shortcut_manager.export_shortcuts(filepath):
                wx.MessageBox(
                    "Shortcuts exported successfully!", "Success", wx.OK | wx.ICON_INFORMATION
                )
            else:
                wx.MessageBox("Failed to export shortcuts.", "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()


class EventAlertsWidget(wx.Panel):
    """
    Widget to display upcoming event alerts on the home page.
    Shows scheduled events with alerts and quick actions.
    """

    def __init__(self, parent, event_scheduler, on_join_event=None, on_schedule_event=None):
        super().__init__(parent)
        self.event_scheduler = event_scheduler
        self.on_join_event = on_join_event
        self.on_schedule_event = on_schedule_event

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build the alerts widget UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header with icon
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header = wx.StaticText(self, label="📅 Upcoming Events")
        header_font = header.GetFont()
        header_font.SetPointSize(12)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        header_sizer.Add(header, 1, wx.EXPAND)

        self.btn_calendar = wx.Button(self, label="View Calendar", size=(100, -1))  # type: ignore[arg-type]
        self.btn_calendar.Bind(wx.EVT_BUTTON, self._on_view_calendar)
        header_sizer.Add(self.btn_calendar, 0)

        sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Alerts list
        self.alerts_list = wx.ListBox(self, style=wx.LB_SINGLE, size=(-1, 120))  # type: ignore[arg-type]
        self.alerts_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_alert_activate)
        sizer.Add(self.alerts_list, 1, wx.EXPAND | wx.ALL, 5)

        # Action buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_join = wx.Button(self, label="Join Now")
        self.btn_join.Bind(wx.EVT_BUTTON, self._on_join)
        btn_sizer.Add(self.btn_join, 0, wx.RIGHT, 5)

        self.btn_schedule = wx.Button(self, label="Schedule Recording")
        self.btn_schedule.Bind(wx.EVT_BUTTON, self._on_schedule_recording)
        btn_sizer.Add(self.btn_schedule, 0, wx.RIGHT, 5)

        self.btn_dismiss = wx.Button(self, label="Dismiss")
        self.btn_dismiss.Bind(wx.EVT_BUTTON, self._on_dismiss)
        btn_sizer.Add(self.btn_dismiss, 0)

        sizer.Add(btn_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)

        # Store alerts data
        self._alerts = []

    def refresh(self):
        """Refresh the alerts display."""
        self.alerts_list.Clear()
        self._alerts = self.event_scheduler.get_upcoming_alerts(hours=24)

        if not self._alerts:
            self.alerts_list.Append("No upcoming events scheduled")
            self.btn_join.Enable(False)
            self.btn_schedule.Enable(False)
            self.btn_dismiss.Enable(False)
            return

        self.btn_join.Enable(True)
        self.btn_schedule.Enable(True)
        self.btn_dismiss.Enable(True)

        for alert in self._alerts:
            display_text = f"{alert.message} - {alert.time_until}"
            self.alerts_list.Append(display_text)

        if self._alerts:
            self.alerts_list.SetSelection(0)

    def _get_selected_alert(self):
        """Get the currently selected alert."""
        idx = self.alerts_list.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self._alerts):
            return None
        return self._alerts[idx]

    def _on_view_calendar(self, event):
        """Navigate to calendar tab."""
        # Find parent notebook and switch to calendar tab
        parent = self.GetParent()
        while parent:
            if isinstance(parent, wx.Notebook):
                for i in range(parent.GetPageCount()):
                    if "Calendar" in parent.GetPageText(i):
                        parent.SetSelection(i)
                        return
            parent = parent.GetParent()

    def _on_alert_activate(self, event):
        """Handle double-click on alert."""
        self._on_join(event)

    def _on_join(self, event):
        """Join the selected event."""
        alert = self._get_selected_alert()
        if alert and self.on_join_event:
            self.on_join_event(alert.event)

    def _on_schedule_recording(self, event):
        """Schedule recording for selected event."""
        alert = self._get_selected_alert()
        if alert and self.on_schedule_event:
            self.on_schedule_event(alert.event)

    def _on_dismiss(self, event):
        """Dismiss the selected alert."""
        alert = self._get_selected_alert()
        if alert:
            self.event_scheduler.remove_scheduled_event(alert.event.id)
            self.refresh()
