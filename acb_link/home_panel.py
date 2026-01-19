"""
ACB Link - Customizable Home Panel
A magical, personalized dashboard with navigable widget sections.
"""

from typing import Any, Callable, Dict, Optional

import wx

from .accessibility import announce, make_accessible
from .home_widgets import (
    BaseWidget,
    CalendarEventsWidget,
    DownloadProgressWidget,
    FavoriteAffiliatesWidget,
    FavoritePodcastsWidget,
    FavoriteStreamsWidget,
    HomePageCustomizeDialog,
    HomePageSettings,
    ListeningStatsWidget,
    NowPlayingWidget,
    QuickActionsWidget,
    RecentEpisodesWidget,
    WelcomeWidget,
    WidgetConfig,
    WidgetType,
)


class CustomizableHomePanel(wx.Panel):
    """
    Customizable home panel with draggable, collapsible widgets.

    Features:
    - Multiple widget types (favorites, calendar, recent, etc.)
    - User-configurable widget order
    - Enable/disable individual widgets
    - Proper heading structure for accessibility
    - Keyboard navigation between sections
    """

    def __init__(
        self,
        parent: wx.Window,
        settings: HomePageSettings,
        favorites_manager,
        podcast_manager,
        calendar_manager=None,
        on_action: Optional[Callable[[str, Any], None]] = None,
    ):
        super().__init__(parent)

        self.settings = settings
        self.favorites_manager = favorites_manager
        self.podcast_manager = podcast_manager
        self.calendar_manager = calendar_manager
        self.on_action = on_action

        self.widgets: Dict[WidgetType, BaseWidget] = {}

        self._build_ui()

    def _build_ui(self):
        """Build the customizable home panel."""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header section
        header = self._create_header()
        self.main_sizer.Add(header, 0, wx.EXPAND | wx.ALL, 15)

        # Separator
        sep = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        self.main_sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # Scrollable content area
        self.scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll.SetScrollRate(0, 20)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)

        self._build_widgets()

        self.scroll.SetSizer(self.scroll_sizer)
        self.main_sizer.Add(self.scroll, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(self.main_sizer)

        # Keyboard navigation
        self.scroll.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _create_header(self) -> wx.Panel:
        """Create the page header."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Main heading (H1)
        self.main_heading = wx.StaticText(panel, label="Welcome to ACB Link")
        heading_font = self.main_heading.GetFont()
        heading_font.SetPointSize(24)
        heading_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.main_heading.SetFont(heading_font)
        self.main_heading.SetForegroundColour(wx.Colour(0, 120, 212))
        self.main_heading.SetName("Heading level 1: Welcome to ACB Link")
        sizer.Add(self.main_heading, 0, wx.BOTTOM, 5)

        # Subtitle row
        subtitle_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.subtitle = wx.StaticText(panel, label="Your personalized gateway to ACB media content")
        sub_font = self.subtitle.GetFont()
        sub_font.SetPointSize(12)
        self.subtitle.SetFont(sub_font)
        self.subtitle.SetForegroundColour(wx.Colour(102, 102, 102))
        subtitle_sizer.Add(self.subtitle, 1, wx.ALIGN_CENTER_VERTICAL)

        # Customize button
        self.customize_btn = wx.Button(panel, label="⚙ Customize", size=(100, 28))
        self.customize_btn.SetToolTip("Customize which widgets appear on this page")
        self.customize_btn.Bind(wx.EVT_BUTTON, self._on_customize)
        make_accessible(
            self.customize_btn,
            "Customize Home Page",
            "Open dialog to customize which widgets appear and their order",
        )
        subtitle_sizer.Add(self.customize_btn, 0, wx.LEFT, 10)

        sizer.Add(subtitle_sizer, 0, wx.EXPAND)

        panel.SetSizer(sizer)
        return panel

    def _build_widgets(self):
        """Build all enabled widgets in order."""
        self.scroll_sizer.Clear(True)
        self.widgets.clear()

        enabled_widgets = self.settings.get_enabled_widgets()

        for config in enabled_widgets:
            widget = self._create_widget(config)
            if widget:
                self.widgets[config.widget_type] = widget
                self.scroll_sizer.Add(widget, 0, wx.EXPAND | wx.ALL, 5)

        self.scroll.Layout()
        self.scroll.FitInside()

    def _create_widget(self, config: WidgetConfig) -> Optional[BaseWidget]:
        """Create a widget instance based on type."""
        widget_type = config.widget_type

        # Widgets that need special initialization
        if widget_type == WidgetType.FAVORITE_STREAMS:
            return FavoriteStreamsWidget(
                self.scroll, config, self._handle_action, self.favorites_manager
            )
        elif widget_type == WidgetType.FAVORITE_PODCASTS:
            return FavoritePodcastsWidget(
                self.scroll,
                config,
                self._handle_action,
                self.favorites_manager,
                self.podcast_manager,
            )
        elif widget_type == WidgetType.CALENDAR_EVENTS:
            return CalendarEventsWidget(
                self.scroll, config, self._handle_action, self.calendar_manager
            )
        elif widget_type == WidgetType.FAVORITE_AFFILIATES:
            return FavoriteAffiliatesWidget(
                self.scroll, config, self._handle_action, self.favorites_manager
            )
        elif widget_type == WidgetType.RECENT_EPISODES:
            return RecentEpisodesWidget(
                self.scroll, config, self._handle_action, self.podcast_manager
            )
        elif widget_type == WidgetType.DOWNLOAD_PROGRESS:
            return DownloadProgressWidget(
                self.scroll, config, self._handle_action, self.podcast_manager.download_manager
            )
        elif widget_type == WidgetType.WELCOME:
            return WelcomeWidget(self.scroll, config, self._handle_action)
        elif widget_type == WidgetType.QUICK_ACTIONS:
            return QuickActionsWidget(self.scroll, config, self._handle_action)
        elif widget_type == WidgetType.NOW_PLAYING:
            return NowPlayingWidget(self.scroll, config, self._handle_action)
        elif widget_type == WidgetType.LISTENING_STATS:
            return ListeningStatsWidget(self.scroll, config, self._handle_action)

        return None

    def _handle_action(self, action: str, data: Any = None):
        """Handle widget action callbacks."""
        if self.on_action:
            self.on_action(action, data)

    def _on_customize(self, event):
        """Open customization dialog."""
        dialog = HomePageCustomizeDialog(self, self.settings)
        if dialog.ShowModal() == wx.ID_OK:
            self._build_widgets()
            announce("Home page updated")
        dialog.Destroy()

    def _on_key_down(self, event):
        """Handle keyboard navigation between widgets."""
        key = event.GetKeyCode()

        if key == ord("H") and event.ControlDown():
            # Ctrl+H - Jump to next heading
            self._focus_next_widget()
        elif key == ord("H") and event.ControlDown() and event.ShiftDown():
            # Ctrl+Shift+H - Jump to previous heading
            self._focus_previous_widget()
        else:
            event.Skip()

    def _focus_next_widget(self):
        """Focus the next widget's heading."""
        # Implementation would cycle through widget headings
        pass

    def _focus_previous_widget(self):
        """Focus the previous widget's heading."""
        pass

    def refresh(self):
        """Refresh all widgets."""
        for widget in self.widgets.values():
            widget.refresh()

    def update_now_playing(self, title: str, details: str = ""):
        """Update the now playing widget."""
        if WidgetType.NOW_PLAYING in self.widgets:
            now_playing = self.widgets[WidgetType.NOW_PLAYING]
            if isinstance(now_playing, NowPlayingWidget):
                now_playing.update_now_playing(title, details)

    def update_greeting(self, name: str = ""):
        """Update the welcome greeting with user's name."""
        if name:
            self.main_heading.SetLabel(f"Welcome back, {name}!")
        else:
            self.main_heading.SetLabel("Welcome to ACB Link")


def create_home_panel_action_handler(main_frame) -> Callable[[str, Any], None]:
    """Create an action handler that routes widget actions to main frame."""

    def handle_action(action: str, data: Any = None):
        """Route widget action to appropriate main frame method."""
        if action == "play_stream":
            main_frame._play_stream(data)
        elif action == "open_podcast":
            # Switch to podcasts tab and select podcast
            main_frame.notebook.SetSelection(2)  # Podcasts tab
        elif action == "play_pause":
            main_frame._on_play_pause(None)
        elif action == "stop":
            main_frame._on_stop(None)
        elif action == "search":
            main_frame._on_search(None)
        elif action == "record":
            main_frame._on_record(None)
        elif action == "playlists":
            # Would navigate to playlists
            pass
        elif action == "settings":
            main_frame._on_settings(None)
        elif action == "view_calendar":
            # Switch to calendar tab if it exists
            pass
        elif action == "view_affiliates":
            main_frame.notebook.SetSelection(3)  # Affiliates tab

    return handle_action
