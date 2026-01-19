"""
ACB Link - Enhanced Voice Control Module
Wake word activation, continuous listening, and natural language processing.

This module provides comprehensive voice control with:
- Wake word detection using OpenWakeWord (free, open source)
- Fallback to speech recognition-based wake word detection
- Natural language processing for commands
- Text-to-speech feedback
"""

import threading
import numpy as np
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
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

# Try to import OpenWakeWord (free, open-source wake word detection)
try:
    import openwakeword  # type: ignore[import-untyped]
    from openwakeword.model import Model as OWWModel  # type: ignore[import-untyped]
    HAS_OPENWAKEWORD = True
except ImportError:
    HAS_OPENWAKEWORD = False

# Try to import PyAudio for audio streaming
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False


class VoiceState(Enum):
    """Voice control states."""
    DISABLED = "disabled"
    LISTENING_FOR_WAKE = "listening_for_wake"
    LISTENING_FOR_COMMAND = "listening_for_command"
    PROCESSING = "processing"
    SPEAKING = "speaking"


@dataclass
class NaturalLanguageQuery:
    """Parsed natural language query."""
    intent: str  # play, pause, search, navigate, etc.
    target: str  # stream name, podcast name, etc.
    parameters: Dict[str, Any]  # Additional parameters
    original_text: str
    confidence: float


