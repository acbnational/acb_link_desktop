"""
ACB Link - System Tray Module
Handles system tray icon, notifications, and tray menu.
"""

from typing import TYPE_CHECKING

import wx
import wx.adv

if TYPE_CHECKING:
    from .main_frame import MainFrame


class ACBLinkTaskBarIcon(wx.adv.TaskBarIcon):
    """System tray icon for ACB Link."""

    TBMENU_SHOW = wx.NewIdRef()
    TBMENU_PLAY_PAUSE = wx.NewIdRef()
    TBMENU_STOP = wx.NewIdRef()
    TBMENU_RECORD = wx.NewIdRef()
    TBMENU_STREAMS = wx.NewIdRef()
    TBMENU_SETTINGS = wx.NewIdRef()
    TBMENU_EXIT = wx.NewIdRef()

    def __init__(self, frame: "MainFrame"):
        super().__init__()
        self.frame = frame

        # Create icon
        self._set_icon("ACB Link")

        # Bind events
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_MENU, self.on_show, id=self.TBMENU_SHOW)
        self.Bind(wx.EVT_MENU, self.on_play_pause, id=self.TBMENU_PLAY_PAUSE)
        self.Bind(wx.EVT_MENU, self.on_stop, id=self.TBMENU_STOP)
        self.Bind(wx.EVT_MENU, self.on_record, id=self.TBMENU_RECORD)
        self.Bind(wx.EVT_MENU, self.on_settings, id=self.TBMENU_SETTINGS)
        self.Bind(wx.EVT_MENU, self.on_exit, id=self.TBMENU_EXIT)

    def _set_icon(self, tooltip: str, recording: bool = False):
        """Set the tray icon and tooltip."""
        # Create a simple icon using wx.ArtProvider or create one
        try:
            # Try to load custom icon
            icon = wx.Icon()
            # For now, use a built-in icon
            bmp = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16))
            icon.CopyFromBitmap(bmp)
            self.SetIcon(icon, tooltip)
        except Exception:
            pass

    def CreatePopupMenu(self) -> wx.Menu:
        """Create the tray context menu."""
        menu = wx.Menu()

        # Show/Hide
        if self.frame.IsShown():
            menu.Append(self.TBMENU_SHOW, "Hide Window")
        else:
            menu.Append(self.TBMENU_SHOW, "Show Window")

        menu.AppendSeparator()

        # Playback controls
        if hasattr(self.frame, "media_player") and self.frame.media_player:
            if self.frame.media_player.is_playing:
                menu.Append(self.TBMENU_PLAY_PAUSE, "⏸ Pause")
            elif self.frame.media_player.is_paused:
                menu.Append(self.TBMENU_PLAY_PAUSE, "▶ Resume")
            else:
                item = menu.Append(self.TBMENU_PLAY_PAUSE, "▶ Play")
                item.Enable(False)

            stop_item = menu.Append(self.TBMENU_STOP, "⏹ Stop")
            stop_item.Enable(
                self.frame.media_player.is_playing or self.frame.media_player.is_paused
            )

            menu.AppendSeparator()

            # Recording
            if self.frame.media_player.is_recording():
                menu.Append(self.TBMENU_RECORD, "⬛ Stop Recording")
            else:
                rec_item = menu.Append(self.TBMENU_RECORD, "● Start Recording")
                rec_item.Enable(self.frame.media_player.is_playing)

        menu.AppendSeparator()

        # Streams submenu
        streams_menu = wx.Menu()
        if hasattr(self.frame, "STREAMS"):
            for i, stream in enumerate(self.frame.STREAMS):
                item_id = wx.NewIdRef()
                streams_menu.Append(item_id, stream["name"])
                self.Bind(wx.EVT_MENU, lambda evt, s=stream: self.on_play_stream(s), id=item_id)
        menu.AppendSubMenu(streams_menu, "Streams")

        menu.AppendSeparator()

        # Settings
        menu.Append(self.TBMENU_SETTINGS, "Settings...")

        menu.AppendSeparator()

        # Exit
        menu.Append(self.TBMENU_EXIT, "Exit ACB Link")

        return menu

    def on_left_dclick(self, event):
        """Handle double-click on tray icon."""
        self.on_show(event)

    def on_show(self, event):
        """Show or hide the main window."""
        if self.frame.IsShown():
            self.frame.Hide()
        else:
            self.frame.Show()
            self.frame.Raise()
            self.frame.Restore()

    def on_play_pause(self, event):
        """Toggle play/pause."""
        if hasattr(self.frame, "media_player") and self.frame.media_player:
            if self.frame.media_player.is_playing:
                self.frame.media_player.pause()
            elif self.frame.media_player.is_paused:
                self.frame.media_player.resume()

    def on_stop(self, event):
        """Stop playback."""
        if hasattr(self.frame, "media_player") and self.frame.media_player:
            self.frame.media_player.stop()

    def on_record(self, event):
        """Toggle recording."""
        if hasattr(self.frame, "on_start_recording") and hasattr(self.frame, "on_stop_recording"):
            if self.frame.media_player and self.frame.media_player.is_recording():
                self.frame.on_stop_recording(None)
            else:
                self.frame.on_start_recording(None)

    def on_play_stream(self, stream: dict):
        """Play a specific stream."""
        if hasattr(self.frame, "_play_stream"):
            self.frame._play_stream(stream)

    def on_settings(self, event):
        """Open settings dialog."""
        if hasattr(self.frame, "on_settings"):
            self.frame.on_settings(None)

    def on_exit(self, event):
        """Exit the application."""
        self.frame.Close(force=True)

    def show_notification(
        self, title: str, message: str, flags: int = wx.ICON_INFORMATION, timeout: int = 5000
    ):
        """Show a balloon notification."""
        if self.IsOk():
            self.ShowBalloon(title, message, timeout, flags)

    def update_tooltip(self, text: str):
        """Update the tray icon tooltip."""
        self._set_icon(text)

    def set_recording_state(self, recording: bool):
        """Update icon to show recording state."""
        if recording:
            self._set_icon("ACB Link - Recording", recording=True)
        else:
            self._set_icon("ACB Link")

    def cleanup(self):
        """Clean up the tray icon."""
        self.RemoveIcon()
        self.Destroy()
