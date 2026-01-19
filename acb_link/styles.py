"""
ACB Link - Visual Styles and Theming
Modern, accessible visual styling for all UI components.
"""

from dataclasses import dataclass
from typing import Dict, Optional

import wx


@dataclass
class ColorScheme:
    """Color scheme for a theme."""

    # Primary colors
    background: str = "#FFFFFF"
    foreground: str = "#1A1A1A"
    accent: str = "#0078D4"
    accent_light: str = "#4CC2FF"
    accent_dark: str = "#005A9E"

    # Surface colors
    surface: str = "#F5F5F5"
    surface_hover: str = "#E8E8E8"
    surface_active: str = "#D0D0D0"

    # Panel colors
    panel_bg: str = "#FAFAFA"
    panel_border: str = "#E0E0E0"

    # Control colors
    button_bg: str = "#E1E1E1"
    button_fg: str = "#1A1A1A"
    button_hover: str = "#D0D0D0"
    button_active: str = "#B0B0B0"
    button_primary_bg: str = "#0078D4"
    button_primary_fg: str = "#FFFFFF"

    # List colors
    list_bg: str = "#FFFFFF"
    list_fg: str = "#1A1A1A"
    list_selected_bg: str = "#0078D4"
    list_selected_fg: str = "#FFFFFF"
    list_hover_bg: str = "#E8F4FD"
    list_alternate_bg: str = "#FAFAFA"

    # Input colors
    input_bg: str = "#FFFFFF"
    input_fg: str = "#1A1A1A"
    input_border: str = "#CCCCCC"
    input_border_focus: str = "#0078D4"

    # Status colors
    success: str = "#107C10"
    warning: str = "#FF8C00"
    error: str = "#D13438"
    info: str = "#0078D4"

    # Text colors
    text_primary: str = "#1A1A1A"
    text_secondary: str = "#666666"
    text_disabled: str = "#999999"
    text_link: str = "#0078D4"

    # Player control colors
    player_bg: str = "#F0F0F0"
    player_fg: str = "#1A1A1A"
    player_accent: str = "#0078D4"
    progress_bg: str = "#E0E0E0"
    progress_fg: str = "#0078D4"

    # Header colors
    header_bg: str = "#0078D4"
    header_fg: str = "#FFFFFF"


# Pre-defined color schemes
LIGHT_SCHEME = ColorScheme()

DARK_SCHEME = ColorScheme(
    background="#1E1E1E",
    foreground="#E0E0E0",
    accent="#4CC2FF",
    accent_light="#7DD4FF",
    accent_dark="#3399CC",
    surface="#252525",
    surface_hover="#2D2D2D",
    surface_active="#3C3C3C",
    panel_bg="#1E1E1E",
    panel_border="#3C3C3C",
    button_bg="#3C3C3C",
    button_fg="#E0E0E0",
    button_hover="#4C4C4C",
    button_active="#5C5C5C",
    button_primary_bg="#4CC2FF",
    button_primary_fg="#000000",
    list_bg="#252525",
    list_fg="#E0E0E0",
    list_selected_bg="#4CC2FF",
    list_selected_fg="#000000",
    list_hover_bg="#2D3748",
    list_alternate_bg="#2A2A2A",
    input_bg="#2D2D2D",
    input_fg="#E0E0E0",
    input_border="#4C4C4C",
    input_border_focus="#4CC2FF",
    success="#6CCB5F",
    warning="#FFA500",
    error="#F1707A",
    info="#4CC2FF",
    text_primary="#E0E0E0",
    text_secondary="#A0A0A0",
    text_disabled="#666666",
    text_link="#4CC2FF",
    player_bg="#252525",
    player_fg="#E0E0E0",
    player_accent="#4CC2FF",
    progress_bg="#3C3C3C",
    progress_fg="#4CC2FF",
    header_bg="#2D2D2D",
    header_fg="#FFFFFF",
)

