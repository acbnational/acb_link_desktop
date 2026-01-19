"""
ACB Link - Customizable Home Page Widget System
A magical, personalized dashboard with navigable sections.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, List, Optional

import wx

from .accessibility import announce, make_accessible, make_list_accessible
from .utils import get_app_data_dir


class WidgetType(Enum):
    """Types of home page widgets."""

    WELCOME = "welcome"
    FAVORITE_STREAMS = "favorite_streams"
    FAVORITE_PODCASTS = "favorite_podcasts"
    RECENT_EPISODES = "recent_episodes"
    CALENDAR_EVENTS = "calendar_events"
    FAVORITE_AFFILIATES = "favorite_affiliates"
    QUICK_ACTIONS = "quick_actions"
    NOW_PLAYING = "now_playing"
    DOWNLOAD_PROGRESS = "download_progress"
    LISTENING_STATS = "listening_stats"


@dataclass
class WidgetConfig:
    """Configuration for a home page widget."""

    widget_type: WidgetType
    enabled: bool = True
    order: int = 0
    collapsed: bool = False
    max_items: int = 5
    custom_title: str = ""

    @property
    def display_title(self) -> str:
        """Get the display title for this widget."""
        if self.custom_title:
            return self.custom_title
        return WIDGET_TITLES.get(self.widget_type, "Widget")


# Default widget titles
WIDGET_TITLES = {
    WidgetType.WELCOME: "Welcome",
    WidgetType.FAVORITE_STREAMS: "Favorite Streams",
    WidgetType.FAVORITE_PODCASTS: "Favorite Podcasts",
    WidgetType.RECENT_EPISODES: "Recent Episodes",
    WidgetType.CALENDAR_EVENTS: "Upcoming Events",
    WidgetType.FAVORITE_AFFILIATES: "My Affiliates",
    WidgetType.QUICK_ACTIONS: "Quick Actions",
    WidgetType.NOW_PLAYING: "Now Playing",
    WidgetType.DOWNLOAD_PROGRESS: "Downloads",
    WidgetType.LISTENING_STATS: "Listening Statistics",
}

# Widget descriptions for accessibility
WIDGET_DESCRIPTIONS = {
    WidgetType.WELCOME: "Welcome message and getting started tips",
    WidgetType.FAVORITE_STREAMS: "Quick access to your favorite audio streams",
    WidgetType.FAVORITE_PODCASTS: "Your favorite podcasts with latest episodes",
    WidgetType.RECENT_EPISODES: "Recently played podcast episodes",
    WidgetType.CALENDAR_EVENTS: "Upcoming ACB calendar events",
    WidgetType.FAVORITE_AFFILIATES: "Your selected state and SIG affiliates",
    WidgetType.QUICK_ACTIONS: "Common actions like play, record, search",
    WidgetType.NOW_PLAYING: "Currently playing content information",
    WidgetType.DOWNLOAD_PROGRESS: "Active and recent downloads",
    WidgetType.LISTENING_STATS: "Your listening history statistics",
}


class HomePageSettings:
    """Manages home page widget configuration and persistence."""

    def __init__(self):
        self._config_file = get_app_data_dir() / "home_widgets.json"
        self.widgets: List[WidgetConfig] = []
        self._load()

    def _load(self):
        """Load widget configuration from disk."""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.widgets = []
                for w in data.get("widgets", []):
                    w["widget_type"] = WidgetType(w["widget_type"])
                    self.widgets.append(WidgetConfig(**w))
                return
            except Exception:
                pass

        # Default widget configuration
        self._set_defaults()

    def _set_defaults(self):
        """Set default widget configuration."""
        self.widgets = [
            WidgetConfig(WidgetType.WELCOME, order=0),
            WidgetConfig(WidgetType.NOW_PLAYING, order=1),
            WidgetConfig(WidgetType.FAVORITE_STREAMS, order=2),
            WidgetConfig(WidgetType.FAVORITE_PODCASTS, order=3),
            WidgetConfig(WidgetType.RECENT_EPISODES, order=4),
            WidgetConfig(WidgetType.CALENDAR_EVENTS, order=5),
            WidgetConfig(WidgetType.FAVORITE_AFFILIATES, order=6, enabled=False),
            WidgetConfig(WidgetType.QUICK_ACTIONS, order=7),
            WidgetConfig(WidgetType.DOWNLOAD_PROGRESS, order=8, enabled=False),
            WidgetConfig(WidgetType.LISTENING_STATS, order=9, enabled=False),
        ]

    def save(self):
        """Save widget configuration to disk."""
        try:
            data = {
                "widgets": [{**asdict(w), "widget_type": w.widget_type.value} for w in self.widgets]
            }
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_enabled_widgets(self) -> List[WidgetConfig]:
        """Get enabled widgets sorted by order."""
        return sorted([w for w in self.widgets if w.enabled], key=lambda w: w.order)

    def get_widget(self, widget_type: WidgetType) -> Optional[WidgetConfig]:
        """Get configuration for a specific widget type."""
        for w in self.widgets:
            if w.widget_type == widget_type:
                return w
        return None

    def set_enabled(self, widget_type: WidgetType, enabled: bool):
        """Enable or disable a widget."""
        widget = self.get_widget(widget_type)
        if widget:
            widget.enabled = enabled
            self.save()

    def move_widget(self, widget_type: WidgetType, direction: int):
        """Move a widget up (-1) or down (+1) in order."""
        enabled = self.get_enabled_widgets()
        for i, w in enumerate(enabled):
            if w.widget_type == widget_type:
                new_idx = max(0, min(len(enabled) - 1, i + direction))
                if new_idx != i:
                    # Swap orders
                    enabled[i].order, enabled[new_idx].order = (
                        enabled[new_idx].order,
                        enabled[i].order,
                    )
                    self.save()
                break

    def reset_to_defaults(self):
        """Reset to default widget configuration."""
        self._set_defaults()
        self.save()


class BaseWidget(wx.Panel):
    """Base class for home page widgets with accessible heading structure."""

    HEADING_LEVEL = 2  # Default heading level (H2)

    def __init__(
        self,
        parent: wx.Window,
        config: WidgetConfig,
        on_action: Optional[Callable[[str, Any], None]] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.on_action = on_action
        self._collapsed = config.collapsed

        self._build_ui()

    def _build_ui(self):
        """Build the widget UI with accessible heading."""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header with heading role
        self.header_panel = wx.Panel(self)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Heading text (using StaticText with heading styling)
        self.heading = wx.StaticText(self.header_panel, label=self.config.display_title)
        heading_font = self.heading.GetFont()
        heading_font.SetPointSize(14 if self.HEADING_LEVEL == 2 else 12)
        heading_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.heading.SetFont(heading_font)
        self.heading.SetForegroundColour(wx.Colour(0, 120, 212))

        # Set accessible name with heading level
        self.heading.SetName(f"Heading level {self.HEADING_LEVEL}: {self.config.display_title}")

        header_sizer.Add(self.heading, 1, wx.ALIGN_CENTER_VERTICAL)

        # Collapse/expand button
        self.collapse_btn = wx.Button(
            self.header_panel, label="−" if not self._collapsed else "+", size=(28, 28)
        )
        self.collapse_btn.SetToolTip(
            "Collapse section" if not self._collapsed else "Expand section"
        )
        self.collapse_btn.Bind(wx.EVT_BUTTON, self._on_toggle_collapse)
        make_accessible(
            self.collapse_btn,
            f"{'Collapse' if not self._collapsed else 'Expand'} {self.config.display_title}",
            f"{'Collapse' if not self._collapsed else 'Expand'} this section",
        )
        header_sizer.Add(self.collapse_btn, 0, wx.LEFT, 5)

        self.header_panel.SetSizer(header_sizer)
        self.main_sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # Content panel (can be collapsed)
        self.content_panel = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self._build_content()
        self.content_panel.SetSizer(self.content_sizer)
        self.main_sizer.Add(self.content_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Apply initial collapsed state
        self.content_panel.Show(not self._collapsed)

        # Separator
        sep = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        self.main_sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.SetSizer(self.main_sizer)

    def _build_content(self):
        """Override in subclasses to build widget content."""
        pass

    def _on_toggle_collapse(self, event):
        """Toggle collapsed state."""
        self._collapsed = not self._collapsed
        self.config.collapsed = self._collapsed

        self.content_panel.Show(not self._collapsed)
        self.collapse_btn.SetLabel("−" if not self._collapsed else "+")
        self.collapse_btn.SetToolTip(
            "Collapse section" if not self._collapsed else "Expand section"
        )

        # Update accessible name
        make_accessible(
            self.collapse_btn,
            f"{'Collapse' if not self._collapsed else 'Expand'} {self.config.display_title}",
            f"{'Collapse' if not self._collapsed else 'Expand'} this section",
        )

        # Announce state change
        state = "collapsed" if self._collapsed else "expanded"
        announce(f"{self.config.display_title} {state}")

        # Trigger layout update
        self.GetParent().Layout()
        if hasattr(self.GetParent(), "FitInside"):
            self.GetParent().FitInside()

    def refresh(self):
        """Override to refresh widget data."""
        pass

    def trigger_action(self, action: str, data: Any = None):
        """Trigger an action callback."""
        if self.on_action:
            self.on_action(action, data)


class WelcomeWidget(BaseWidget):
    """Welcome message widget with tips and getting started."""

    def _build_content(self):
        welcome_text = wx.StaticText(
            self.content_panel,
            label="Welcome to ACB Link! Your gateway to ACB media content.\n\n"
            "• Press Ctrl+1-5 to switch tabs\n"
            "• Press F5 for quick status\n"
            "• Use the View menu to customize this page",
        )
        welcome_text.Wrap(500)
        self.content_sizer.Add(welcome_text, 0, wx.ALL, 5)


class FavoriteStreamsWidget(BaseWidget):
    """Widget showing favorite streams with quick play buttons."""

    def __init__(self, parent, config, on_action, favorites_manager):
        self.favorites_manager = favorites_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.streams_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self._populate_streams()
        self.content_sizer.Add(self.streams_sizer, 0, wx.EXPAND)

        # Empty state
        self.empty_label = wx.StaticText(
            self.content_panel, label="No favorite streams yet. Add streams from the Streams tab."
        )
        self.empty_label.SetForegroundColour(wx.Colour(102, 102, 102))
        self.content_sizer.Add(self.empty_label, 0, wx.ALL, 5)

    def _populate_streams(self):
        """Populate stream buttons."""
        self.streams_sizer.Clear(True)

        favorites = self.favorites_manager.get_favorite_streams()
        has_favorites = len(favorites) > 0

        if has_favorites:
            for fav in favorites[: self.config.max_items]:
                btn = wx.Button(self.content_panel, label=f"▶ {fav.name}", size=(-1, 32))
                btn.SetBackgroundColour(wx.Colour(0, 120, 212))
                btn.SetForegroundColour(wx.WHITE)
                btn.Bind(wx.EVT_BUTTON, lambda e, f=fav: self.trigger_action("play_stream", f.name))
                make_accessible(btn, f"Play {fav.name}", f"Start playing {fav.name} stream")
                self.streams_sizer.Add(btn, 0, wx.ALL, 3)

        if hasattr(self, "empty_label"):
            self.empty_label.Show(not has_favorites)

    def refresh(self):
        """Refresh the streams list."""
        self._populate_streams()
        self.Layout()


class FavoritePodcastsWidget(BaseWidget):
    """Widget showing favorite podcasts with latest episodes."""

    def __init__(self, parent, config, on_action, favorites_manager, podcast_manager):
        self.favorites_manager = favorites_manager
        self.podcast_manager = podcast_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.podcasts_list = wx.ListCtrl(
            self.content_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
            size=(-1, 120),
        )
        self.podcasts_list.InsertColumn(0, "Podcast", width=200)
        self.podcasts_list.InsertColumn(1, "Latest Episode", width=250)
        make_list_accessible(
            self.podcasts_list,
            "Favorite podcasts",
            "Your favorite podcasts. Press Enter to play latest episode.",
        )

        self.podcasts_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_podcast_activated)
        self.content_sizer.Add(self.podcasts_list, 0, wx.EXPAND | wx.ALL, 5)

        self._populate_podcasts()

    def _populate_podcasts(self):
        """Populate the podcasts list."""
        self.podcasts_list.DeleteAllItems()

        favorites = self.favorites_manager.get_favorite_podcasts()
        for i, fav in enumerate(favorites[: self.config.max_items]):
            idx = self.podcasts_list.InsertItem(i, fav.name)

            # Try to get latest episode
            podcast = self.podcast_manager.get_podcast_by_url(fav.url)
            if podcast and podcast.episodes:
                latest = podcast.episodes[0].title
                self.podcasts_list.SetItem(idx, 1, latest[:40])
            else:
                self.podcasts_list.SetItem(idx, 1, "Load to see episodes")

            self.podcasts_list.SetItemData(idx, i)

    def _on_podcast_activated(self, event):
        """Handle podcast double-click."""
        idx = event.GetIndex()
        favorites = self.favorites_manager.get_favorite_podcasts()
        if idx < len(favorites):
            self.trigger_action("open_podcast", favorites[idx])

    def refresh(self):
        self._populate_podcasts()


class CalendarEventsWidget(BaseWidget):
    """Widget showing upcoming ACB calendar events."""

    def __init__(self, parent, config, on_action, calendar_manager=None):
        self.calendar_manager = calendar_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.events_list = wx.ListCtrl(
            self.content_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
            size=(-1, 120),
        )
        self.events_list.InsertColumn(0, "Date", width=100)
        self.events_list.InsertColumn(1, "Time", width=80)
        self.events_list.InsertColumn(2, "Event", width=300)
        make_list_accessible(
            self.events_list,
            "Upcoming events",
            "ACB calendar events. Press Enter for event details.",
        )

        self.events_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_event_activated)
        self.content_sizer.Add(self.events_list, 0, wx.EXPAND | wx.ALL, 5)

        self._populate_events()

    def _populate_events(self):
        """Populate events list."""
        self.events_list.DeleteAllItems()

        # Sample events (would come from calendar_manager)
        events = [
            {"date": "Jan 20", "time": "2:00 PM", "title": "ACB Board Meeting"},
            {"date": "Jan 22", "time": "7:00 PM", "title": "Tech Talk Tuesday"},
            {"date": "Jan 25", "time": "3:00 PM", "title": "Advocacy Update Call"},
        ]

        for i, event in enumerate(events[: self.config.max_items]):
            idx = self.events_list.InsertItem(i, event["date"])
            self.events_list.SetItem(idx, 1, event["time"])
            self.events_list.SetItem(idx, 2, event["title"])

    def _on_event_activated(self, event):
        """Handle event double-click."""
        self.trigger_action("view_calendar")

    def refresh(self):
        self._populate_events()


class FavoriteAffiliatesWidget(BaseWidget):
    """Widget showing user's selected affiliates."""

    def __init__(self, parent, config, on_action, favorites_manager):
        self.favorites_manager = favorites_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.affiliates_list = wx.ListCtrl(
            self.content_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
            size=(-1, 100),
        )
        self.affiliates_list.InsertColumn(0, "Organization", width=250)
        self.affiliates_list.InsertColumn(1, "Contact", width=150)
        make_list_accessible(
            self.affiliates_list,
            "My affiliates",
            "Your selected affiliate organizations. Press Enter for details.",
        )

        self.affiliates_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_affiliate_activated)
        self.content_sizer.Add(self.affiliates_list, 0, wx.EXPAND | wx.ALL, 5)

        # Empty state message
        self.empty_label = wx.StaticText(
            self.content_panel, label="Enable this in Affiliates tab to see your state or SIG here."
        )
        self.empty_label.SetForegroundColour(wx.Colour(102, 102, 102))
        self.content_sizer.Add(self.empty_label, 0, wx.ALL, 5)

        self._populate_affiliates()

    def _populate_affiliates(self):
        """Populate affiliates list from favorites."""
        self.affiliates_list.DeleteAllItems()
        # Would pull from favorites - for now show empty state
        self.empty_label.Show(True)

    def _on_affiliate_activated(self, event):
        """Handle affiliate activation."""
        self.trigger_action("view_affiliates")

    def refresh(self):
        self._populate_affiliates()


