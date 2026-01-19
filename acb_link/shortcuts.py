"""
ACB Link - Keyboard Shortcuts Configuration Module
Configurable keyboard shortcuts with persistence and conflict detection.
"""

import json
import os
from typing import Dict, Optional, Callable, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ShortcutCategory(Enum):
    """Categories for organizing shortcuts."""
    PLAYBACK = "playback"
    NAVIGATION = "navigation"
    STREAMS = "streams"
    GENERAL = "general"
    RECORDING = "recording"
    VOLUME = "volume"


@dataclass
class Shortcut:
    """Represents a keyboard shortcut."""
    id: str
    name: str
    description: str
    category: ShortcutCategory
    default_key: str
    current_key: str = ""
    is_global: bool = False  # System-wide hotkey
    enabled: bool = True
    
    def __post_init__(self):
        if not self.current_key:
            self.current_key = self.default_key


# Default shortcuts configuration
DEFAULT_SHORTCUTS: Dict[str, Dict[str, Any]] = {
    # Playback
    "play_pause": {
        "name": "Play/Pause",
        "description": "Toggle playback",
        "category": "playback",
        "default_key": "Space",
    },
    "stop": {
        "name": "Stop",
        "description": "Stop playback",
        "category": "playback",
        "default_key": "Ctrl+Shift+S",
    },
    "skip_back": {
        "name": "Skip Backward",
        "description": "Skip backward",
        "category": "playback",
        "default_key": "Ctrl+Left",
    },
    "skip_forward": {
        "name": "Skip Forward",
        "description": "Skip forward",
        "category": "playback",
        "default_key": "Ctrl+Right",
    },
    
    # Volume
    "volume_up": {
        "name": "Volume Up",
        "description": "Increase volume",
        "category": "volume",
        "default_key": "Ctrl+Up",
    },
    "volume_down": {
        "name": "Volume Down",
        "description": "Decrease volume",
        "category": "volume",
        "default_key": "Ctrl+Down",
    },
    "mute": {
        "name": "Mute/Unmute",
        "description": "Toggle mute",
        "category": "volume",
        "default_key": "Ctrl+M",
    },
    
    # Recording
    "record": {
        "name": "Record",
        "description": "Start/stop recording",
        "category": "recording",
        "default_key": "Ctrl+R",
    },
    "schedule_recording": {
        "name": "Schedule Recording",
        "description": "Open scheduled recording dialog",
        "category": "recording",
        "default_key": "Ctrl+Shift+R",
    },
    
    # Navigation
    "tab_home": {
        "name": "Home Tab",
        "description": "Go to Home tab",
        "category": "navigation",
        "default_key": "Ctrl+1",
    },
    "tab_streams": {
        "name": "Streams Tab",
        "description": "Go to Streams tab",
        "category": "navigation",
        "default_key": "Ctrl+2",
    },
    "tab_podcasts": {
        "name": "Podcasts Tab",
        "description": "Go to Podcasts tab",
        "category": "navigation",
        "default_key": "Ctrl+3",
    },
    "tab_favorites": {
        "name": "Favorites Tab",
        "description": "Go to Favorites tab",
        "category": "navigation",
        "default_key": "Ctrl+4",
    },
    "tab_playlists": {
        "name": "Playlists Tab",
        "description": "Go to Playlists tab",
        "category": "navigation",
        "default_key": "Ctrl+5",
    },
    "tab_search": {
        "name": "Search Tab",
        "description": "Go to Search tab",
        "category": "navigation",
        "default_key": "Ctrl+6",
    },
    "tab_calendar": {
        "name": "Calendar Tab",
        "description": "Go to Calendar tab",
        "category": "navigation",
        "default_key": "Ctrl+7",
    },
    "global_search": {
        "name": "Global Search",
        "description": "Focus search box",
        "category": "navigation",
        "default_key": "Ctrl+F",
    },
    
    # General
    "settings": {
        "name": "Settings",
        "description": "Open settings dialog",
        "category": "general",
        "default_key": "Ctrl+,",
    },
    "open_browser": {
        "name": "Open in Browser",
        "description": "Open current content in browser",
        "category": "general",
        "default_key": "Ctrl+B",
    },
    "user_guide": {
        "name": "User Guide",
        "description": "Open user guide",
        "category": "general",
        "default_key": "F1",
    },
    "shortcuts_help": {
        "name": "Keyboard Shortcuts",
        "description": "Show keyboard shortcuts",
        "category": "general",
        "default_key": "Ctrl+/",
    },
    "exit": {
        "name": "Exit",
        "description": "Exit application",
        "category": "general",
        "default_key": "Alt+F4",
    },
    "voice_control": {
        "name": "Voice Control",
        "description": "Toggle voice control",
        "category": "general",
        "default_key": "Ctrl+Shift+V",
    },
    "add_favorite": {
        "name": "Add to Favorites",
        "description": "Add current item to favorites",
        "category": "general",
        "default_key": "Ctrl+D",
    },
    "add_to_playlist": {
        "name": "Add to Playlist",
        "description": "Add current item to playlist",
        "category": "general",
        "default_key": "Ctrl+Shift+P",
    },
    "sleep_timer": {
        "name": "Sleep Timer",
        "description": "Set sleep timer",
        "category": "general",
        "default_key": "Ctrl+T",
    },
    
    # Stream shortcuts (1-10)
    "stream_1": {
        "name": "Play Stream 1",
        "description": "Play ACB Media 1",
        "category": "streams",
        "default_key": "Alt+1",
    },
    "stream_2": {
        "name": "Play Stream 2",
        "description": "Play ACB Media 2",
        "category": "streams",
        "default_key": "Alt+2",
    },
    "stream_3": {
        "name": "Play Stream 3",
        "description": "Play ACB Media 3",
        "category": "streams",
        "default_key": "Alt+3",
    },
    "stream_4": {
        "name": "Play Stream 4",
        "description": "Play ACB Media 4",
        "category": "streams",
        "default_key": "Alt+4",
    },
    "stream_5": {
        "name": "Play Stream 5",
        "description": "Play ACB Media 5",
        "category": "streams",
        "default_key": "Alt+5",
    },
    "stream_6": {
        "name": "Play Stream 6",
        "description": "Play ACB Media 6",
        "category": "streams",
        "default_key": "Alt+6",
    },
    "stream_7": {
        "name": "Play Stream 7",
        "description": "Play Cafe 1",
        "category": "streams",
        "default_key": "Alt+7",
    },
    "stream_8": {
        "name": "Play Stream 8",
        "description": "Play Cafe 2",
        "category": "streams",
        "default_key": "Alt+8",
    },
    "stream_9": {
        "name": "Play Stream 9",
        "description": "Play Treasure Trove",
        "category": "streams",
        "default_key": "Alt+9",
    },
    "stream_10": {
        "name": "Play Stream 10",
        "description": "Play ACBS Main",
        "category": "streams",
        "default_key": "Alt+0",
    },
}