class WakeWordDetector:
    """
    Detects wake word ("Hey ACB Link" or similar).
    Uses OpenWakeWord if available (free, open source), falls back to speech recognition.
    
    OpenWakeWord runs entirely locally with no API keys or costs.
    """
    
    WAKE_PHRASES = [
        "hey acb link",
        "acb link",
        "hey acb",
        "okay acb link",
        "hey a c b link",
        "a c b link"
    ]
    
    def __init__(self, on_wake_detected: Optional[Callable[[], None]] = None):
        self.on_wake_detected = on_wake_detected
        self._is_listening = False
        self._stop_event = threading.Event()
        self._listen_thread: Optional[threading.Thread] = None
        
        # OpenWakeWord setup
        self._oww_model = None
        self._audio_stream = None
        self._pyaudio_instance = None
        self._use_openwakeword = False
        
        # Try to initialize OpenWakeWord
        self._init_openwakeword()
        
        # Fallback to speech recognition
        if HAS_SPEECH_RECOGNITION and not self._use_openwakeword:
            self.recognizer = sr.Recognizer()
            # Adjust for faster response
            self.recognizer.pause_threshold = 0.5
            self.recognizer.phrase_threshold = 0.3
        else:
            self.recognizer = None
    
    def _init_openwakeword(self):
        """Initialize OpenWakeWord engine if available."""
        if not HAS_OPENWAKEWORD or not HAS_PYAUDIO:
            return
        
        try:
            # Download/load models on first use
            # OpenWakeWord comes with pre-trained models including "hey jarvis" 
            # which we can use as a base, or train custom "hey acb link"
            openwakeword.utils.download_models()
            
            # Load model - using "hey_jarvis" as similar wake word pattern
            # In production, a custom "hey_acb_link" model could be trained
            self._oww_model = OWWModel(
                wakeword_models=["hey_jarvis_v0.1"],
                inference_framework="onnx"
            )
            self._use_openwakeword = True
        except Exception:
            # OpenWakeWord not available, will use speech recognition fallback
            self._use_openwakeword = False
    
    @property
    def using_openwakeword(self) -> bool:
        """Check if OpenWakeWord is being used for wake word detection."""
        return self._use_openwakeword
    
    @property
    def detection_method(self) -> str:
        """Return the current wake word detection method."""
        if self._use_openwakeword:
            return "OpenWakeWord (local, free)"
        elif HAS_SPEECH_RECOGNITION:
            return "Speech Recognition (cloud-based)"
        else:
            return "None"
    
    def start(self):
        """Start listening for wake word."""
        if self._is_listening:
            return
        
        self._stop_event.clear()
        self._is_listening = True
        
        if self._use_openwakeword:
            self._listen_thread = threading.Thread(
                target=self._openwakeword_listen_loop,
                daemon=True,
                name="WakeWordDetector-OpenWakeWord"
            )
        elif HAS_SPEECH_RECOGNITION:
            self._listen_thread = threading.Thread(
                target=self._wake_listen_loop,
                daemon=True,
                name="WakeWordDetector-SpeechRec"
            )
        else:
            self._is_listening = False
            return
        
        self._listen_thread.start()
    
    def stop(self):
        """Stop listening for wake word."""
        self._stop_event.set()
        self._is_listening = False
        
        # Clean up audio resources
        if self._audio_stream:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        
        if self._pyaudio_instance:
            try:
                self._pyaudio_instance.terminate()
            except Exception:
                pass
            self._pyaudio_instance = None
        
        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
    
    def cleanup(self):
        """Clean up all resources."""
        self.stop()
        self._oww_model = None
    
    def _openwakeword_listen_loop(self):
        """Background loop using OpenWakeWord for wake word detection."""
        if not self._oww_model:
            return
        
        # Audio parameters for OpenWakeWord
        CHUNK = 1280  # OpenWakeWord expects 80ms of 16kHz audio
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        try:
            self._pyaudio_instance = pyaudio.PyAudio()
            self._audio_stream = self._pyaudio_instance.open(
                rate=RATE,
                channels=CHANNELS,
                format=FORMAT,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while not self._stop_event.is_set():
                try:
                    # Read audio chunk
                    audio_data = self._audio_stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Convert to numpy array
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Run prediction
                    prediction = self._oww_model.predict(audio_array)
                    
                    # Check for wake word activation (threshold of 0.5)
                    for model_name, score in prediction.items():
                        if score > 0.5:
                            if self.on_wake_detected:
                                self.on_wake_detected()
                            # Reset model state after detection
                            self._oww_model.reset()
                            break
                            
                except Exception:
                    continue
                    
        except Exception:
            # Fall back to speech recognition
            self._use_openwakeword = False
            if HAS_SPEECH_RECOGNITION:
                self._wake_listen_loop()
        finally:
            self._is_listening = False
    
    def _wake_listen_loop(self):
        """Background loop listening for wake word."""
        if not HAS_SPEECH_RECOGNITION:
            return
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)  # type: ignore[union-attr]
                
                while not self._stop_event.is_set():
                    try:
                        # Short listen for wake word
                        audio = self.recognizer.listen(  # type: ignore[union-attr]
                            source,
                            timeout=1.0,
                            phrase_time_limit=3.0
                        )
                        
                        # Check for wake word
                        text = self._recognize_audio(audio)
                        if text and self._is_wake_word(text):
                            if self.on_wake_detected:
                                self.on_wake_detected()
                            
                    except sr.WaitTimeoutError:
                        continue
                    except Exception:
                        continue
                        
        except Exception:
            self._is_listening = False
    
    def _recognize_audio(self, audio) -> Optional[str]:
        """Recognize audio to text."""
        try:
            text = self.recognizer.recognize_google(audio).lower()  # type: ignore[union-attr]
            return text
        except (sr.UnknownValueError, sr.RequestError):
            return None
    
    def _is_wake_word(self, text: str) -> bool:
        """Check if text contains wake word."""
        text = text.lower()
        for phrase in self.WAKE_PHRASES:
            if phrase in text:
                return True
        return False


