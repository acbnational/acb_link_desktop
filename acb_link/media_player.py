"""
ACB Link - Media Player Module
Handles audio playback, recording, and media controls.
"""

import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import wx
import wx.media


class StreamRecorder:
    """Records audio streams to file."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.is_recording = False
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None

    def start(self, stream_url: str):
        """Start recording a stream."""
        if self.is_recording:
            return False

        self.stop_event.clear()
        self.is_recording = True
        self.thread = threading.Thread(target=self._record, args=(stream_url,), daemon=True)
        self.thread.start()
        return True

    def stop(self):
        """Stop recording."""
        if not self.is_recording:
            return

        self.stop_event.set()
        self.is_recording = False

        if self.on_complete:
            self.on_complete(self.output_path)

    def _record(self, stream_url: str):
        """Background recording thread."""
        try:
            import requests

            with requests.get(stream_url, stream=True, timeout=10) as response:
                with open(self.output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_event.is_set():
                            break
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            if self.on_error:
                wx.CallAfter(self.on_error, str(e))
            self.is_recording = False


class MediaPlayer:
    """Manages audio playback for streams and podcasts."""

    def __init__(self, parent: wx.Window):
        self.parent = parent
        self.media_ctrl: Optional[wx.media.MediaCtrl] = None
        self.is_playing = False
        self.is_paused = False
        self.current_url: Optional[str] = None
        self.current_title: Optional[str] = None
        self.volume = 1.0
        self.playback_speed = 1.0

        # Callbacks
        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_position_change: Optional[Callable[[int, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Recording
        self.recorder: Optional[StreamRecorder] = None

        # Timer for position updates
        self.position_timer: Optional[wx.Timer] = None

        self._init_media_ctrl()

    def _init_media_ctrl(self):
        """Initialize the media control."""
        try:
            self.media_ctrl = wx.media.MediaCtrl(
                self.parent, style=wx.SIMPLE_BORDER, szBackend=wx.media.MEDIABACKEND_WMP10
            )
            self.media_ctrl.Hide()

            # Bind events
            self.media_ctrl.Bind(wx.media.EVT_MEDIA_LOADED, self._on_media_loaded)
            self.media_ctrl.Bind(wx.media.EVT_MEDIA_STOP, self._on_media_stop)
            self.media_ctrl.Bind(wx.media.EVT_MEDIA_FINISHED, self._on_media_finished)

            # Position timer
            self.position_timer = wx.Timer(self.parent)
            self.parent.Bind(wx.EVT_TIMER, self._on_position_timer, self.position_timer)

        except Exception as e:
            self.media_ctrl = None
            if self.on_error:
                self.on_error(f"Failed to initialize media player: {e}")

    def _on_media_loaded(self, event):
        """Handle media loaded event."""
        if self.media_ctrl:
            self.media_ctrl.Play()
            self.is_playing = True
            self.is_paused = False
            self.position_timer.Start(1000)  # Update every second

            if self.on_state_change:
                self.on_state_change("playing")

    def _on_media_stop(self, event):
        """Handle media stop event."""
        pass

    def _on_media_finished(self, event):
        """Handle media finished event."""
        self.is_playing = False
        self.is_paused = False
        self.position_timer.Stop()

        # If recording, stop it
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()

        if self.on_state_change:
            self.on_state_change("stopped")

    def _on_position_timer(self, event):
        """Update position callback."""
        if self.media_ctrl and self.is_playing and self.on_position_change:
            try:
                pos = self.media_ctrl.Tell()
                length = self.media_ctrl.Length()
                self.on_position_change(pos, length)
            except Exception:
                pass

    def play(self, url: str, title: str = "") -> bool:
        """Play a media URL."""
        if not self.media_ctrl:
            return False

        self.current_url = url
        self.current_title = title

        try:
            if self.media_ctrl.Load(url):
                return True
            else:
                if self.on_error:
                    self.on_error("Failed to load media")
                return False
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
            return False

    def play_stream(self, stream: dict) -> bool:
        """Play an ACB Media stream."""
        url = f"https://streaming.live365.com/{stream['station']}"
        return self.play(url, stream["name"])

    def pause(self):
        """Pause playback."""
        if self.media_ctrl and self.is_playing:
            self.media_ctrl.Pause()
            self.is_paused = True
            self.is_playing = False

            if self.on_state_change:
                self.on_state_change("paused")

    def resume(self):
        """Resume playback."""
        if self.media_ctrl and self.is_paused:
            self.media_ctrl.Play()
            self.is_playing = True
            self.is_paused = False

            if self.on_state_change:
                self.on_state_change("playing")

    def stop(self):
        """Stop playback."""
        if self.media_ctrl:
            self.media_ctrl.Stop()
            self.is_playing = False
            self.is_paused = False
            self.position_timer.Stop()

            # Stop recording if active
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()

            if self.on_state_change:
                self.on_state_change("stopped")

    def seek(self, position_ms: int):
        """Seek to position in milliseconds."""
        if self.media_ctrl and (self.is_playing or self.is_paused):
            self.media_ctrl.Seek(position_ms)

    def seek_relative(self, offset_ms: int):
        """Seek relative to current position."""
        if self.media_ctrl:
            current = self.media_ctrl.Tell()
            new_pos = max(0, current + offset_ms)
            length = self.media_ctrl.Length()
            if length > 0:
                new_pos = min(new_pos, length)
            self.seek(new_pos)

    def skip_forward(self, seconds: int = 30):
        """Skip forward by seconds."""
        self.seek_relative(seconds * 1000)

    def skip_backward(self, seconds: int = 10):
        """Skip backward by seconds."""
        self.seek_relative(-seconds * 1000)

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.media_ctrl:
            self.media_ctrl.SetVolume(self.volume)

    def get_volume(self) -> float:
        """Get current volume."""
        return self.volume

    def mute(self):
        """Mute audio."""
        if self.media_ctrl:
            self.media_ctrl.SetVolume(0.0)

    def unmute(self):
        """Unmute audio."""
        if self.media_ctrl:
            self.media_ctrl.SetVolume(self.volume)

    def get_position(self) -> int:
        """Get current position in milliseconds."""
        if self.media_ctrl:
            return self.media_ctrl.Tell()
        return 0

    def get_length(self) -> int:
        """Get media length in milliseconds."""
        if self.media_ctrl:
            return self.media_ctrl.Length()
        return 0

    def start_recording(self, output_path: str) -> bool:
        """Start recording current stream."""
        if not self.current_url or self.recorder and self.recorder.is_recording:
            return False

        self.recorder = StreamRecorder(output_path)
        return self.recorder.start(self.current_url)

    def stop_recording(self) -> Optional[str]:
        """Stop recording and return output path."""
        if self.recorder and self.recorder.is_recording:
            path = self.recorder.output_path
            self.recorder.stop()
            return path
        return None

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.recorder is not None and self.recorder.is_recording

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.position_timer:
            self.position_timer.Stop()


def format_time(ms: int) -> str:
    """Format milliseconds to MM:SS or HH:MM:SS."""
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60

    if hours > 0:
        return f"{hours}:{minutes % 60:02d}:{seconds % 60:02d}"
    return f"{minutes}:{seconds % 60:02d}"


def generate_recording_filename(stream_name: str, recording_path: str, format: str = "mp3") -> str:
    """Generate a unique recording filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in stream_name if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_name = safe_name.replace(" ", "_")
    filename = f"{safe_name}_{timestamp}.{format}"
    return str(Path(recording_path) / filename)
