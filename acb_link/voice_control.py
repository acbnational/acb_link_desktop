"""
ACB Link - Voice Control
Speech recognition and voice command handling.

This module provides a fully extensible and configurable voice control system
for ACB Link. Users can customize wake words, command triggers, and TTS settings.
Developers can easily add custom voice commands through plugins or direct registration.

EXTENSIBILITY GUIDE
===================

1. ADDING A SIMPLE COMMAND
--------------------------
    from acb_link.voice_control import VoiceCommand, VoiceController
    
    # Create a command
    my_command = VoiceCommand(
        name="my_action",
        triggers=["do my action", "my action please", "execute my action"],
        action=lambda: print("Action executed!"),
        description="Performs my custom action",
        category="Custom"
    )
    
    # Register it
    voice_controller.register_command(my_command)

2. CREATING A COMMAND PLUGIN
----------------------------
    class MyVoicePlugin(VoiceCommandPlugin):
        @property
        def name(self) -> str:
            return "My Plugin"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        def get_commands(self) -> List[VoiceCommand]:
            return [
                VoiceCommand(
                    name="plugin_action",
                    triggers=["plugin action", "do plugin thing"],
                    action=self.do_action,
                    description="Plugin action",
                    category="Plugin"
                )
            ]
        
        def do_action(self):
            print("Plugin action executed!")
    
    # Register plugin
    voice_controller.register_plugin(MyVoicePlugin())

3. ADDING TRIGGERS TO EXISTING COMMANDS
---------------------------------------
    voice_controller.add_triggers("play", ["start music", "begin playback"])

4. USER CONFIGURATION
---------------------
    Users can configure voice control through Settings > Voice Control:
    - Enable/disable voice control
    - Set custom wake word (e.g., "hey link", "ok link", "computer")
    - Customize triggers for any command
    - Adjust TTS voice, rate, and volume
    - Enable/disable voice feedback

5. CUSTOM SPEECH RECOGNITION BACKEND
------------------------------------
    class MyRecognizer(SpeechRecognizerBackend):
        def recognize(self, audio) -> Optional[str]:
            # Your custom recognition logic
            return recognized_text
    
    voice_controller.set_recognizer_backend(MyRecognizer())

5. VOICE FEEDBACK CUSTOMIZATION
-------------------------------
    voice_controller.set_tts_voice("Microsoft Zira Desktop")
    voice_controller.set_tts_rate(150)  # Words per minute
    voice_controller.set_tts_volume(0.8)  # 0.0 to 1.0
"""

import threading
import queue
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Dict, List, Any, Type
from dataclasses import dataclass, field
from enum import Enum

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


class CommandCategory(Enum):
    """Categories for organizing voice commands."""
    PLAYBACK = "Playback"
    NAVIGATION = "Navigation"
    RECORDING = "Recording"
    SYSTEM = "System"
    STREAMS = "Streams"
    PODCASTS = "Podcasts"
    CUSTOM = "Custom"


@dataclass
class VoiceCommand:
    """
    Represents a voice command with its triggers and action.
    
    Attributes:
        name: Unique identifier for the command
        triggers: List of phrases that activate this command
        action: Callable to execute when command is recognized
        description: Human-readable description
        category: Category for grouping commands
        requires_argument: Whether command needs additional input
        enabled: Whether command is currently active
        priority: Higher priority commands match first (default 0)
        feedback: Optional custom feedback message
    """
    name: str
    triggers: List[str]
    action: Callable
    description: str = ""
    category: str = "Custom"
    requires_argument: bool = False
    enabled: bool = True
    priority: int = 0
    feedback: Optional[str] = None