class NaturalLanguageProcessor:
    """
    Processes natural language queries and extracts intent.
    """
    
    # Intent patterns
    PATTERNS = {
        'play': [
            r'play\s+(.+)',
            r'start\s+(.+)',
            r'listen\s+to\s+(.+)',
            r'tune\s+in\s+to\s+(.+)',
        ],
        'pause': [
            r'pause',
            r'stop\s+playing',
            r'hold',
        ],
        'stop': [
            r'stop',
            r'end',
            r'quit\s+playing',
        ],
        'search': [
            r'search\s+(?:for\s+)?(.+)',
            r'find\s+(.+)',
            r'look\s+for\s+(.+)',
        ],
        'navigate': [
            r'go\s+to\s+(.+)',
            r'open\s+(.+)',
            r'show\s+(?:me\s+)?(.+)',
        ],
        'volume': [
            r'(?:set\s+)?volume\s+(?:to\s+)?(\d+)',
            r'volume\s+(up|down)',
            r'(louder|quieter)',
            r'(mute|unmute)',
        ],
        'stream': [
            r'(?:play\s+)?(?:acb\s+)?(?:media\s+)?(?:stream\s+)?(\d+)',
            r'(?:play\s+)?channel\s+(\d+)',
        ],
        'record': [
            r'(?:start\s+)?record(?:ing)?',
            r'stop\s+record(?:ing)?',
        ],
        'settings': [
            r'(?:open\s+)?settings',
            r'preferences',
            r'options',
        ],
        'help': [
            r'help',
            r'what\s+can\s+(?:i|you)\s+(?:say|do)',
            r'commands',
        ],
        'status': [
            r"what(?:'s|\s+is)\s+playing",
            r'now\s+playing',
            r'current\s+(?:stream|song)',
        ],
    }
    
    # Entity extraction patterns
    STREAM_NAMES = {
        'media 1': 'ACB Media 1',
        'media 2': 'ACB Media 2',
        'media 3': 'ACB Media 3',
        'media 4': 'ACB Media 4',
        'media 5': 'ACB Media 5',
        'cafe': 'Cafe 1',
        'cafe 1': 'Cafe 1',
        'cafe 2': 'Cafe 2',
        'treasure trove': 'Treasure Trove',
        'main': 'ACBS Main',
    }
    
    def __init__(self):
        import re
        self._compiled_patterns = {}
        
        for intent, patterns in self.PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def process(self, text: str) -> NaturalLanguageQuery:
        """Process natural language text and extract intent."""
        text = text.strip().lower()
        
        # Try each intent pattern
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    target = match.group(1) if match.lastindex else ""
                    params = self._extract_parameters(intent, target, text)
                    
                    return NaturalLanguageQuery(
                        intent=intent,
                        target=target,
                        parameters=params,
                        original_text=text,
                        confidence=0.8 if match else 0.5
                    )
        
        # No match - return generic query
        return NaturalLanguageQuery(
            intent="unknown",
            target="",
            parameters={},
            original_text=text,
            confidence=0.3
        )
    
    def _extract_parameters(
        self, 
        intent: str, 
        target: str, 
        text: str
    ) -> Dict[str, Any]:
        """Extract additional parameters from query."""
        params = {}
        
        if intent == 'volume':
            # Extract volume level or direction
            if target.isdigit():
                params['level'] = int(target)
            elif target in ['up', 'louder']:
                params['direction'] = 'up'
            elif target in ['down', 'quieter']:
                params['direction'] = 'down'
            elif 'mute' in text:
                params['mute'] = 'mute' if 'unmute' not in text else 'unmute'
        
        elif intent == 'stream':
            # Extract stream number
            if target.isdigit():
                params['stream_number'] = int(target)
        
        elif intent == 'play':
            # Try to match stream name
            target_lower = target.lower()
            for key, name in self.STREAM_NAMES.items():
                if key in target_lower:
                    params['stream_name'] = name
                    break
        
        return params