HIGH_CONTRAST_LIGHT = ColorScheme(
    background="#FFFFFF",
    foreground="#000000",
    accent="#0000FF",
    accent_light="#4444FF",
    accent_dark="#000099",
    surface="#FFFFFF",
    surface_hover="#FFFF00",
    surface_active="#FFFF00",
    panel_bg="#FFFFFF",
    panel_border="#000000",
    button_bg="#FFFFFF",
    button_fg="#000000",
    button_hover="#FFFF00",
    button_active="#FFFF00",
    button_primary_bg="#000080",
    button_primary_fg="#FFFFFF",
    list_bg="#FFFFFF",
    list_fg="#000000",
    list_selected_bg="#000080",
    list_selected_fg="#FFFFFF",
    list_hover_bg="#FFFF00",
    list_alternate_bg="#F0F0F0",
    input_bg="#FFFFFF",
    input_fg="#000000",
    input_border="#000000",
    input_border_focus="#0000FF",
    success="#008000",
    warning="#FF8C00",
    error="#FF0000",
    info="#0000FF",
    text_primary="#000000",
    text_secondary="#000000",
    text_disabled="#666666",
    text_link="#0000FF",
    player_bg="#FFFFFF",
    player_fg="#000000",
    player_accent="#0000FF",
    progress_bg="#CCCCCC",
    progress_fg="#0000FF",
    header_bg="#000080",
    header_fg="#FFFFFF",
)

HIGH_CONTRAST_DARK = ColorScheme(
    background="#000000",
    foreground="#FFFFFF",
    accent="#00FFFF",
    accent_light="#66FFFF",
    accent_dark="#00CCCC",
    surface="#000000",
    surface_hover="#FFFF00",
    surface_active="#FFFF00",
    panel_bg="#000000",
    panel_border="#FFFFFF",
    button_bg="#000000",
    button_fg="#FFFFFF",
    button_hover="#FFFF00",
    button_active="#FFFF00",
    button_primary_bg="#FFFF00",
    button_primary_fg="#000000",
    list_bg="#000000",
    list_fg="#FFFFFF",
    list_selected_bg="#FFFF00",
    list_selected_fg="#000000",
    list_hover_bg="#00FFFF",
    list_alternate_bg="#1A1A1A",
    input_bg="#000000",
    input_fg="#FFFFFF",
    input_border="#FFFFFF",
    input_border_focus="#00FFFF",
    success="#00FF00",
    warning="#FFFF00",
    error="#FF0000",
    info="#00FFFF",
    text_primary="#FFFFFF",
    text_secondary="#FFFFFF",
    text_disabled="#808080",
    text_link="#00FFFF",
    player_bg="#000000",
    player_fg="#FFFFFF",
    player_accent="#00FFFF",
    progress_bg="#333333",
    progress_fg="#00FFFF",
    header_bg="#000000",
    header_fg="#FFFFFF",
)

# Scheme registry
COLOR_SCHEMES: Dict[str, ColorScheme] = {
    "light": LIGHT_SCHEME,
    "dark": DARK_SCHEME,
    "high_contrast_light": HIGH_CONTRAST_LIGHT,
    "high_contrast_dark": HIGH_CONTRAST_DARK,
}