class ShortcutManager:
    """
    Manages keyboard shortcuts with persistence and conflict detection.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._default_config_path()
        self.shortcuts: Dict[str, Shortcut] = {}
        self.handlers: Dict[str, Callable] = {}
        self._load_defaults()
        self._load_config()
    
    def _default_config_path(self) -> str:
        """Get default config path."""
        home = os.path.expanduser("~")
        return os.path.join(home, ".acb_link", "shortcuts.json")
    
    def _load_defaults(self):
        """Load default shortcuts."""
        for shortcut_id, data in DEFAULT_SHORTCUTS.items():
            category = ShortcutCategory(data["category"])
            self.shortcuts[shortcut_id] = Shortcut(
                id=shortcut_id,
                name=data["name"],
                description=data["description"],
                category=category,
                default_key=data["default_key"],
                current_key=data["default_key"],
            )
    
    def _load_config(self):
        """Load saved shortcut configuration."""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            for shortcut_id, key in config.get("shortcuts", {}).items():
                if shortcut_id in self.shortcuts:
                    self.shortcuts[shortcut_id].current_key = key
                    
            for shortcut_id, enabled in config.get("enabled", {}).items():
                if shortcut_id in self.shortcuts:
                    self.shortcuts[shortcut_id].enabled = enabled
                    
        except Exception:
            pass
    
    def save(self):
        """Save shortcut configuration."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        config = {
            "shortcuts": {
                sid: s.current_key for sid, s in self.shortcuts.items()
            },
            "enabled": {
                sid: s.enabled for sid, s in self.shortcuts.items()
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_shortcut(self, shortcut_id: str) -> Optional[Shortcut]:
        """Get shortcut by ID."""
        return self.shortcuts.get(shortcut_id)
    
    def set_shortcut(self, shortcut_id: str, key: str) -> Tuple[bool, str]:
        """
        Set a shortcut key.
        
        Returns:
            Tuple of (success, error_message)
        """
        if shortcut_id not in self.shortcuts:
            return False, "Unknown shortcut ID"
        
        # Check for conflicts
        conflict = self.find_conflict(key, exclude_id=shortcut_id)
        if conflict:
            return False, f"Conflicts with '{conflict.name}'"
        
        self.shortcuts[shortcut_id].current_key = key
        return True, ""
    
    def find_conflict(self, key: str, exclude_id: Optional[str] = None) -> Optional[Shortcut]:
        """Find if a key conflicts with existing shortcuts."""
        key_lower = key.lower()
        for sid, shortcut in self.shortcuts.items():
            if sid == exclude_id:
                continue
            if shortcut.current_key.lower() == key_lower and shortcut.enabled:
                return shortcut
        return None
    
    def reset_shortcut(self, shortcut_id: str):
        """Reset a shortcut to its default."""
        if shortcut_id in self.shortcuts:
            self.shortcuts[shortcut_id].current_key = self.shortcuts[shortcut_id].default_key
    
    def reset_all(self):
        """Reset all shortcuts to defaults."""
        for shortcut in self.shortcuts.values():
            shortcut.current_key = shortcut.default_key
            shortcut.enabled = True
    
    def get_by_category(self, category: ShortcutCategory) -> List[Shortcut]:
        """Get all shortcuts in a category."""
        return [s for s in self.shortcuts.values() if s.category == category]
    
    def get_all_shortcuts(self) -> List[Shortcut]:
        """Get all shortcuts."""
        return list(self.shortcuts.values())
    
    def register_handler(self, shortcut_id: str, handler: Callable):
        """Register a handler for a shortcut."""
        self.handlers[shortcut_id] = handler
    
    def execute(self, shortcut_id: str) -> bool:
        """Execute a shortcut handler."""
        if shortcut_id not in self.handlers:
            return False
        
        shortcut = self.shortcuts.get(shortcut_id)
        if not shortcut or not shortcut.enabled:
            return False
        
        try:
            self.handlers[shortcut_id]()
            return True
        except Exception:
            return False
    
    def key_to_wx_accel(self, key: str) -> Tuple[int, int]:
        """
        Convert key string to wx accelerator flags and key code.
        
        Returns:
            Tuple of (flags, keycode)
        """
        import wx
        
        flags = 0
        key = key.strip()
        
        # Parse modifiers
        parts = key.split('+')
        keycode_str = parts[-1].strip()
        modifiers = [p.strip().lower() for p in parts[:-1]]
        
        if 'ctrl' in modifiers:
            flags |= wx.ACCEL_CTRL
        if 'alt' in modifiers:
            flags |= wx.ACCEL_ALT
        if 'shift' in modifiers:
            flags |= wx.ACCEL_SHIFT
        
        # Parse key code
        keycode_str = keycode_str.upper()
        
        # Special keys
        special_keys = {
            'SPACE': wx.WXK_SPACE,
            'ENTER': wx.WXK_RETURN,
            'RETURN': wx.WXK_RETURN,
            'TAB': wx.WXK_TAB,
            'ESCAPE': wx.WXK_ESCAPE,
            'ESC': wx.WXK_ESCAPE,
            'LEFT': wx.WXK_LEFT,
            'RIGHT': wx.WXK_RIGHT,
            'UP': wx.WXK_UP,
            'DOWN': wx.WXK_DOWN,
            'HOME': wx.WXK_HOME,
            'END': wx.WXK_END,
            'PAGEUP': wx.WXK_PAGEUP,
            'PAGEDOWN': wx.WXK_PAGEDOWN,
            'INSERT': wx.WXK_INSERT,
            'DELETE': wx.WXK_DELETE,
            'F1': wx.WXK_F1,
            'F2': wx.WXK_F2,
            'F3': wx.WXK_F3,
            'F4': wx.WXK_F4,
            'F5': wx.WXK_F5,
            'F6': wx.WXK_F6,
            'F7': wx.WXK_F7,
            'F8': wx.WXK_F8,
            'F9': wx.WXK_F9,
            'F10': wx.WXK_F10,
            'F11': wx.WXK_F11,
            'F12': wx.WXK_F12,
        }
        
        if keycode_str in special_keys:
            keycode = special_keys[keycode_str]
        elif len(keycode_str) == 1:
            keycode = ord(keycode_str)
        else:
            keycode = 0
        
        return flags, keycode
    
    def get_display_string(self, shortcut_id: str) -> str:
        """Get display string for a shortcut."""
        shortcut = self.shortcuts.get(shortcut_id)
        if not shortcut:
            return ""
        return shortcut.current_key if shortcut.enabled else "(disabled)"
    
    def export_shortcuts(self, filepath: str):
        """Export shortcuts to file."""
        data = {
            sid: {
                "name": s.name,
                "key": s.current_key,
                "enabled": s.enabled
            }
            for sid, s in self.shortcuts.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_shortcuts(self, filepath: str) -> Tuple[bool, str]:
        """Import shortcuts from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for sid, info in data.items():
                if sid in self.shortcuts:
                    self.shortcuts[sid].current_key = info.get("key", self.shortcuts[sid].default_key)
                    self.shortcuts[sid].enabled = info.get("enabled", True)
            
            return True, "Shortcuts imported successfully"
        except Exception as e:
            return False, f"Import failed: {str(e)}"


# Global shortcut manager instance
_shortcut_manager: Optional[ShortcutManager] = None


def get_shortcut_manager() -> ShortcutManager:
    """Get global shortcut manager instance."""
    global _shortcut_manager
    if _shortcut_manager is None:
        _shortcut_manager = ShortcutManager()
    return _shortcut_manager