class VoiceCommandPlugin(ABC):
    """
    Abstract base class for voice command plugins.
    
    Implement this class to create reusable voice command packages
    that can be easily shared and installed.
    
    Example:
        class WeatherPlugin(VoiceCommandPlugin):
            @property
            def name(self) -> str:
                return "Weather Commands"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            def get_commands(self) -> List[VoiceCommand]:
                return [
                    VoiceCommand(
                        name="weather",
                        triggers=["what's the weather", "weather report"],
                        action=self.get_weather,
                        description="Get current weather"
                    )
                ]
            
            def get_weather(self):
                # Implementation
                pass
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    def author(self) -> str:
        """Plugin author (optional)."""
        return "Unknown"
    
    @property
    def description(self) -> str:
        """Plugin description (optional)."""
        return ""
    
    @abstractmethod
    def get_commands(self) -> List[VoiceCommand]:
        """Return list of commands provided by this plugin."""
        pass
    
    def on_load(self, controller: 'VoiceController'):
        """Called when plugin is loaded. Override for initialization."""
        pass
    
    def on_unload(self, controller: 'VoiceController'):
        """Called when plugin is unloaded. Override for cleanup."""
        pass


class SpeechRecognizerBackend(ABC):
    """
    Abstract base class for speech recognition backends.
    
    Implement this to use alternative speech recognition services
    such as Whisper, Azure Speech, AWS Transcribe, etc.
    
    Example:
        class WhisperBackend(SpeechRecognizerBackend):
            def __init__(self, model="base"):
                import whisper
                self.model = whisper.load_model(model)
            
            @property
            def name(self) -> str:
                return "OpenAI Whisper"
            
            def recognize(self, audio_data) -> Optional[str]:
                result = self.model.transcribe(audio_data)
                return result["text"]
            
            def is_available(self) -> bool:
                return True
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name."""
        pass
    
    @abstractmethod
    def recognize(self, audio_data) -> Optional[str]:
        """
        Recognize speech from audio data.
        
        Args:
            audio_data: Audio data to recognize
            
        Returns:
            Recognized text or None if recognition failed
        """
        pass
    
    def is_available(self) -> bool:
        """Check if this backend is available."""
        return True


class GoogleSpeechBackend(SpeechRecognizerBackend):
    """Default Google Speech Recognition backend."""
    
    def __init__(self, recognizer: 'sr.Recognizer'):
        self.recognizer = recognizer
    
    @property
    def name(self) -> str:
        return "Google Speech Recognition"
    
    def recognize(self, audio_data) -> Optional[str]:
        try:
            return self.recognizer.recognize_google(audio_data).lower()
        except Exception:
            return None
    
    def is_available(self) -> bool:
        return HAS_SPEECH_RECOGNITION


class VoiceController:
    """
    Voice control system for ACB Link.
    Provides hands-free operation through speech recognition.
    
    This class is designed to be fully extensible and configurable:
    - Register custom commands via register_command()
    - Load command plugins via register_plugin()
    - Add triggers to existing commands via add_triggers()
    - Use custom recognition backends via set_recognizer_backend()
    - Customize TTS via set_tts_*() methods
    - Configure wake word via set_wake_word()
    - Apply user settings via apply_settings()
    - Save/load command configurations via save_config()/load_config()
    
    Attributes:
        commands: Dictionary of registered commands
        plugins: Dictionary of loaded plugins
        is_listening: Whether currently listening for commands
        is_enabled: Whether voice control is enabled
        wake_word: The phrase that activates voice control
        wake_word_enabled: Whether wake word is required
    """
    
    # Default triggers for all built-in commands (for reset functionality)
    DEFAULT_TRIGGERS = {
        "play": ["play", "start", "resume", "continue"],
        "pause": ["pause", "wait", "hold"],
        "stop": ["stop", "end", "halt"],
        "volume_up": ["volume up", "louder", "increase volume", "turn it up"],
        "volume_down": ["volume down", "quieter", "decrease volume", "turn it down", "softer"],
        "mute": ["mute", "silence", "quiet"],
        "unmute": ["unmute", "sound on"],
        "skip_forward": ["skip forward", "skip ahead", "fast forward", "next"],
        "skip_back": ["skip back", "skip backward", "rewind", "go back"],
        "go_home": ["go home", "home tab", "show home", "open home"],
        "go_streams": ["go to streams", "streams tab", "show streams", "open streams"],
        "go_podcasts": ["go to podcasts", "podcasts tab", "show podcasts", "open podcasts"],
        "go_affiliates": ["go to affiliates", "affiliates tab", "show affiliates"],
        "go_resources": ["go to resources", "resources tab", "show resources"],
        "start_recording": ["start recording", "record", "begin recording", "record stream"],
        "stop_recording": ["stop recording", "end recording", "finish recording"],
        "open_settings": ["open settings", "settings", "preferences", "options"],
        "what_playing": ["what's playing", "what is playing", "now playing", "current stream"],
        "help": ["help", "what can i say", "voice commands", "list commands"],
        "stop_listening": ["stop listening", "voice off", "disable voice", "goodbye"],
    }
    
    def __init__(self, on_command: Optional[Callable[[str, str], None]] = None):
        """
        Initialize voice controller.
        
        Args:
            on_command: Callback when command is recognized (command_name, full_text)
        """
        self.on_command = on_command
        self.is_listening = False
        self.is_enabled = False
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._command_queue: queue.Queue = queue.Queue()
        
        # Wake word configuration
        self.wake_word = "hey link"
        self.wake_word_enabled = True
        self.wake_word_active = False  # True when wake word detected
        self.wake_word_timeout = 10.0  # Seconds to listen after wake word
        self._wake_word_timer: Optional[threading.Timer] = None
        
        # Voice feedback settings
        self.voice_feedback = True
        self.command_confirmation = True
        
        # Plugins
        self.plugins: Dict[str, VoiceCommandPlugin] = {}
        
        # Custom command handlers for extensibility
        self._pre_command_hooks: List[Callable[[str, str], bool]] = []
        self._post_command_hooks: List[Callable[[str, str, bool], None]] = []
        
        # Speech recognition
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
            self.microphone: Optional[sr.Microphone] = None
            self._recognizer_backend: SpeechRecognizerBackend = GoogleSpeechBackend(self.recognizer)
        else:
            self.recognizer = None
            self.microphone = None
            self._recognizer_backend = None
        
        # Text-to-speech
        self.tts_engine = None
        if HAS_TTS:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_tts()
            except Exception:
                pass
        
        # Command registry
        self.commands: Dict[str, VoiceCommand] = {}
        self._register_default_commands()
    
    def set_wake_word(self, wake_word: str, enabled: bool = True):
        """
        Set the wake word phrase.
        
        Args:
            wake_word: The phrase to listen for (e.g., "hey link", "ok computer")
            enabled: Whether wake word is required before commands
        """
        self.wake_word = wake_word.lower().strip()
        self.wake_word_enabled = enabled
    
    def apply_settings(self, voice_settings):
        """
        Apply voice settings from the application settings.
        
        Args:
            voice_settings: VoiceSettings dataclass instance
        """
        from .settings import VoiceSettings
        if not isinstance(voice_settings, VoiceSettings):
            return
        
        # Wake word
        self.set_wake_word(voice_settings.wake_word, voice_settings.wake_word_enabled)
        
        # Voice feedback
        self.voice_feedback = voice_settings.voice_feedback
        self.command_confirmation = voice_settings.command_confirmation
        
        # TTS settings
        if voice_settings.tts_enabled and self.tts_engine:
            self.set_tts_rate(voice_settings.tts_rate)
            self.set_tts_volume(voice_settings.tts_volume)
            if voice_settings.tts_voice:
                self.set_tts_voice(voice_settings.tts_voice)
        
        # Custom triggers
        if voice_settings.custom_triggers:
            for cmd_name, triggers in voice_settings.custom_triggers.items():
                if cmd_name in self.commands and triggers:
                    self.commands[cmd_name].triggers = list(triggers)
    
    def reset_triggers(self, command_name: Optional[str] = None):
        """
        Reset triggers to defaults.
        
        Args:
            command_name: Specific command to reset, or None for all
        """
        if command_name:
            if command_name in self.DEFAULT_TRIGGERS:
                if command_name in self.commands:
                    self.commands[command_name].triggers = list(self.DEFAULT_TRIGGERS[command_name])
        else:
            for name, triggers in self.DEFAULT_TRIGGERS.items():
                if name in self.commands:
                    self.commands[name].triggers = list(triggers)
    
    def get_default_triggers(self, command_name: str) -> List[str]:
        """Get the default triggers for a command."""
        return list(self.DEFAULT_TRIGGERS.get(command_name, []))
    
    def _configure_tts(self):
        """Configure text-to-speech engine."""
        if not self.tts_engine:
            return
        
        # Set properties
        self.tts_engine.setProperty('rate', 175)  # Speed
        self.tts_engine.setProperty('volume', 0.9)  # Volume
        
        # Try to use a clear voice
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
    
    def _register_default_commands(self):
        """Register built-in voice commands."""
        # Playback commands
        self.register_command(VoiceCommand(
            name="play",
            triggers=["play", "start", "resume", "continue"],
            action=lambda: None,  # Will be connected to actual action
            description="Start or resume playback",
            category=CommandCategory.PLAYBACK.value,
            priority=10
        ))
        
        self.register_command(VoiceCommand(
            name="pause",
            triggers=["pause", "wait", "hold"],
            action=lambda: None,
            description="Pause playback",
            category=CommandCategory.PLAYBACK.value,
            priority=10
        ))
        
        self.register_command(VoiceCommand(
            name="stop",
            triggers=["stop", "end", "halt"],
            action=lambda: None,
            description="Stop playback",
            category=CommandCategory.PLAYBACK.value,
            priority=10
        ))
        
        self.register_command(VoiceCommand(
            name="volume_up",
            triggers=["volume up", "louder", "increase volume", "turn it up"],
            action=lambda: None,
            description="Increase volume",
            category=CommandCategory.PLAYBACK.value
        ))
        
        self.register_command(VoiceCommand(
            name="volume_down",
            triggers=["volume down", "quieter", "decrease volume", "turn it down", "softer"],
            action=lambda: None,
            description="Decrease volume",
            category=CommandCategory.PLAYBACK.value
        ))
        
        self.register_command(VoiceCommand(
            name="mute",
            triggers=["mute", "silence", "quiet"],
            action=lambda: None,
            description="Mute audio",
            category=CommandCategory.PLAYBACK.value
        ))
        
        self.register_command(VoiceCommand(
            name="unmute",
            triggers=["unmute", "sound on"],
            action=lambda: None,
            description="Unmute audio",
            category=CommandCategory.PLAYBACK.value
        ))
        
        # Navigation commands
        self.register_command(VoiceCommand(
            name="skip_forward",
            triggers=["skip forward", "skip ahead", "fast forward", "next"],
            action=lambda: None,
            description="Skip forward",
            category=CommandCategory.NAVIGATION.value
        ))
        
        self.register_command(VoiceCommand(
            name="skip_back",
            triggers=["skip back", "skip backward", "rewind", "go back"],
            action=lambda: None,
            description="Skip backward",
            category=CommandCategory.NAVIGATION.value
        ))
        
        # Tab navigation
        self.register_command(VoiceCommand(
            name="go_home",
            triggers=["go home", "home tab", "show home", "open home"],
            action=lambda: None,
            description="Go to Home tab",
            category=CommandCategory.NAVIGATION.value
        ))
        
        self.register_command(VoiceCommand(
            name="go_streams",
            triggers=["go to streams", "streams tab", "show streams", "open streams"],
            action=lambda: None,
            description="Go to Streams tab",
            category=CommandCategory.NAVIGATION.value
        ))
        
        self.register_command(VoiceCommand(
            name="go_podcasts",
            triggers=["go to podcasts", "podcasts tab", "show podcasts", "open podcasts"],
            action=lambda: None,
            description="Go to Podcasts tab",
            category=CommandCategory.NAVIGATION.value
        ))
        
        self.register_command(VoiceCommand(
            name="go_affiliates",
            triggers=["go to affiliates", "affiliates tab", "show affiliates"],
            action=lambda: None,
            description="Go to Affiliates tab",
            category=CommandCategory.NAVIGATION.value
        ))
        
        self.register_command(VoiceCommand(
            name="go_resources",
            triggers=["go to resources", "resources tab", "show resources"],
            action=lambda: None,
            description="Go to Resources tab",
            category=CommandCategory.NAVIGATION.value
        ))
        
        # Stream commands
        for i in range(1, 11):
            self.register_command(VoiceCommand(
                name=f"play_stream_{i}",
                triggers=[
                    f"play stream {i}",
                    f"stream {i}",
                    f"play acb media {i}",
                    f"acb media {i}",
                    f"play channel {i}",
                    f"channel {i}"
                ],
                action=lambda: None,
                description=f"Play ACB Media {i}",
                category=CommandCategory.STREAMS.value
            ))
        
        # Recording
        self.register_command(VoiceCommand(
            name="start_recording",
            triggers=["start recording", "record", "begin recording", "record stream"],
            action=lambda: None,
            description="Start recording",
            category=CommandCategory.RECORDING.value
        ))
        
        self.register_command(VoiceCommand(
            name="stop_recording",
            triggers=["stop recording", "end recording", "finish recording"],
            action=lambda: None,
            description="Stop recording",
            category=CommandCategory.RECORDING.value
        ))
        
        # System commands
        self.register_command(VoiceCommand(
            name="open_settings",
            triggers=["open settings", "settings", "preferences", "options"],
            action=lambda: None,
            description="Open settings",
            category=CommandCategory.SYSTEM.value
        ))
        
        self.register_command(VoiceCommand(
            name="what_playing",
            triggers=["what's playing", "what is playing", "now playing", "current stream", "current song"],
            action=lambda: None,
            description="Announce what's playing",
            category=CommandCategory.SYSTEM.value
        ))
        
        self.register_command(VoiceCommand(
            name="help",
            triggers=["help", "what can i say", "voice commands", "list commands"],
            action=lambda: None,
            description="List available commands",
            category=CommandCategory.SYSTEM.value,
            priority=5
        ))
        
        self.register_command(VoiceCommand(
            name="stop_listening",
            triggers=["stop listening", "voice off", "disable voice", "goodbye"],
            action=lambda: None,
            description="Stop voice control",
            category=CommandCategory.SYSTEM.value,
            priority=100  # High priority to always catch
        ))
    
    def register_command(self, command: VoiceCommand):
        """
        Register a voice command.
        
        Args:
            command: VoiceCommand instance to register
        
        Example:
            controller.register_command(VoiceCommand(
                name="custom",
                triggers=["my command"],
                action=lambda: print("Custom!")
            ))
        """
        self.commands[command.name] = command
    
    def unregister_command(self, command_name: str) -> bool:
        """
        Unregister a voice command.
        
        Args:
            command_name: Name of command to remove
            
        Returns:
            True if command was removed, False if not found
        """
        if command_name in self.commands:
            del self.commands[command_name]
            return True
        return False
    
    def set_command_action(self, command_name: str, action: Callable):
        """Set the action for a registered command."""
        if command_name in self.commands:
            self.commands[command_name].action = action
    
    def enable_command(self, command_name: str, enabled: bool = True):
        """Enable or disable a command."""
        if command_name in self.commands:
            self.commands[command_name].enabled = enabled
    
    def add_triggers(self, command_name: str, triggers: List[str]) -> bool:
        """
        Add additional triggers to an existing command.
        
        Args:
            command_name: Name of command to modify
            triggers: List of new trigger phrases to add
            
        Returns:
            True if triggers were added, False if command not found
            
        Example:
            controller.add_triggers("play", ["start music", "begin playback"])
        """
        if command_name in self.commands:
            existing = set(self.commands[command_name].triggers)
            existing.update(triggers)
            self.commands[command_name].triggers = list(existing)
            return True
        return False
    
    def remove_triggers(self, command_name: str, triggers: List[str]) -> bool:
        """
        Remove triggers from an existing command.
        
        Args:
            command_name: Name of command to modify
            triggers: List of trigger phrases to remove
            
        Returns:
            True if command exists, False otherwise
        """
        if command_name in self.commands:
            current = self.commands[command_name].triggers
            self.commands[command_name].triggers = [
                t for t in current if t not in triggers
            ]
            return True
        return False
    
    # Plugin Management
    def register_plugin(self, plugin: VoiceCommandPlugin) -> bool:
        """
        Register a voice command plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if plugin was registered successfully
            
        Example:
            class MyPlugin(VoiceCommandPlugin):
                ...
            controller.register_plugin(MyPlugin())
        """
        try:
            # Check if already registered
            if plugin.name in self.plugins:
                return False
            
            # Call plugin's on_load
            plugin.on_load(self)
            
            # Register all commands from plugin
            for command in plugin.get_commands():
                self.register_command(command)
            
            # Store plugin
            self.plugins[plugin.name] = plugin
            return True
            
        except Exception as e:
            print(f"Failed to register plugin {plugin.name}: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a voice command plugin.
        
        Args:
            plugin_name: Name of plugin to remove
            
        Returns:
            True if plugin was removed successfully
        """
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Remove all commands from plugin
        for command in plugin.get_commands():
            self.unregister_command(command.name)
        
        # Call plugin's on_unload
        plugin.on_unload(self)
        
        # Remove plugin
        del self.plugins[plugin_name]
        return True
    
    def get_loaded_plugins(self) -> List[Dict[str, str]]:
        """Get information about loaded plugins."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "author": p.author,
                "description": p.description
            }
            for p in self.plugins.values()
        ]
    
    # Hook Management
    def add_pre_command_hook(self, hook: Callable[[str, str], bool]):
        """
        Add a hook that runs before command execution.
        
        The hook receives (command_name, recognized_text) and should
        return True to continue execution or False to cancel.
        
        Args:
            hook: Callable that returns bool
            
        Example:
            def my_hook(cmd_name, text):
                print(f"About to run: {cmd_name}")
                return True  # Continue execution
            controller.add_pre_command_hook(my_hook)
        """
        self._pre_command_hooks.append(hook)
    
    def add_post_command_hook(self, hook: Callable[[str, str, bool], None]):
        """
        Add a hook that runs after command execution.
        
        The hook receives (command_name, recognized_text, success).
        
        Args:
            hook: Callable for post-execution
            
        Example:
            def my_hook(cmd_name, text, success):
                print(f"Command {cmd_name} {'succeeded' if success else 'failed'}")
            controller.add_post_command_hook(my_hook)
        """
        self._post_command_hooks.append(hook)
    
    def remove_pre_command_hook(self, hook: Callable):
        """Remove a pre-command hook."""
        if hook in self._pre_command_hooks:
            self._pre_command_hooks.remove(hook)
    
    def remove_post_command_hook(self, hook: Callable):
        """Remove a post-command hook."""
        if hook in self._post_command_hooks:
            self._post_command_hooks.remove(hook)
    
    # Recognition Backend Management
    def set_recognizer_backend(self, backend: SpeechRecognizerBackend):
        """
        Set a custom speech recognition backend.
        
        Args:
            backend: SpeechRecognizerBackend implementation
            
        Example:
            class WhisperBackend(SpeechRecognizerBackend):
                ...
            controller.set_recognizer_backend(WhisperBackend())
        """
        if backend.is_available():
            self._recognizer_backend = backend
            return True
        return False
    
    def get_recognizer_backend(self) -> Optional[SpeechRecognizerBackend]:
        """Get current speech recognition backend."""
        return self._recognizer_backend
    
    # TTS Customization
    def set_tts_voice(self, voice_name: str) -> bool:
        """
        Set text-to-speech voice by name.
        
        Args:
            voice_name: Partial or full voice name to match
            
        Returns:
            True if voice was set successfully
        """
        if not self.tts_engine:
            return False
        
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if voice_name.lower() in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                return True
        return False
    
    def set_tts_rate(self, rate: int):
        """
        Set text-to-speech rate (words per minute).
        
        Args:
            rate: Speaking rate (typically 100-200)
        """
        if self.tts_engine:
            self.tts_engine.setProperty('rate', rate)
    
    def set_tts_volume(self, volume: float):
        """
        Set text-to-speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.tts_engine:
            self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available TTS voices."""
        if not self.tts_engine:
            return []
        
        voices = self.tts_engine.getProperty('voices')
        return [{"id": v.id, "name": v.name} for v in voices]
    
    # Configuration Persistence
    def save_config(self, path: Optional[str] = None) -> bool:
        """
        Save voice control configuration to file.
        
        Args:
            path: Path to save config (default: user data dir)
            
        Returns:
            True if saved successfully
        """
        if path is None:
            path = str(Path.home() / ".acb_link" / "voice_config.json")
        
        config = {
            "commands": {
                name: {
                    "enabled": cmd.enabled,
                    "triggers": cmd.triggers,
                    "priority": cmd.priority
                }
                for name, cmd in self.commands.items()
            },
            "tts": {
                "rate": self.tts_engine.getProperty('rate') if self.tts_engine else 175,
                "volume": self.tts_engine.getProperty('volume') if self.tts_engine else 0.9
            }
        }
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save voice config: {e}")
            return False
    
    def load_config(self, path: Optional[str] = None) -> bool:
        """
        Load voice control configuration from file.
        
        Args:
            path: Path to load config from (default: user data dir)
            
        Returns:
            True if loaded successfully
        """
        if path is None:
            path = str(Path.home() / ".acb_link" / "voice_config.json")
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            
            # Apply command settings
            for name, settings in config.get("commands", {}).items():
                if name in self.commands:
                    self.commands[name].enabled = settings.get("enabled", True)
                    self.commands[name].priority = settings.get("priority", 0)
                    if "triggers" in settings:
                        self.commands[name].triggers = settings["triggers"]
            
            # Apply TTS settings
            tts_config = config.get("tts", {})
            if self.tts_engine:
                self.tts_engine.setProperty('rate', tts_config.get("rate", 175))
                self.tts_engine.setProperty('volume', tts_config.get("volume", 0.9))
            
            return True
        except Exception as e:
            print(f"Failed to load voice config: {e}")
            return False
    
    # Command Query Methods
    def get_commands_by_category(self, category: str) -> List[VoiceCommand]:
        """Get all commands in a category."""
        return [cmd for cmd in self.commands.values() if cmd.category == category]
    
    def get_enabled_commands(self) -> List[VoiceCommand]:
        """Get all enabled commands."""
        return [cmd for cmd in self.commands.values() if cmd.enabled]
    
    def search_commands(self, query: str) -> List[VoiceCommand]:
        """Search commands by name, trigger, or description."""
        query = query.lower()
        results = []
        for cmd in self.commands.values():
            if (query in cmd.name.lower() or
                query in cmd.description.lower() or
                any(query in t.lower() for t in cmd.triggers)):
                results.append(cmd)
        return results
    
    def is_available(self) -> bool:
        """Check if voice control is available."""
        return HAS_SPEECH_RECOGNITION and self.recognizer is not None
    
    def start_listening(self) -> bool:
        """Start listening for voice commands."""
        if not self.is_available():
            return False
        
        if self.is_listening:
            return True
        
        self._stop_event.clear()
        self.is_listening = True
        self.is_enabled = True
        
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="VoiceControlListener"
        )
        self._listen_thread.start()
        
        self.speak("Voice control activated")
        return True
    
    def stop_listening(self):
        """Stop listening for voice commands."""
        if not self.is_listening:
            return
        
        self._stop_event.set()
        self.is_listening = False
        self.is_enabled = False
        
        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
            self._listen_thread = None
        
        self.speak("Voice control deactivated")
    
    def _listen_loop(self):
        """Main listening loop running in background thread."""
        if not HAS_SPEECH_RECOGNITION:
            return
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                while not self._stop_event.is_set():
                    try:
                        # Listen for audio
                        audio = self.recognizer.listen(
                            source,
                            timeout=1.0,
                            phrase_time_limit=5.0
                        )
                        
                        # Process in separate thread to not block listening
                        threading.Thread(
                            target=self._process_audio,
                            args=(audio,),
                            daemon=True
                        ).start()
                        
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"Listen error: {e}")
                        continue
                        
        except Exception as e:
            print(f"Microphone error: {e}")
            self.is_listening = False
    
    def _process_audio(self, audio):
        """Process recorded audio and recognize speech."""
        if not HAS_SPEECH_RECOGNITION:
            return
        
        try:
            # Try Google Speech Recognition (free, no API key needed)
            text = self.recognizer.recognize_google(audio).lower()
            self._handle_recognized_text(text)
            
        except sr.UnknownValueError:
            # Speech not understood
            pass
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
    
    def _reset_wake_word_timer(self):
        """Reset the wake word timeout timer."""
        if self._wake_word_timer:
            self._wake_word_timer.cancel()
        self._wake_word_timer = threading.Timer(
            self.wake_word_timeout,
            self._on_wake_word_timeout
        )
        self._wake_word_timer.daemon = True
        self._wake_word_timer.start()
    
    def _on_wake_word_timeout(self):
        """Called when wake word listening times out."""
        self.wake_word_active = False
        if self.voice_feedback:
            self.speak_async("Listening stopped")
    
    def _handle_recognized_text(self, text: str):
        """Handle recognized speech text."""
        # Check for wake word if enabled
        if self.wake_word_enabled and not self.wake_word_active:
            if self.wake_word.lower() in text:
                self.wake_word_active = True
                self._reset_wake_word_timer()
                if self.voice_feedback:
                    self.speak_async("Listening")
                # Check if command is in same utterance after wake word
                text_after_wake = text.split(self.wake_word.lower(), 1)[-1].strip()
                if not text_after_wake:
                    return  # Just wake word, wait for command
                text = text_after_wake
            else:
                return  # Wake word required but not detected
        
        # Reset wake word timer if active
        if self.wake_word_enabled and self.wake_word_active:
            self._reset_wake_word_timer()
        
        # Sort commands by priority (higher first) and find matching command
        sorted_commands = sorted(
            [c for c in self.commands.values() if c.enabled],
            key=lambda c: c.priority,
            reverse=True
        )
        
        matched_command = None
        for command in sorted_commands:
            for trigger in command.triggers:
                if trigger.lower() in text:
                    matched_command = command
                    break
            if matched_command:
                break
        
        if matched_command:
            # Run pre-command hooks
            for hook in self._pre_command_hooks:
                try:
                    if not hook(matched_command.name, text):
                        return  # Hook cancelled execution
                except Exception as e:
                    print(f"Pre-command hook error: {e}")
            
            # Execute command
            success = False
            try:
                if matched_command.name == "stop_listening":
                    self.stop_listening()
                    success = True
                elif matched_command.name == "help":
                    self._announce_commands()
                    success = True
                else:
                    matched_command.action()
                    success = True
                
                # Provide voice feedback if configured
                if matched_command.feedback and success:
                    self.speak_async(matched_command.feedback)
                    
                # Notify callback
                if self.on_command:
                    self.on_command(matched_command.name, text)
                    
            except Exception as e:
                print(f"Command error: {e}")
            
            # Run post-command hooks
            for hook in self._post_command_hooks:
                try:
                    hook(matched_command.name, text, success)
                except Exception as e:
                    print(f"Post-command hook error: {e}")
    
    def speak(self, text: str):
        """Speak text using text-to-speech."""
        if not self.tts_engine:
            return
        
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
    
    def speak_async(self, text: str):
        """Speak text asynchronously."""
        threading.Thread(
            target=self.speak,
            args=(text,),
            daemon=True
        ).start()
    
    def _announce_commands(self):
        """Announce available voice commands."""
        commands_text = "Available commands: "
        
        # Group commands by category
        categories: Dict[str, List[str]] = {}
        for cmd in self.get_enabled_commands():
            cat = cmd.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cmd.triggers[0] if cmd.triggers else cmd.name)
        
        # Build announcement
        for category, triggers in categories.items():
            if triggers:
                commands_text += f"{category}: {', '.join(triggers[:3])}. "
        
        self.speak(commands_text)
    
    def get_command_list(self) -> List[Dict[str, str]]:
        """Get list of all commands with descriptions."""
        return [
            {
                "name": cmd.name,
                "triggers": cmd.triggers,
                "description": cmd.description
            }
            for cmd in self.commands.values()
        ]


class VoiceControlManager:
    """
    Manager class that integrates voice control with the main application.
    """
    
    def __init__(self, main_frame):
        """
        Initialize voice control manager.
        
        Args:
            main_frame: Reference to the main application frame
        """
        self.main_frame = main_frame
        self.voice_controller = VoiceController(on_command=self._on_voice_command)
        
        # Connect commands to actions
        self._connect_commands()
    
    def _connect_commands(self):
        """Connect voice commands to application actions."""
        vc = self.voice_controller
        mf = self.main_frame
        
        # Playback controls
        vc.set_command_action("play", lambda: mf._on_play_pause(None))
        vc.set_command_action("pause", lambda: mf._on_play_pause(None))
        vc.set_command_action("stop", lambda: mf._on_stop(None))
        vc.set_command_action("volume_up", lambda: mf._on_volume_up(None))
        vc.set_command_action("volume_down", lambda: mf._on_volume_down(None))
        vc.set_command_action("mute", lambda: mf._on_mute(None))
        vc.set_command_action("unmute", lambda: mf._on_mute(None))
        vc.set_command_action("skip_forward", lambda: mf._on_skip_forward(None))
        vc.set_command_action("skip_back", lambda: mf._on_skip_back(None))
        
        # Tab navigation
        vc.set_command_action("go_home", lambda: mf.notebook.SetSelection(0))
        vc.set_command_action("go_streams", lambda: mf.notebook.SetSelection(1))
        vc.set_command_action("go_podcasts", lambda: mf.notebook.SetSelection(2))
        
        # Stream selection
        from .data import STREAMS
        stream_names = list(STREAMS.keys())
        for i in range(1, 11):
            if i <= len(stream_names):
                stream_name = stream_names[i - 1]
                vc.set_command_action(
                    f"play_stream_{i}",
                    lambda name=stream_name: mf._play_stream(name)
                )
        
        # Recording
        vc.set_command_action("start_recording", lambda: self._start_recording())
        vc.set_command_action("stop_recording", lambda: mf._stop_recording())
        
        # System
        vc.set_command_action("open_settings", lambda: mf._on_settings(None))
        vc.set_command_action("what_playing", lambda: self._announce_now_playing())
    
    def _start_recording(self):
        """Start recording current stream."""
        if self.main_frame.current_stream:
            self.main_frame._start_recording(self.main_frame.current_stream)
        else:
            self.voice_controller.speak("No stream is playing")
    
    def _announce_now_playing(self):
        """Announce what's currently playing."""
        if self.main_frame.current_stream:
            self.voice_controller.speak(f"Now playing {self.main_frame.current_stream}")
        else:
            self.voice_controller.speak("Nothing is currently playing")
    
    def _on_voice_command(self, command_name: str, full_text: str):
        """Handle voice command callback."""
        # Log the command
        if hasattr(self.main_frame, 'logger'):
            self.main_frame.logger.info(f"Voice command: {command_name} (text: {full_text})")
        
        # Update status
        if hasattr(self.main_frame, 'statusbar'):
            import wx
            wx.CallAfter(
                self.main_frame.statusbar.SetStatusText,
                f"Voice: {command_name}",
                0
            )
    
    def start(self) -> bool:
        """Start voice control."""
        return self.voice_controller.start_listening()
    
    def stop(self):
        """Stop voice control."""
        self.voice_controller.stop_listening()
    
    def is_active(self) -> bool:
        """Check if voice control is active."""
        return self.voice_controller.is_listening
    
    def toggle(self) -> bool:
        """Toggle voice control on/off."""
        if self.is_active():
            self.stop()
            return False
        else:
            return self.start()
