"""
Tests for voice control functionality including key feedback sounds.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from acb_link.voice_control import KeySoundPlayer, get_default_sounds_path


class TestKeySoundPlayer(unittest.TestCase):
    """Tests for the KeySoundPlayer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = KeySoundPlayer()

    def test_default_enabled_state(self):
        """Test that key sounds are enabled by default."""
        self.assertTrue(self.player.enabled)

    def test_enable_disable(self):
        """Test enabling and disabling key sounds."""
        self.player.enabled = False
        self.assertFalse(self.player.enabled)
        self.player.enabled = True
        self.assertTrue(self.player.enabled)

    def test_custom_sound_paths(self):
        """Test setting custom sound paths."""
        self.player.key_down_sound = "/path/to/custom_down.mp3"
        self.player.key_up_sound = "/path/to/custom_up.wav"
        
        self.assertEqual(self.player.key_down_sound, "/path/to/custom_down.mp3")
        self.assertEqual(self.player.key_up_sound, "/path/to/custom_up.wav")

    def test_empty_paths_default_to_empty(self):
        """Test that empty paths are stored correctly."""
        self.player.key_down_sound = ""
        self.player.key_up_sound = ""
        
        self.assertEqual(self.player.key_down_sound, "")
        self.assertEqual(self.player.key_up_sound, "")

    def test_apply_settings(self):
        """Test applying settings from VoiceSettings-like object."""
        mock_settings = MagicMock()
        mock_settings.key_sounds_enabled = False
        mock_settings.key_down_sound = "/custom/down.mp3"
        mock_settings.key_up_sound = "/custom/up.ogg"
        
        self.player.apply_settings(mock_settings)
        
        self.assertFalse(self.player.enabled)
        self.assertEqual(self.player.key_down_sound, "/custom/down.mp3")
        self.assertEqual(self.player.key_up_sound, "/custom/up.ogg")

    def test_apply_settings_handles_missing_attributes(self):
        """Test that apply_settings handles objects without all attributes."""
        mock_settings = MagicMock(spec=[])  # Empty spec means no attributes
        
        # Should not raise an exception
        self.player.apply_settings(mock_settings)
        
        # Should use defaults when attributes are missing
        self.assertTrue(self.player.enabled)

    def test_play_key_down_when_disabled(self):
        """Test that play_key_down does nothing when disabled."""
        self.player.enabled = False
        # Should not raise any exception
        self.player.play_key_down()

    def test_play_key_up_when_disabled(self):
        """Test that play_key_up does nothing when disabled."""
        self.player.enabled = False
        # Should not raise any exception
        self.player.play_key_up()


class TestDefaultSoundsPath(unittest.TestCase):
    """Tests for the default sounds path function."""

    def test_get_default_sounds_path_returns_path(self):
        """Test that get_default_sounds_path returns a Path object."""
        result = get_default_sounds_path()
        self.assertIsInstance(result, Path)

    def test_default_sounds_directory_exists(self):
        """Test that the default sounds directory exists."""
        sounds_path = get_default_sounds_path()
        # The sounds directory should exist in the project
        self.assertTrue(sounds_path.exists(), f"Sounds directory not found at {sounds_path}")

    def test_default_key_down_sound_exists(self):
        """Test that the default key_down.mp3 file exists."""
        sounds_path = get_default_sounds_path()
        key_down_file = sounds_path / "key_down.mp3"
        self.assertTrue(key_down_file.exists(), f"key_down.mp3 not found at {key_down_file}")

    def test_default_key_up_sound_exists(self):
        """Test that the default key_up.mp3 file exists."""
        sounds_path = get_default_sounds_path()
        key_up_file = sounds_path / "key_up.mp3"
        self.assertTrue(key_up_file.exists(), f"key_up.mp3 not found at {key_up_file}")


class TestVoiceSettingsIntegration(unittest.TestCase):
    """Tests for VoiceSettings integration with key sounds."""

    def test_voice_settings_has_key_sound_fields(self):
        """Test that VoiceSettings dataclass has key sound fields."""
        from acb_link.settings import VoiceSettings
        
        settings = VoiceSettings()
        
        # Check default values
        self.assertTrue(settings.key_sounds_enabled)
        self.assertEqual(settings.key_down_sound, "")
        self.assertEqual(settings.key_up_sound, "")

    def test_voice_settings_serialization(self):
        """Test that key sound settings are serialized correctly."""
        from acb_link.settings import VoiceSettings
        from dataclasses import asdict
        
        settings = VoiceSettings(
            key_sounds_enabled=False,
            key_down_sound="/path/to/down.mp3",
            key_up_sound="/path/to/up.wav"
        )
        
        data = asdict(settings)
        
        self.assertFalse(data["key_sounds_enabled"])
        self.assertEqual(data["key_down_sound"], "/path/to/down.mp3")
        self.assertEqual(data["key_up_sound"], "/path/to/up.wav")


if __name__ == "__main__":
    unittest.main()
