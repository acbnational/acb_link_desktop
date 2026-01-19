"""
ACB Link - Native Audio Player Module
Windows Media Foundation backend with VLC/FFmpeg fallback.
Provides gapless playback, audio normalization, and sleep timer.
"""

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, List, Optional

try:
    import wx
    import wx.media

    HAS_WX_MEDIA = True
except ImportError:
    HAS_WX_MEDIA = False

# Try VLC as a fallback
try:
    import vlc  # type: ignore[import-untyped]

    HAS_VLC = True
except ImportError:
    HAS_VLC = False


class PlayerState(Enum):
    """Player state enumeration."""

    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"


class AudioBackend(Enum):
    """Audio backend options."""

    WMF = "wmf"  # Windows Media Foundation
    VLC = "vlc"
    AUTO = "auto"


@dataclass
class PlaybackInfo:
    """Current playback information."""

    state: PlayerState = PlayerState.STOPPED
    title: str = ""
    url: str = ""
    position: float = 0.0  # seconds
    duration: float = 0.0  # seconds
    volume: float = 1.0  # 0.0 to 1.0
    speed: float = 1.0
    is_muted: bool = False


class SleepTimer:
    """
    Sleep timer for automatic playback stop.
    """

    def __init__(self, on_timer_complete: Optional[Callable[[], None]] = None):
        self.on_timer_complete = on_timer_complete
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._target_time: Optional[datetime] = None
        self._remaining_seconds: int = 0
        self._is_active = False

    def start(self, minutes: int):
        """Start the sleep timer."""
        self.stop()

        self._remaining_seconds = minutes * 60
        self._target_time = datetime.now() + timedelta(minutes=minutes)
        self._stop_event.clear()
        self._is_active = True

        self._timer_thread = threading.Thread(
            target=self._timer_loop, daemon=True, name="SleepTimer"
        )
        self._timer_thread.start()

    def stop(self):
        """Stop the sleep timer."""
        self._stop_event.set()
        self._is_active = False
        self._target_time = None
        self._remaining_seconds = 0

        if self._timer_thread:
            self._timer_thread.join(timeout=1.0)
            self._timer_thread = None

    def _timer_loop(self):
        """Timer thread loop."""
        while not self._stop_event.is_set():
            if self._target_time and datetime.now() >= self._target_time:
                if self.on_timer_complete:
                    self.on_timer_complete()
                self._is_active = False
                break

            # Update remaining time
            if self._target_time:
                remaining = (self._target_time - datetime.now()).total_seconds()
                self._remaining_seconds = max(0, int(remaining))

            time.sleep(1)

    @property
    def is_active(self) -> bool:
        """Check if timer is active."""
        return self._is_active

    @property
    def remaining_seconds(self) -> int:
        """Get remaining seconds."""
        return self._remaining_seconds

    def get_remaining_str(self) -> str:
        """Get remaining time as formatted string."""
        if not self._is_active:
            return ""

        mins = self._remaining_seconds // 60
        secs = self._remaining_seconds % 60
        return f"{mins:02d}:{secs:02d}"