class EnhancedVoiceController:
    """
    Enhanced voice control with wake word activation,
    continuous listening, and natural language processing.
    """
    
    def __init__(self, on_command: Optional[Callable[[str, Any], None]] = None):
        self.on_command = on_command
        self._state = VoiceState.DISABLED
        
        # Components
        self.wake_detector = WakeWordDetector(on_wake_detected=self._on_wake_word)
        self.nlp = NaturalLanguageProcessor()
        
        # Speech recognition
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
        
        # Text-to-speech
        if HAS_TTS:
            try:
                self.tts = pyttsx3.init()
                self._configure_tts()
            except Exception:
                self.tts = None
        else:
            self.tts = None
        
        # Threading
        self._command_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._command_timeout = 5.0  # seconds
        
        # Settings
        self.wake_word_enabled = True
        self.continuous_listening = False
        self.audio_feedback = True
        
        # Callbacks
        self.on_state_change: Optional[Callable[[VoiceState], None]] = None
        self.on_transcription: Optional[Callable[[str], None]] = None
    
    def _configure_tts(self):
        """Configure text-to-speech."""
        if self.tts:
            self.tts.setProperty('rate', 175)
            self.tts.setProperty('volume', 0.9)
    
    @property
    def state(self) -> VoiceState:
        """Get current state."""
        return self._state
    
    def _set_state(self, state: VoiceState):
        """Set state and notify."""
        self._state = state
        if self.on_state_change:
            self.on_state_change(state)
    
    def is_available(self) -> bool:
        """Check if voice control is available."""
        return HAS_SPEECH_RECOGNITION and self.recognizer is not None
    
    def start(self):
        """Start voice control."""
        if not self.is_available():
            return False
        
        self._stop_event.clear()
        
        if self.wake_word_enabled:
            self._set_state(VoiceState.LISTENING_FOR_WAKE)
            self.wake_detector.start()
            self.speak("Voice control ready. Say 'Hey ACB Link' to activate.")
        else:
            self._set_state(VoiceState.LISTENING_FOR_COMMAND)
            self._start_command_listening()
            self.speak("Voice control activated.")
        
        return True
    
    def stop(self):
        """Stop voice control."""
        self._stop_event.set()
        self.wake_detector.stop()
        self._set_state(VoiceState.DISABLED)
        self.speak("Voice control deactivated.")
    
    def _on_wake_word(self):
        """Handle wake word detection."""
        self._set_state(VoiceState.LISTENING_FOR_COMMAND)
        
        if self.audio_feedback:
            # Play a sound or speak
            self.speak_async("Yes?")
        
        self._start_command_listening()
    
    def _start_command_listening(self):
        """Start listening for a command."""
        if self._command_thread and self._command_thread.is_alive():
            return
        
        self._command_thread = threading.Thread(
            target=self._listen_for_command,
            daemon=True,
            name="CommandListener"
        )
        self._command_thread.start()
    
    def _listen_for_command(self):
        """Listen for a single command."""
        if not HAS_SPEECH_RECOGNITION:
            return
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)  # type: ignore[union-attr]
                
                # Listen for command
                audio = self.recognizer.listen(  # type: ignore[union-attr]
                    source,
                    timeout=self._command_timeout,
                    phrase_time_limit=10.0
                )
                
                self._set_state(VoiceState.PROCESSING)
                
                # Recognize
                try:
                    text = self.recognizer.recognize_google(audio)  # type: ignore[union-attr]
                    
                    if self.on_transcription:
                        self.on_transcription(text)
                    
                    self._process_command(text)
                    
                except sr.UnknownValueError:
                    self.speak("I didn't understand that. Please try again.")
                except sr.RequestError:
                    self.speak("Speech recognition service unavailable.")
                    
        except sr.WaitTimeoutError:
            # No speech detected
            pass
        except Exception:
            pass
        finally:
            # Return to wake word listening or stay in continuous mode
            if self.continuous_listening:
                self._set_state(VoiceState.LISTENING_FOR_COMMAND)
                self._start_command_listening()
            elif self.wake_word_enabled:
                self._set_state(VoiceState.LISTENING_FOR_WAKE)
            else:
                self._set_state(VoiceState.DISABLED)
    
    def _process_command(self, text: str):
        """Process recognized text as a command."""
        query = self.nlp.process(text)
        
        # Handle command
        if query.intent == 'help':
            self._speak_help()
        elif query.intent == 'unknown':
            self.speak("I'm not sure what you meant. Try saying 'help' for commands.")
        else:
            # Pass to handler
            if self.on_command:
                self.on_command(query.intent, query)
            
            # Feedback
            if self.audio_feedback:
                self._confirm_command(query)
    
    def _confirm_command(self, query: NaturalLanguageQuery):
        """Provide audio confirmation of command."""
        confirmations = {
            'play': "Playing.",
            'pause': "Paused.",
            'stop': "Stopped.",
            'volume': "Volume adjusted.",
            'search': f"Searching for {query.target}.",
            'navigate': f"Opening {query.target}.",
            'record': "Recording.",
            'settings': "Opening settings.",
            'status': None,  # Will be spoken separately
        }
        
        msg = confirmations.get(query.intent)
        if msg:
            self.speak_async(msg)
    
    def _speak_help(self):
        """Speak available commands."""
        help_text = """
        You can say:
        Play stream 1 through 10.
        Play, pause, or stop.
        Volume up, down, or a number.
        Search for something.
        Go to home, streams, or podcasts.
        Start or stop recording.
        Open settings.
        What's playing.
        """
        self.speak(help_text)
    
    def speak(self, text: str):
        """Speak text synchronously."""
        if not self.tts:
            return
        
        self._set_state(VoiceState.SPEAKING)
        try:
            self.tts.say(text)
            self.tts.runAndWait()
        except Exception:
            pass
        finally:
            # Return to previous state
            if self._state == VoiceState.SPEAKING:
                if self.continuous_listening:
                    self._set_state(VoiceState.LISTENING_FOR_COMMAND)
                elif self.wake_word_enabled:
                    self._set_state(VoiceState.LISTENING_FOR_WAKE)
    
    def speak_async(self, text: str):
        """Speak text asynchronously."""
        threading.Thread(
            target=self.speak,
            args=(text,),
            daemon=True
        ).start()
    
    def set_continuous_listening(self, enabled: bool):
        """Enable or disable continuous listening mode."""
        self.continuous_listening = enabled
        
        if enabled and self._state != VoiceState.DISABLED:
            self._set_state(VoiceState.LISTENING_FOR_COMMAND)
            self._start_command_listening()
    
    def set_wake_word_enabled(self, enabled: bool):
        """Enable or disable wake word detection."""
        self.wake_word_enabled = enabled
        
        if enabled and self._state == VoiceState.LISTENING_FOR_COMMAND:
            self._set_state(VoiceState.LISTENING_FOR_WAKE)
            self.wake_detector.start()
        elif not enabled:
            self.wake_detector.stop()