def hex_to_colour(hex_color: str) -> wx.Colour:
    """Convert hex color string to wx.Colour."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return wx.Colour(r, g, b)


class StyleManager:
    """Manages application styling and theme application."""

    def __init__(self, scheme_name: str = "light"):
        self.scheme_name = scheme_name
        self.scheme = COLOR_SCHEMES.get(scheme_name, LIGHT_SCHEME)
        self.font_size = 11
        self.font_family = "Segoe UI"

    def set_scheme(self, scheme_name: str):
        """Set the color scheme."""
        if scheme_name in COLOR_SCHEMES:
            self.scheme_name = scheme_name
            self.scheme = COLOR_SCHEMES[scheme_name]

    def set_font_size(self, size: int):
        """Set the base font size."""
        self.font_size = max(8, min(24, size))

    def get_font(self, size_offset: int = 0, bold: bool = False) -> wx.Font:
        """Get a font with the current settings."""
        size = self.font_size + size_offset
        weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
        return wx.Font(
            size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, weight, faceName=self.font_family
        )

    def style_frame(self, frame: wx.Frame):
        """Apply styling to the main frame."""
        frame.SetBackgroundColour(hex_to_colour(self.scheme.background))
        frame.SetForegroundColour(hex_to_colour(self.scheme.foreground))
        frame.SetFont(self.get_font())

    def style_panel(self, panel: wx.Panel, elevated: bool = False):
        """Apply styling to a panel."""
        bg = self.scheme.surface if elevated else self.scheme.background
        panel.SetBackgroundColour(hex_to_colour(bg))
        panel.SetForegroundColour(hex_to_colour(self.scheme.foreground))
        panel.SetFont(self.get_font())

    def style_button(self, button: wx.Button, primary: bool = False):
        """Apply styling to a button."""
        if primary:
            button.SetBackgroundColour(hex_to_colour(self.scheme.button_primary_bg))
            button.SetForegroundColour(hex_to_colour(self.scheme.button_primary_fg))
        else:
            button.SetBackgroundColour(hex_to_colour(self.scheme.button_bg))
            button.SetForegroundColour(hex_to_colour(self.scheme.button_fg))
        button.SetFont(self.get_font())

    def style_list_ctrl(self, list_ctrl: wx.ListCtrl):
        """Apply styling to a list control."""
        list_ctrl.SetBackgroundColour(hex_to_colour(self.scheme.list_bg))
        list_ctrl.SetForegroundColour(hex_to_colour(self.scheme.list_fg))
        list_ctrl.SetFont(self.get_font())

    def style_text_ctrl(self, text_ctrl: wx.TextCtrl):
        """Apply styling to a text control."""
        text_ctrl.SetBackgroundColour(hex_to_colour(self.scheme.input_bg))
        text_ctrl.SetForegroundColour(hex_to_colour(self.scheme.input_fg))
        text_ctrl.SetFont(self.get_font())

    def style_static_text(self, text: wx.StaticText, secondary: bool = False):
        """Apply styling to a static text."""
        color = self.scheme.text_secondary if secondary else self.scheme.text_primary
        text.SetForegroundColour(hex_to_colour(color))
        text.SetFont(self.get_font())

    def style_header(self, text: wx.StaticText, level: int = 1):
        """Apply header styling to a static text."""
        size_offset = {1: 8, 2: 5, 3: 3}.get(level, 0)
        text.SetForegroundColour(hex_to_colour(self.scheme.text_primary))
        text.SetFont(self.get_font(size_offset=size_offset, bold=True))

    def style_notebook(self, notebook: wx.Notebook):
        """Apply styling to a notebook."""
        notebook.SetBackgroundColour(hex_to_colour(self.scheme.background))
        notebook.SetForegroundColour(hex_to_colour(self.scheme.foreground))
        notebook.SetFont(self.get_font())

    def style_slider(self, slider: wx.Slider):
        """Apply styling to a slider."""
        slider.SetBackgroundColour(hex_to_colour(self.scheme.surface))

    def style_player_panel(self, panel: wx.Panel):
        """Apply styling to the player control panel."""
        panel.SetBackgroundColour(hex_to_colour(self.scheme.player_bg))
        panel.SetForegroundColour(hex_to_colour(self.scheme.player_fg))

    def apply_to_window(self, window: wx.Window):
        """Recursively apply styling to a window and all children."""
        self._apply_style_recursive(window)

    def _apply_style_recursive(self, window: wx.Window):
        """Recursively apply styles to window hierarchy."""
        # Apply based on widget type
        if isinstance(window, wx.Frame):
            self.style_frame(window)
        elif isinstance(window, wx.Notebook):
            self.style_notebook(window)
        elif isinstance(window, wx.ListCtrl):
            self.style_list_ctrl(window)
        elif isinstance(window, wx.TextCtrl):
            self.style_text_ctrl(window)
        elif isinstance(window, wx.Button):
            self.style_button(window)
        elif isinstance(window, wx.Slider):
            self.style_slider(window)
        elif isinstance(window, wx.StaticText):
            self.style_static_text(window)
        elif isinstance(window, wx.Panel):
            self.style_panel(window)

        # Recurse into children
        for child in window.GetChildren():
            self._apply_style_recursive(child)


# Shared style constants for modern look
class UIConstants:
    """UI constants for consistent styling."""

    # Spacing
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE = 20

    # Border radius (for custom drawn controls)
    BORDER_RADIUS_SMALL = 4
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE = 12

    # Sizes
    BUTTON_HEIGHT = 32
    BUTTON_MIN_WIDTH = 80
    ICON_BUTTON_SIZE = 36

    # Player bar
    PLAYER_BAR_HEIGHT = 60
    PROGRESS_BAR_HEIGHT = 4

    # List items
    LIST_ITEM_HEIGHT = 40
    LIST_ICON_SIZE = 24

    # Headers
    HEADER_HEIGHT = 48

    # Transitions (ms)
    TRANSITION_FAST = 100
    TRANSITION_NORMAL = 200
    TRANSITION_SLOW = 300


def get_scheme_for_system_theme() -> str:
    """Detect system theme and return appropriate scheme name."""
    # Try to detect Windows dark mode
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value else "dark"
    except Exception:
        return "light"


# Global style manager instance
_style_manager: Optional[StyleManager] = None


def get_style_manager() -> StyleManager:
    """Get the global style manager instance."""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager


def set_global_scheme(scheme_name: str):
    """Set the global color scheme."""
    get_style_manager().set_scheme(scheme_name)