class NativeAudioPlayer:
    """
    Native audio player with multiple backend support.
    Uses Windows Media Foundation by default with VLC fallback.
    """

    def __init__(self, parent_window=None, backend: AudioBackend = AudioBackend.AUTO):
        self.parent = parent_window
        self._backend = backend
        self._state = PlayerState.STOPPED
        self._info = PlaybackInfo()

        # Backend instances
        self._vlc_instance = None
        self._vlc_player = None
        self._wx_media = None

        # Queue for gapless playback
        self._queue: List[str] = []
        self._queue_index = 0
        self._auto_advance = True

        # Sleep timer
        self.sleep_timer = SleepTimer(on_timer_complete=self._on_sleep_timer)

        # Callbacks
        self.on_state_change: Optional[Callable[[PlayerState], None]] = None
        self.on_position_update: Optional[Callable[[float, float], None]] = None
        self.on_track_change: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Position update timer
        self._position_timer: Optional[threading.Thread] = None
        self._stop_position_updates = threading.Event()

        # Normalization settings
        self._normalize_audio = False
        self._target_loudness = -16.0  # LUFS

        # Initialize backend
        self._init_backend()

    def _init_backend(self):
        """Initialize the audio backend."""
        if self._backend == AudioBackend.AUTO:
            # Try VLC first (better streaming support)
            if HAS_VLC:
                self._init_vlc()
            elif HAS_WX_MEDIA and self.parent:
                self._init_wx_media()
        elif self._backend == AudioBackend.VLC and HAS_VLC:
            self._init_vlc()
        elif self._backend == AudioBackend.WMF and HAS_WX_MEDIA:
            self._init_wx_media()

    def _init_vlc(self):
        """Initialize VLC backend."""
        try:
            # VLC options for better streaming
            vlc_args = [
                "--no-video",
                "--network-caching=1000",
                "--file-caching=1000",
                "--live-caching=1000",
            ]
            self._vlc_instance = vlc.Instance(*vlc_args)
            self._vlc_player = self._vlc_instance.media_player_new()

            # Set up event manager
            events = self._vlc_player.event_manager()
            events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_vlc_end)
            events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_vlc_error)

        except Exception:
            self._vlc_instance = None
            self._vlc_player = None

    def _init_wx_media(self):
        """Initialize wxPython MediaCtrl backend."""
        if not self.parent:
            return

        try:
            self._wx_media = wx.media.MediaCtrl(
                self.parent, style=wx.SIMPLE_BORDER, szBackend=wx.media.MEDIABACKEND_WMP10
            )
            self._wx_media.Hide()
        except Exception:
            self._wx_media = None

    def _on_vlc_end(self, event):
        """Handle VLC end of track event."""
        if self._auto_advance and self._queue_index < len(self._queue) - 1:
            self._queue_index += 1
            self.play(self._queue[self._queue_index])
        else:
            self._set_state(PlayerState.STOPPED)

    def _on_vlc_error(self, event):
        """Handle VLC error event."""
        self._set_state(PlayerState.ERROR)
        if self.on_error:
            self.on_error("Playback error occurred")

    def _on_sleep_timer(self):
        """Handle sleep timer completion."""
        self.stop()

    def _set_state(self, state: PlayerState):
        """Set player state and notify."""
        self._state = state
        self._info.state = state
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception:
                pass

    @property
    def backend_name(self) -> str:
        """Get the name of the active backend."""
        if self._vlc_player:
            return "VLC"
        elif self._wx_media:
            return "Windows Media Foundation"
        return "None"

    @property
    def is_available(self) -> bool:
        """Check if any backend is available."""
        return self._vlc_player is not None or self._wx_media is not None

    @property
    def state(self) -> PlayerState:
        """Get current player state."""
        return self._state

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """Check if paused."""
        return self._state == PlayerState.PAUSED

    def play(self, url_or_path: str, title: str = "") -> bool:
        """
        Play a URL or local file.

        Args:
            url_or_path: URL or local file path
            title: Optional title for display

        Returns:
            True if playback started successfully
        """
        self._info.url = url_or_path
        self._info.title = title or os.path.basename(url_or_path)

        self._set_state(PlayerState.LOADING)

        try:
            if self._vlc_player:
                return self._play_vlc(url_or_path)
            elif self._wx_media:
                return self._play_wx(url_or_path)
            else:
                self._set_state(PlayerState.ERROR)
                return False
        except Exception as e:
            self._set_state(PlayerState.ERROR)
            if self.on_error:
                self.on_error(str(e))
            return False

    def _play_vlc(self, url_or_path: str) -> bool:
        """Play using VLC backend."""
        media = self._vlc_instance.media_new(url_or_path)  # type: ignore[union-attr]
        self._vlc_player.set_media(media)  # type: ignore[union-attr]

        result = self._vlc_player.play()  # type: ignore[union-attr]

        if result == 0:
            self._set_state(PlayerState.PLAYING)
            self._start_position_updates()

            if self.on_track_change:
                self.on_track_change(self._info.title)
            return True

        self._set_state(PlayerState.ERROR)
        return False

    def _play_wx(self, url_or_path: str) -> bool:
        """Play using wxPython MediaCtrl."""
        if self._wx_media.Load(url_or_path):  # type: ignore[union-attr]
            self._wx_media.Play()  # type: ignore[union-attr]
            self._set_state(PlayerState.PLAYING)
            self._start_position_updates()

            if self.on_track_change:
                self.on_track_change(self._info.title)
            return True

        self._set_state(PlayerState.ERROR)
        return False

    def pause(self):
        """Pause playback."""
        if self._state != PlayerState.PLAYING:
            return

        if self._vlc_player:
            self._vlc_player.pause()
        elif self._wx_media:
            self._wx_media.Pause()

        self._set_state(PlayerState.PAUSED)

    def resume(self):
        """Resume playback."""
        if self._state != PlayerState.PAUSED:
            return

        if self._vlc_player:
            self._vlc_player.play()
        elif self._wx_media:
            self._wx_media.Play()

        self._set_state(PlayerState.PLAYING)

    def toggle_pause(self):
        """Toggle between play and pause."""
        if self._state == PlayerState.PLAYING:
            self.pause()
        elif self._state == PlayerState.PAUSED:
            self.resume()

    def stop(self):
        """Stop playback."""
        if self._vlc_player:
            self._vlc_player.stop()
        elif self._wx_media:
            self._wx_media.Stop()

        self._stop_position_updates.set()
        self._set_state(PlayerState.STOPPED)
        self._info.position = 0
        self._info.duration = 0

    def seek(self, position: float):
        """
        Seek to position in seconds.

        Args:
            position: Position in seconds
        """
        if self._state not in [PlayerState.PLAYING, PlayerState.PAUSED]:
            return

        if self._vlc_player:
            self._vlc_player.set_time(int(position * 1000))
        elif self._wx_media:
            self._wx_media.Seek(int(position * 1000))

        self._info.position = position

    def seek_relative(self, offset: float):
        """
        Seek relative to current position.

        Args:
            offset: Offset in seconds (positive or negative)
        """
        new_pos = max(0, self._info.position + offset)
        if self._info.duration > 0:
            new_pos = min(new_pos, self._info.duration)
        self.seek(new_pos)

    def skip_forward(self, seconds: int = 30):
        """Skip forward by seconds."""
        self.seek_relative(seconds)

    def skip_backward(self, seconds: int = 10):
        """Skip backward by seconds."""
        self.seek_relative(-seconds)

    def set_volume(self, volume: float):
        """
        Set volume.

        Args:
            volume: Volume level 0.0 to 1.0
        """
        volume = max(0.0, min(1.0, volume))
        self._info.volume = volume

        if self._vlc_player:
            self._vlc_player.audio_set_volume(int(volume * 100))
        elif self._wx_media:
            self._wx_media.SetVolume(volume)

    def get_volume(self) -> float:
        """Get current volume (0.0 to 1.0)."""
        return self._info.volume

    def mute(self):
        """Mute audio."""
        if self._vlc_player:
            self._vlc_player.audio_set_mute(True)
        elif self._wx_media:
            self._wx_media.SetVolume(0.0)
        self._info.is_muted = True

    def unmute(self):
        """Unmute audio."""
        if self._vlc_player:
            self._vlc_player.audio_set_mute(False)
        elif self._wx_media:
            self._wx_media.SetVolume(self._info.volume)
        self._info.is_muted = False

    def toggle_mute(self):
        """Toggle mute state."""
        if self._info.is_muted:
            self.unmute()
        else:
            self.mute()

    def set_speed(self, speed: float):
        """
        Set playback speed.

        Args:
            speed: Playback speed (0.5 to 2.0)
        """
        speed = max(0.5, min(2.0, speed))
        self._info.speed = speed

        if self._vlc_player:
            self._vlc_player.set_rate(speed)
        # Note: wxMediaCtrl doesn't support speed control

    def get_speed(self) -> float:
        """Get current playback speed."""
        return self._info.speed

    def get_position(self) -> float:
        """Get current position in seconds."""
        if self._vlc_player:
            pos = self._vlc_player.get_time()
            return pos / 1000.0 if pos >= 0 else 0
        elif self._wx_media:
            return self._wx_media.Tell() / 1000.0
        return 0

    def get_duration(self) -> float:
        """Get total duration in seconds."""
        if self._vlc_player:
            length = self._vlc_player.get_length()
            return length / 1000.0 if length >= 0 else 0
        elif self._wx_media:
            return self._wx_media.Length() / 1000.0
        return 0

    def get_info(self) -> PlaybackInfo:
        """Get current playback info."""
        self._info.position = self.get_position()
        self._info.duration = self.get_duration()
        return self._info

    # Queue Management (for gapless playback)

    def set_queue(self, urls: List[str]):
        """Set the playback queue."""
        self._queue = urls.copy()
        self._queue_index = 0

    def add_to_queue(self, url: str):
        """Add a URL to the queue."""
        self._queue.append(url)

    def clear_queue(self):
        """Clear the playback queue."""
        self._queue.clear()
        self._queue_index = 0

    def play_next(self):
        """Play next item in queue."""
        if self._queue_index < len(self._queue) - 1:
            self._queue_index += 1
            self.play(self._queue[self._queue_index])

    def play_previous(self):
        """Play previous item in queue."""
        if self._queue_index > 0:
            self._queue_index -= 1
            self.play(self._queue[self._queue_index])

    # Sleep Timer

    def set_sleep_timer(self, minutes: int):
        """Set sleep timer in minutes."""
        if minutes > 0:
            self.sleep_timer.start(minutes)
        else:
            self.sleep_timer.stop()

    def cancel_sleep_timer(self):
        """Cancel the sleep timer."""
        self.sleep_timer.stop()

    # Audio Normalization

    def set_normalization(self, enabled: bool, target_loudness: float = -16.0):
        """
        Enable or disable audio normalization.

        Args:
            enabled: Whether to enable normalization
            target_loudness: Target loudness in LUFS
        """
        self._normalize_audio = enabled
        self._target_loudness = target_loudness
        # Note: Full implementation would require audio analysis

    # Position Updates

    def _start_position_updates(self):
        """Start position update thread."""
        self._stop_position_updates.clear()

        self._position_timer = threading.Thread(
            target=self._position_update_loop, daemon=True, name="PositionUpdater"
        )
        self._position_timer.start()

    def _position_update_loop(self):
        """Position update thread loop."""
        while not self._stop_position_updates.is_set():
            if self._state == PlayerState.PLAYING:
                pos = self.get_position()
                dur = self.get_duration()
                self._info.position = pos
                self._info.duration = dur

                if self.on_position_update:
                    try:
                        self.on_position_update(pos, dur)
                    except Exception:
                        pass

            time.sleep(0.5)

    # Cleanup

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.sleep_timer.stop()

        if self._vlc_player:
            self._vlc_player.release()
        if self._vlc_instance:
            self._vlc_instance.release()