class VoiceGuidedSetup:
    """
    Voice-guided initial setup for ACB Link.
    """
    
    def __init__(self, voice_controller: EnhancedVoiceController):
        self.voice = voice_controller
        self._setup_complete = False
        self._current_step = 0
        self._settings: Dict[str, Any] = {}
    
    def start_setup(self):
        """Start voice-guided setup."""
        self.voice.speak(
            "Welcome to ACB Link. I'll help you set up the application. "
            "You can say 'skip' to skip any step, or 'repeat' to hear the question again."
        )
        
        self._current_step = 0
        self._run_step()
    
    def _run_step(self):
        """Run current setup step."""
        steps = [
            self._setup_voice_preference,
            self._setup_default_tab,
            self._setup_notifications,
            self._setup_complete_message,
        ]
        
        if self._current_step < len(steps):
            steps[self._current_step]()
    
    def _setup_voice_preference(self):
        """Ask about voice control preferences."""
        self.voice.speak(
            "Would you like to enable the wake word 'Hey ACB Link' "
            "to activate voice control? Say yes or no."
        )
        # In real implementation, would listen for response
    
    def _setup_default_tab(self):
        """Ask about default tab."""
        self.voice.speak(
            "Which tab would you like to see when the app opens? "
            "Say home, streams, or podcasts."
        )
    
    def _setup_notifications(self):
        """Ask about notifications."""
        self.voice.speak(
            "Would you like to receive notifications about live events? "
            "Say yes or no."
        )
    
    def _setup_complete_message(self):
        """Complete setup."""
        self.voice.speak(
            "Setup complete! You can change these settings anytime "
            "by saying 'open settings' or using the settings menu."
        )
        self._setup_complete = True