class QuickActionsWidget(BaseWidget):
    """Widget with common action buttons."""

    def _build_content(self):
        btn_sizer = wx.WrapSizer(wx.HORIZONTAL)

        actions = [
            ("🔍 Search", "search", "Search for content"),
            ("⏺ Record", "record", "Start recording current stream"),
            ("📋 Playlists", "playlists", "Open playlists"),
            ("⚙ Settings", "settings", "Open settings"),
        ]

        for label, action, tooltip in actions:
            btn = wx.Button(self.content_panel, label=label, size=(-1, 32))
            btn.SetToolTip(tooltip)
            btn.Bind(wx.EVT_BUTTON, lambda e, a=action: self.trigger_action(a))
            make_accessible(btn, label.split(" ")[1], tooltip)
            btn_sizer.Add(btn, 0, wx.ALL, 3)

        self.content_sizer.Add(btn_sizer, 0, wx.EXPAND)


class NowPlayingWidget(BaseWidget):
    """Widget showing current playback information."""

    def _build_content(self):
        self.now_playing_label = wx.StaticText(self.content_panel, label="Nothing playing")
        self.now_playing_label.SetFont(self.now_playing_label.GetFont().Bold())
        self.content_sizer.Add(self.now_playing_label, 0, wx.ALL, 5)

        self.details_label = wx.StaticText(
            self.content_panel, label="Select a stream or podcast to start listening"
        )
        self.details_label.SetForegroundColour(wx.Colour(102, 102, 102))
        self.content_sizer.Add(self.details_label, 0, wx.LEFT | wx.BOTTOM, 5)

        # Playback controls
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.play_btn = wx.Button(self.content_panel, label="▶ Play", size=(80, 28))
        self.play_btn.Bind(wx.EVT_BUTTON, lambda e: self.trigger_action("play_pause"))
        make_accessible(self.play_btn, "Play or Pause", "Toggle playback")
        ctrl_sizer.Add(self.play_btn, 0, wx.RIGHT, 5)

        self.stop_btn = wx.Button(self.content_panel, label="⏹ Stop", size=(80, 28))
        self.stop_btn.Bind(wx.EVT_BUTTON, lambda e: self.trigger_action("stop"))
        make_accessible(self.stop_btn, "Stop", "Stop playback")
        ctrl_sizer.Add(self.stop_btn, 0)

        self.content_sizer.Add(ctrl_sizer, 0, wx.ALL, 5)

    def update_now_playing(self, title: str, details: str = ""):
        """Update the now playing display."""
        if title:
            self.now_playing_label.SetLabel(f"▶ {title}")
            self.play_btn.SetLabel("⏸ Pause")
        else:
            self.now_playing_label.SetLabel("Nothing playing")
            self.play_btn.SetLabel("▶ Play")

        self.details_label.SetLabel(details or "Select a stream or podcast to start listening")
        self.Layout()


