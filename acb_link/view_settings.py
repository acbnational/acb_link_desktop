"""
ACB Link - View Settings and UI Layout Management
Manages visibility of UI elements, pane navigation, and view preferences.
"""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import wx

# ============================================================================
# VIEW SETTINGS
# ============================================================================


@dataclass
class ViewSettings:
    """Settings for UI element visibility and layout."""

    # Element visibility
    show_menu_bar: bool = True
    show_toolbar: bool = True
    show_tab_bar: bool = True
    show_status_bar: bool = True
    show_player_panel: bool = True
    show_sidebar: bool = False
    show_now_playing_banner: bool = True

    # Layout preferences
    sidebar_width: int = 250
    player_panel_height: int = 80

    # Full screen
    full_screen: bool = False

    # Focus mode
    focus_mode: bool = False

    # Remember window position
    remember_window_position: bool = True
    window_x: int = -1
    window_y: int = -1
    window_width: int = 1000
    window_height: int = 700
    window_maximized: bool = False


class ViewSettingsManager:
    """Manages view settings persistence and application."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "view_settings.json")
        self.settings = self._load()
        self._callbacks: List[Callable[[str, Any], None]] = []

    def _load(self) -> ViewSettings:
        """Load settings from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ViewSettings(**data)
            except Exception:
                pass
        return ViewSettings()

    def save(self):
        """Save settings to storage."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, indent=2)

    def add_change_callback(self, callback: Callable[[str, Any], None]):
        """Add callback for setting changes."""
        self._callbacks.append(callback)

    def _notify_change(self, setting_name: str, value: Any):
        """Notify callbacks of setting change."""
        for callback in self._callbacks:
            try:
                callback(setting_name, value)
            except Exception:
                pass

    def set(self, setting_name: str, value: Any):
        """Set a view setting."""
        if hasattr(self.settings, setting_name):
            setattr(self.settings, setting_name, value)
            self.save()
            self._notify_change(setting_name, value)

    def get(self, setting_name: str, default: Any = None) -> Any:
        """Get a view setting."""
        return getattr(self.settings, setting_name, default)

    def toggle(self, setting_name: str) -> bool:
        """Toggle a boolean setting."""
        current = self.get(setting_name, False)
        new_value = not current
        self.set(setting_name, new_value)
        return new_value


# ============================================================================
# PANE NAVIGATION (F6 / Shift+F6)
# ============================================================================


class PaneType(Enum):
    """Types of navigable panes."""

    TAB_CONTENT = "tab_content"
    PLAYER_CONTROLS = "player_controls"
    SIDEBAR = "sidebar"
    TOOLBAR = "toolbar"
    STATUS_BAR = "status_bar"


@dataclass
class NavigablePane:
    """A pane that can receive focus via F6 navigation."""

    pane_type: PaneType
    window: wx.Window
    label: str
    is_visible: Callable[[], bool]
    focus_target: Optional[wx.Window] = None  # Specific control to focus within pane


class PaneNavigator:
    """
    Manages F6/Shift+F6 navigation between panes.
    Similar to VS Code and other professional applications.
    """

    def __init__(self, announcer: Optional[Callable[[str], None]] = None):
        self.panes: List[NavigablePane] = []
        self.current_index: int = 0
        self.announcer = announcer
        self.focus_callback: Optional[Callable[[NavigablePane], bool]] = None

    def set_focus_callback(self, callback: Optional[Callable[[NavigablePane], bool]]):
        """
        Set a custom focus callback for advanced focus handling.
        
        The callback receives the pane to focus and should return True if it
        handled the focus, False to use default behavior.
        """
        self.focus_callback = callback

    def register_pane(
        self,
        pane_type: PaneType,
        window: wx.Window,
        label: str,
        is_visible: Callable[[], bool],
        focus_target: Optional[wx.Window] = None,
    ):
        """Register a navigable pane."""
        self.panes.append(
            NavigablePane(
                pane_type=pane_type,
                window=window,
                label=label,
                is_visible=is_visible,
                focus_target=focus_target,
            )
        )

    def unregister_pane(self, pane_type: PaneType):
        """Unregister a pane."""
        self.panes = [p for p in self.panes if p.pane_type != pane_type]

    def get_visible_panes(self) -> List[NavigablePane]:
        """Get list of currently visible panes."""
        return [p for p in self.panes if p.is_visible()]

    def navigate_next(self) -> Optional[NavigablePane]:
        """Navigate to next pane (F6)."""
        visible = self.get_visible_panes()
        if not visible:
            return None

        self.current_index = (self.current_index + 1) % len(visible)
        return self._focus_pane(visible[self.current_index])

    def navigate_previous(self) -> Optional[NavigablePane]:
        """Navigate to previous pane (Shift+F6)."""
        visible = self.get_visible_panes()
        if not visible:
            return None

        self.current_index = (self.current_index - 1) % len(visible)
        return self._focus_pane(visible[self.current_index])

    def _focus_pane(self, pane: NavigablePane) -> NavigablePane:
        """Focus a pane and announce it."""
        # Try custom focus callback first
        if self.focus_callback:
            if self.focus_callback(pane):
                return pane

        # Default focus behavior
        target = pane.focus_target or pane.window

        if target and target.IsShown():
            target.SetFocus()

            if self.announcer:
                self.announcer(f"{pane.label} pane")

        return pane

    def focus_pane_by_type(self, pane_type: PaneType) -> bool:
        """Focus a specific pane by type."""
        for i, pane in enumerate(self.get_visible_panes()):
            if pane.pane_type == pane_type:
                self.current_index = i
                self._focus_pane(pane)
                return True
        return False

    def get_current_pane(self) -> Optional[NavigablePane]:
        """Get currently focused pane."""
        visible = self.get_visible_panes()
        if visible and 0 <= self.current_index < len(visible):
            return visible[self.current_index]
        return None


# ============================================================================
# FOCUS MODE
# ============================================================================


@dataclass
class FocusModeSettings:
    """Settings preserved when entering focus mode."""

    previous_show_menu_bar: bool = True
    previous_show_toolbar: bool = True
    previous_show_tab_bar: bool = True
    previous_show_status_bar: bool = True
    previous_show_sidebar: bool = False


class FocusModeManager:
    """
    Manages focus mode - a minimal interface showing only playback controls.
    Similar to "distraction-free" modes in editors.
    """

    def __init__(
        self,
        view_manager: ViewSettingsManager,
        on_enter: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        self.view_manager = view_manager
        self.on_enter = on_enter
        self.on_exit = on_exit
        self._saved_settings: Optional[FocusModeSettings] = None
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    def enter(self):
        """Enter focus mode."""
        if self._is_active:
            return

        # Save current settings
        self._saved_settings = FocusModeSettings(
            previous_show_menu_bar=self.view_manager.settings.show_menu_bar,
            previous_show_toolbar=self.view_manager.settings.show_toolbar,
            previous_show_tab_bar=self.view_manager.settings.show_tab_bar,
            previous_show_status_bar=self.view_manager.settings.show_status_bar,
            previous_show_sidebar=self.view_manager.settings.show_sidebar,
        )

        # Hide UI elements
        self.view_manager.set("show_toolbar", False)
        self.view_manager.set("show_tab_bar", False)
        self.view_manager.set("show_status_bar", False)
        self.view_manager.set("show_sidebar", False)
        self.view_manager.set("focus_mode", True)

        self._is_active = True

        if self.on_enter:
            self.on_enter()

    def exit(self):
        """Exit focus mode."""
        if not self._is_active:
            return

        # Restore settings
        if self._saved_settings:
            self.view_manager.set("show_menu_bar", self._saved_settings.previous_show_menu_bar)
            self.view_manager.set("show_toolbar", self._saved_settings.previous_show_toolbar)
            self.view_manager.set("show_tab_bar", self._saved_settings.previous_show_tab_bar)
            self.view_manager.set("show_status_bar", self._saved_settings.previous_show_status_bar)
            self.view_manager.set("show_sidebar", self._saved_settings.previous_show_sidebar)

        self.view_manager.set("focus_mode", False)
        self._is_active = False
        self._saved_settings = None

        if self.on_exit:
            self.on_exit()

    def toggle(self) -> bool:
        """Toggle focus mode."""
        if self._is_active:
            self.exit()
        else:
            self.enter()
        return self._is_active


# ============================================================================
# VISUAL SETTINGS FOR LOW VISION
# ============================================================================


@dataclass
class LowVisionSettings:
    """Visual settings optimized for low vision users."""

    # Font settings
    font_size: int = 12
    use_bold_text: bool = False
    font_family: str = ""  # Empty = system default

    # Colors
    high_contrast: bool = False
    color_scheme: str = (
        "system"  # "system", "light", "dark", "high_contrast_light", "high_contrast_dark"
    )
    custom_foreground: str = ""
    custom_background: str = ""

    # Cursor and focus
    large_cursor: bool = False
    thick_focus_indicator: bool = True
    focus_indicator_width: int = 3

    # Spacing
    increased_spacing: bool = False
    line_height_multiplier: float = 1.2
    button_padding: int = 8

    # Animations
    reduce_motion: bool = False


# Built-in color schemes optimized for accessibility
COLOR_SCHEMES = {
    "light": {
        "name": "Light",
        "background": "#FFFFFF",
        "foreground": "#1A1A1A",
        "accent": "#0066CC",
        "secondary_bg": "#F5F5F5",
        "border": "#CCCCCC",
        "error": "#CC0000",
        "success": "#006600",
        "warning": "#CC6600",
    },
    "dark": {
        "name": "Dark",
        "background": "#1E1E1E",
        "foreground": "#E0E0E0",
        "accent": "#4DA6FF",
        "secondary_bg": "#2D2D2D",
        "border": "#404040",
        "error": "#FF6666",
        "success": "#66CC66",
        "warning": "#FFAA33",
    },
    "high_contrast_dark": {
        "name": "High Contrast Dark",
        "background": "#000000",
        "foreground": "#FFFFFF",
        "accent": "#00FFFF",
        "secondary_bg": "#1A1A1A",
        "border": "#FFFFFF",
        "error": "#FF0000",
        "success": "#00FF00",
        "warning": "#FFFF00",
    },
    "high_contrast_light": {
        "name": "High Contrast Light",
        "background": "#FFFFFF",
        "foreground": "#000000",
        "accent": "#0000CC",
        "secondary_bg": "#F0F0F0",
        "border": "#000000",
        "error": "#CC0000",
        "success": "#006600",
        "warning": "#996600",
    },
    "yellow_on_black": {
        "name": "Yellow on Black",
        "background": "#000000",
        "foreground": "#FFFF00",
        "accent": "#FFD700",
        "secondary_bg": "#1A1A00",
        "border": "#FFFF00",
        "error": "#FF6666",
        "success": "#66FF66",
        "warning": "#FFA500",
    },
    "white_on_black": {
        "name": "White on Black",
        "background": "#000000",
        "foreground": "#FFFFFF",
        "accent": "#00BFFF",
        "secondary_bg": "#1A1A1A",
        "border": "#FFFFFF",
        "error": "#FF6666",
        "success": "#66FF66",
        "warning": "#FFA500",
    },
    "green_on_black": {
        "name": "Green on Black",
        "background": "#000000",
        "foreground": "#00FF00",
        "accent": "#00FFFF",
        "secondary_bg": "#001A00",
        "border": "#00FF00",
        "error": "#FF6666",
        "success": "#66FF66",
        "warning": "#FFFF00",
    },
    "black_on_white": {
        "name": "Black on White",
        "background": "#FFFFFF",
        "foreground": "#000000",
        "accent": "#0000CC",
        "secondary_bg": "#F0F0F0",
        "border": "#000000",
        "error": "#CC0000",
        "success": "#006600",
        "warning": "#996600",
    },
    "blue_on_white": {
        "name": "Blue on White",
        "background": "#FFFFFF",
        "foreground": "#000080",
        "accent": "#0066CC",
        "secondary_bg": "#F0F0FF",
        "border": "#000080",
        "error": "#CC0000",
        "success": "#006600",
        "warning": "#996600",
    },
}


class VisualSettingsManager:
    """Manages visual settings for accessibility."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "visual_settings.json")
        self.settings = self._load()
        self._callbacks: List[Callable[[], None]] = []

    def _load(self) -> LowVisionSettings:
        """Load settings."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return LowVisionSettings(**data)
            except Exception:
                pass
        return LowVisionSettings()

    def save(self):
        """Save settings."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, indent=2)

    def add_change_callback(self, callback: Callable[[], None]):
        """Add callback for when settings change."""
        self._callbacks.append(callback)

    def notify_change(self):
        """Notify callbacks of settings change."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass

    def get_color_scheme(self) -> Dict[str, str]:
        """Get current color scheme."""
        scheme_name = self.settings.color_scheme
        if scheme_name in COLOR_SCHEMES:
            return COLOR_SCHEMES[scheme_name]
        return COLOR_SCHEMES["light"]

    def apply_to_window(self, window: wx.Window):
        """Apply visual settings to a window and its children."""
        scheme = self.get_color_scheme()

        # Apply colors
        bg = wx.Colour(scheme["background"])
        fg = wx.Colour(scheme["foreground"])

        window.SetBackgroundColour(bg)
        window.SetForegroundColour(fg)

        # Apply font
        font = window.GetFont()
        font.SetPointSize(self.settings.font_size)
        if self.settings.use_bold_text:
            font.SetWeight(wx.FONTWEIGHT_BOLD)
        if self.settings.font_family:
            font.SetFaceName(self.settings.font_family)
        window.SetFont(font)

        # Recursively apply to children
        for child in window.GetChildren():
            self.apply_to_window(child)

        window.Refresh()


# ============================================================================
# VIEW SETTINGS DIALOG
# ============================================================================


class ViewSettingsDialog(wx.Dialog):
    """Dialog for configuring view settings."""

    def __init__(
        self,
        parent: wx.Window,
        view_manager: ViewSettingsManager,
        visual_manager: VisualSettingsManager,
    ):
        super().__init__(
            parent, title="View Settings", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.view_manager = view_manager
        self.visual_manager = visual_manager

        self.SetSize(wx.Size(500, 550))
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Notebook for tabs
        notebook = wx.Notebook(panel)

        # UI Elements tab
        ui_panel = self._create_ui_elements_tab(notebook)
        notebook.AddPage(ui_panel, "UI Elements")

        # Appearance tab
        appearance_panel = self._create_appearance_tab(notebook)
        notebook.AddPage(appearance_panel, "Appearance")

        # Accessibility tab
        accessibility_panel = self._create_accessibility_tab(notebook)
        notebook.AddPage(accessibility_panel, "Accessibility")

        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_apply = wx.Button(panel, label="&Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self._on_apply)
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)

        btn_sizer.Add(btn_apply, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(main_sizer)

    def _create_ui_elements_tab(self, parent: wx.Window) -> wx.Panel:
        """Create UI elements visibility tab."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Show/hide checkboxes
        elements = [
            ("show_menu_bar", "Show &Menu Bar"),
            ("show_toolbar", "Show &Toolbar"),
            ("show_tab_bar", "Show &Tab Bar"),
            ("show_status_bar", "Show &Status Bar"),
            ("show_player_panel", "Show &Player Controls"),
            ("show_now_playing_banner", "Show &Now Playing Banner"),
            ("show_sidebar", "Show Side&bar"),
        ]

        self.ui_checks = {}
        for setting_name, label in elements:
            check = wx.CheckBox(panel, label=label)
            check.SetValue(self.view_manager.get(setting_name, True))
            self.ui_checks[setting_name] = check
            sizer.Add(check, 0, wx.ALL, 8)

        # Window position
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 10)

        self.remember_pos_check = wx.CheckBox(panel, label="&Remember window position and size")
        self.remember_pos_check.SetValue(self.view_manager.settings.remember_window_position)
        sizer.Add(self.remember_pos_check, 0, wx.ALL, 8)

        panel.SetSizer(sizer)
        return panel

    def _create_appearance_tab(self, parent: wx.Window) -> wx.Panel:
        """Create appearance settings tab."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Color scheme
        scheme_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scheme_sizer.Add(
            wx.StaticText(panel, label="Color scheme:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10
        )

        scheme_names = [COLOR_SCHEMES[k]["name"] for k in COLOR_SCHEMES]
        self.scheme_choice = wx.Choice(panel, choices=scheme_names)

        current_scheme = self.visual_manager.settings.color_scheme
        for i, key in enumerate(COLOR_SCHEMES):
            if key == current_scheme:
                self.scheme_choice.SetSelection(i)
                break

        scheme_sizer.Add(self.scheme_choice, 1)
        sizer.Add(scheme_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Font size
        font_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_sizer.Add(
            wx.StaticText(panel, label="Font size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10
        )

        self.font_spin = wx.SpinCtrl(
            panel, min=8, max=32, initial=self.visual_manager.settings.font_size
        )
        self.font_spin.SetName("Font size")
        font_sizer.Add(self.font_spin, 0, wx.RIGHT, 5)
        font_sizer.Add(wx.StaticText(panel, label="pt"), 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(font_sizer, 0, wx.ALL, 10)

        # Bold text
        self.bold_check = wx.CheckBox(panel, label="Use &bold text")
        self.bold_check.SetValue(self.visual_manager.settings.use_bold_text)
        sizer.Add(self.bold_check, 0, wx.ALL, 10)

        # Increased spacing
        self.spacing_check = wx.CheckBox(panel, label="&Increased spacing (easier to read)")
        self.spacing_check.SetValue(self.visual_manager.settings.increased_spacing)
        sizer.Add(self.spacing_check, 0, wx.ALL, 10)

        panel.SetSizer(sizer)
        return panel

    def _create_accessibility_tab(self, parent: wx.Window) -> wx.Panel:
        """Create accessibility settings tab."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # High contrast
        self.high_contrast_check = wx.CheckBox(panel, label="&High contrast mode")
        self.high_contrast_check.SetValue(self.visual_manager.settings.high_contrast)
        sizer.Add(self.high_contrast_check, 0, wx.ALL, 10)

        # Large cursor
        self.large_cursor_check = wx.CheckBox(panel, label="&Large cursor")
        self.large_cursor_check.SetValue(self.visual_manager.settings.large_cursor)
        sizer.Add(self.large_cursor_check, 0, wx.ALL, 10)

        # Thick focus indicator
        self.thick_focus_check = wx.CheckBox(panel, label="&Thick focus indicator")
        self.thick_focus_check.SetValue(self.visual_manager.settings.thick_focus_indicator)
        sizer.Add(self.thick_focus_check, 0, wx.ALL, 10)

        # Reduce motion
        self.reduce_motion_check = wx.CheckBox(panel, label="&Reduce motion/animations")
        self.reduce_motion_check.SetValue(self.visual_manager.settings.reduce_motion)
        sizer.Add(self.reduce_motion_check, 0, wx.ALL, 10)

        # Focus indicator width
        focus_width_sizer = wx.BoxSizer(wx.HORIZONTAL)
        focus_width_sizer.Add(
            wx.StaticText(panel, label="Focus indicator width:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            10,
        )
        self.focus_width_spin = wx.SpinCtrl(
            panel, min=1, max=10, initial=self.visual_manager.settings.focus_indicator_width
        )
        self.focus_width_spin.SetName("Focus indicator width pixels")
        focus_width_sizer.Add(self.focus_width_spin, 0, wx.RIGHT, 5)
        focus_width_sizer.Add(wx.StaticText(panel, label="pixels"), 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(focus_width_sizer, 0, wx.ALL, 10)

        panel.SetSizer(sizer)
        return panel

    def _apply_settings(self):
        """Apply all settings."""
        # UI elements
        for setting_name, check in self.ui_checks.items():
            self.view_manager.set(setting_name, check.GetValue())

        self.view_manager.set("remember_window_position", self.remember_pos_check.GetValue())

        # Visual settings
        scheme_idx = self.scheme_choice.GetSelection()
        if scheme_idx >= 0:
            scheme_key = list(COLOR_SCHEMES.keys())[scheme_idx]
            self.visual_manager.settings.color_scheme = scheme_key

        self.visual_manager.settings.font_size = self.font_spin.GetValue()
        self.visual_manager.settings.use_bold_text = self.bold_check.GetValue()
        self.visual_manager.settings.increased_spacing = self.spacing_check.GetValue()
        self.visual_manager.settings.high_contrast = self.high_contrast_check.GetValue()
        self.visual_manager.settings.large_cursor = self.large_cursor_check.GetValue()
        self.visual_manager.settings.thick_focus_indicator = self.thick_focus_check.GetValue()
        self.visual_manager.settings.reduce_motion = self.reduce_motion_check.GetValue()
        self.visual_manager.settings.focus_indicator_width = self.focus_width_spin.GetValue()

        self.visual_manager.save()
        self.visual_manager.notify_change()

    def _on_apply(self, event):
        """Apply settings without closing."""
        self._apply_settings()

    def _on_ok(self, event):
        """Apply settings and close."""
        self._apply_settings()
        self.EndModal(wx.ID_OK)


# ============================================================================
# STREAM SCHEDULE PREVIEW
# ============================================================================


@dataclass
class ScheduleEntry:
    """An entry in the stream schedule."""

    stream_name: str
    program_title: str
    start_time: str  # HH:MM format
    end_time: str
    description: str = ""
    day_of_week: int = -1  # 0=Monday, -1=everyday


class StreamScheduleManager:
    """Manages stream schedule data."""

    def __init__(self, schedule_url: Optional[str] = None):
        self.schedule_url = schedule_url
        self.schedules: Dict[str, List[ScheduleEntry]] = {}
        self._last_update: Optional[str] = None

    def get_current_program(self, stream_name: str) -> Optional[ScheduleEntry]:
        """Get currently playing program for a stream."""
        if stream_name not in self.schedules:
            return None

        from datetime import datetime

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday()

        for entry in self.schedules.get(stream_name, []):
            if entry.day_of_week != -1 and entry.day_of_week != current_day:
                continue
            if entry.start_time <= current_time < entry.end_time:
                return entry

        return None

    def get_upcoming(self, stream_name: str, count: int = 5) -> List[ScheduleEntry]:
        """Get upcoming programs for a stream."""
        if stream_name not in self.schedules:
            return []

        from datetime import datetime

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday()

        upcoming = []
        for entry in self.schedules.get(stream_name, []):
            if entry.day_of_week != -1 and entry.day_of_week != current_day:
                continue
            if entry.start_time > current_time:
                upcoming.append(entry)
                if len(upcoming) >= count:
                    break

        return upcoming

    def set_schedule(self, stream_name: str, entries: List[ScheduleEntry]):
        """Set schedule for a stream."""
        self.schedules[stream_name] = entries

    def get_schedule_text(self, stream_name: str) -> str:
        """Get formatted schedule text for a stream."""
        current = self.get_current_program(stream_name)
        upcoming = self.get_upcoming(stream_name, 3)

        lines = [f"Schedule for {stream_name}"]
        lines.append("-" * 40)

        if current:
            lines.append(f"NOW: {current.program_title} (until {current.end_time})")
            if current.description:
                lines.append(f"     {current.description}")
        else:
            lines.append("No current program information")

        if upcoming:
            lines.append("\nComing up:")
            for entry in upcoming:
                lines.append(f"  {entry.start_time}: {entry.program_title}")

        return "\n".join(lines)


class SchedulePreviewDialog(wx.Dialog):
    """Dialog showing stream schedule preview."""

    def __init__(
        self, parent: wx.Window, schedule_manager: StreamScheduleManager, stream_name: str
    ):
        super().__init__(
            parent,
            title=f"Schedule: {stream_name}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.schedule_manager = schedule_manager
        self.stream_name = stream_name

        self.SetSize(wx.Size(400, 350))
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Schedule text
        schedule_text = self.schedule_manager.get_schedule_text(self.stream_name)
        text_ctrl = wx.TextCtrl(
            panel, value=schedule_text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        text_ctrl.SetFont(
            wx.Font(11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        )
        main_sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Close button
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        panel.SetSizer(main_sizer)


# ============================================================================
# FAVORITES QUICK DIAL
# ============================================================================


class FavoritesQuickDial:
    """
    Manages Alt+F1 through Alt+F5 quick dial for favorites.
    """

    MAX_QUICK_DIAL = 5

    def __init__(
        self,
        get_favorites: Callable[[], List[Any]],
        play_callback: Callable[[Any], None],
        announcer: Optional[Callable[[str], None]] = None,
    ):
        self.get_favorites = get_favorites
        self.play_callback = play_callback
        self.announcer = announcer

    def play_by_index(self, index: int) -> bool:
        """
        Play favorite by quick dial index (0-4).
        Returns True if successful.
        """
        if index < 0 or index >= self.MAX_QUICK_DIAL:
            return False

        favorites = self.get_favorites()
        if index >= len(favorites):
            if self.announcer:
                self.announcer(f"No favorite assigned to quick dial {index + 1}")
            return False

        favorite = favorites[index]
        self.play_callback(favorite)

        if self.announcer:
            name = getattr(favorite, "name", str(favorite))
            self.announcer(f"Playing quick dial {index + 1}: {name}")

        return True

    def get_quick_dial_list(self) -> List[str]:
        """Get list of quick dial assignments."""
        favorites = self.get_favorites()
        result = []
        for i in range(self.MAX_QUICK_DIAL):
            if i < len(favorites):
                name = getattr(favorites[i], "name", str(favorites[i]))
                result.append(f"Alt+F{i + 1}: {name}")
            else:
                result.append(f"Alt+F{i + 1}: (not assigned)")
        return result