class RecentEpisodesWidget(BaseWidget):
    """Widget showing recently played podcast episodes."""

    def __init__(self, parent, config, on_action, podcast_manager):
        self.podcast_manager = podcast_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.episodes_list = wx.ListCtrl(
            self.content_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
            size=(-1, 100),
        )
        self.episodes_list.InsertColumn(0, "Episode", width=300)
        self.episodes_list.InsertColumn(1, "Podcast", width=150)
        make_list_accessible(
            self.episodes_list,
            "Recent episodes",
            "Recently played podcast episodes. Press Enter to resume.",
        )

        self.episodes_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_episode_activated)
        self.content_sizer.Add(self.episodes_list, 0, wx.EXPAND | wx.ALL, 5)

        self._populate_episodes()

    def _populate_episodes(self):
        """Populate recent episodes."""
        self.episodes_list.DeleteAllItems()
        # Would pull from podcast manager's played history

    def _on_episode_activated(self, event):
        """Handle episode activation - resume playback."""
        pass

    def refresh(self):
        self._populate_episodes()


class DownloadProgressWidget(BaseWidget):
    """Widget showing active downloads."""

    def __init__(self, parent, config, on_action, download_manager):
        self.download_manager = download_manager
        super().__init__(parent, config, on_action)

    def _build_content(self):
        self.downloads_list = wx.ListCtrl(
            self.content_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE,
            size=(-1, 80),
        )
        self.downloads_list.InsertColumn(0, "Episode", width=300)
        self.downloads_list.InsertColumn(1, "Progress", width=100)
        make_list_accessible(
            self.downloads_list, "Active downloads", "Currently downloading episodes"
        )
        self.content_sizer.Add(self.downloads_list, 0, wx.EXPAND | wx.ALL, 5)

        self.empty_label = wx.StaticText(self.content_panel, label="No active downloads")
        self.empty_label.SetForegroundColour(wx.Colour(102, 102, 102))
        self.content_sizer.Add(self.empty_label, 0, wx.ALL, 5)

    def refresh(self):
        """Refresh download status."""
        pass


class ListeningStatsWidget(BaseWidget):
    """Widget showing listening statistics."""

    def _build_content(self):
        stats_grid = wx.FlexGridSizer(2, 3, 10, 20)

        stats = [
            ("This Week", "4h 32m"),
            ("This Month", "18h 15m"),
            ("Total", "156h"),
        ]

        for label, value in stats:
            lbl = wx.StaticText(self.content_panel, label=label)
            lbl.SetForegroundColour(wx.Colour(102, 102, 102))
            stats_grid.Add(lbl, 0, wx.ALIGN_CENTER)

        for label, value in stats:
            val = wx.StaticText(self.content_panel, label=value)
            val_font = val.GetFont()
            val_font.SetPointSize(16)
            val_font.SetWeight(wx.FONTWEIGHT_BOLD)
            val.SetFont(val_font)
            val.SetForegroundColour(wx.Colour(0, 120, 212))
            stats_grid.Add(val, 0, wx.ALIGN_CENTER)

        self.content_sizer.Add(stats_grid, 0, wx.ALL | wx.ALIGN_CENTER, 10)


# Widget factory
WIDGET_CLASSES = {
    WidgetType.WELCOME: WelcomeWidget,
    WidgetType.FAVORITE_STREAMS: FavoriteStreamsWidget,
    WidgetType.FAVORITE_PODCASTS: FavoritePodcastsWidget,
    WidgetType.RECENT_EPISODES: RecentEpisodesWidget,
    WidgetType.CALENDAR_EVENTS: CalendarEventsWidget,
    WidgetType.FAVORITE_AFFILIATES: FavoriteAffiliatesWidget,
    WidgetType.QUICK_ACTIONS: QuickActionsWidget,
    WidgetType.NOW_PLAYING: NowPlayingWidget,
    WidgetType.DOWNLOAD_PROGRESS: DownloadProgressWidget,
    WidgetType.LISTENING_STATS: ListeningStatsWidget,
}


class HomePageCustomizeDialog(wx.Dialog):
    """Dialog for customizing home page widgets."""

    def __init__(self, parent: wx.Window, settings: HomePageSettings):
        super().__init__(
            parent,
            title="Customize Home Page",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(500, 500),
        )
        self.settings = settings
        self._build_ui()
        self.Centre()

    def _build_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Select which widgets to show on your home page and arrange their order. "
            "Use the checkboxes to enable/disable widgets, and the Move Up/Down buttons "
            "to change their position.",
        )
        instructions.Wrap(450)
        main_sizer.Add(instructions, 0, wx.ALL, 10)

        # Widgets list
        list_label = wx.StaticText(panel, label="&Widgets:")
        main_sizer.Add(list_label, 0, wx.LEFT | wx.TOP, 10)

        self.widgets_list = wx.CheckListBox(panel, size=(-1, 250), style=wx.LB_SINGLE)
        self.widgets_list.SetName("Widgets list")

        self._populate_list()

        main_sizer.Add(self.widgets_list, 1, wx.EXPAND | wx.ALL, 10)

        # Description
        self.desc_label = wx.StaticText(panel, label="")
        self.desc_label.SetForegroundColour(wx.Colour(102, 102, 102))
        main_sizer.Add(self.desc_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Move buttons
        move_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.move_up_btn = wx.Button(panel, label="Move &Up")
        self.move_up_btn.Bind(wx.EVT_BUTTON, self._on_move_up)
        move_sizer.Add(self.move_up_btn, 0, wx.RIGHT, 5)

        self.move_down_btn = wx.Button(panel, label="Move &Down")
        self.move_down_btn.Bind(wx.EVT_BUTTON, self._on_move_down)
        move_sizer.Add(self.move_down_btn, 0, wx.RIGHT, 20)

        self.reset_btn = wx.Button(panel, label="&Reset to Defaults")
        self.reset_btn.Bind(wx.EVT_BUTTON, self._on_reset)
        move_sizer.Add(self.reset_btn, 0)

        main_sizer.Add(move_sizer, 0, wx.ALL, 10)

        # OK/Cancel buttons
        btn_sizer = wx.StdDialogButtonSizer()

        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.SetDefault()
        btn_sizer.AddButton(ok_btn)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.AddButton(cancel_btn)

        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

        # Bindings
        self.widgets_list.Bind(wx.EVT_LISTBOX, self._on_selection_changed)
        self.widgets_list.Bind(wx.EVT_CHECKLISTBOX, self._on_check_changed)
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)

        # Set initial selection
        if self.widgets_list.GetCount() > 0:
            self.widgets_list.SetSelection(0)
            self._on_selection_changed(None)

    def _populate_list(self):
        """Populate the widgets list."""
        self.widgets_list.Clear()

        # Sort by order
        sorted_widgets = sorted(self.settings.widgets, key=lambda w: w.order)

        for w in sorted_widgets:
            idx = self.widgets_list.Append(w.display_title)
            self.widgets_list.Check(idx, w.enabled)

    def _on_selection_changed(self, event):
        """Update description when selection changes."""
        idx = self.widgets_list.GetSelection()
        if idx == wx.NOT_FOUND:
            return

        sorted_widgets = sorted(self.settings.widgets, key=lambda w: w.order)
        widget = sorted_widgets[idx]

        desc = WIDGET_DESCRIPTIONS.get(widget.widget_type, "")
        self.desc_label.SetLabel(desc)

    def _on_check_changed(self, event):
        """Handle checkbox state change."""
        idx = event.GetInt()
        sorted_widgets = sorted(self.settings.widgets, key=lambda w: w.order)
        widget = sorted_widgets[idx]
        widget.enabled = self.widgets_list.IsChecked(idx)

    def _on_move_up(self, event):
        """Move selected widget up."""
        idx = self.widgets_list.GetSelection()
        if idx == wx.NOT_FOUND or idx == 0:
            return

        sorted_widgets = sorted(self.settings.widgets, key=lambda w: w.order)
        widget = sorted_widgets[idx]

        # Swap orders
        sorted_widgets[idx].order, sorted_widgets[idx - 1].order = (
            sorted_widgets[idx - 1].order,
            sorted_widgets[idx].order,
        )

        self._populate_list()
        self.widgets_list.SetSelection(idx - 1)
        announce(f"Moved {widget.display_title} up")

    def _on_move_down(self, event):
        """Move selected widget down."""
        idx = self.widgets_list.GetSelection()
        if idx == wx.NOT_FOUND or idx >= self.widgets_list.GetCount() - 1:
            return

        sorted_widgets = sorted(self.settings.widgets, key=lambda w: w.order)
        widget = sorted_widgets[idx]

        # Swap orders
        sorted_widgets[idx].order, sorted_widgets[idx + 1].order = (
            sorted_widgets[idx + 1].order,
            sorted_widgets[idx].order,
        )

        self._populate_list()
        self.widgets_list.SetSelection(idx + 1)
        announce(f"Moved {widget.display_title} down")

    def _on_reset(self, event):
        """Reset to default configuration."""
        result = wx.MessageBox(
            "Reset home page to default layout?",
            "Confirm Reset",
            wx.YES_NO | wx.ICON_QUESTION,
            self,
        )
        if result == wx.YES:
            self.settings.reset_to_defaults()
            self._populate_list()
            announce("Reset to defaults")

    def _on_ok(self, event):
        """Save settings and close."""
        self.settings.save()
        self.EndModal(wx.ID_OK)
