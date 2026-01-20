"""
ACB Link - Localization and Multi-language Support Module
Provides UI translation and language management.
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional


class Language(Enum):
    """Supported languages."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    ITALIAN = "it"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    RUSSIAN = "ru"


@dataclass
class LanguageInfo:
    """Information about a language."""

    code: str
    name: str
    native_name: str
    direction: str  # ltr or rtl


# Language metadata
LANGUAGE_INFO: Dict[str, LanguageInfo] = {
    "en": LanguageInfo("en", "English", "English", "ltr"),
    "es": LanguageInfo("es", "Spanish", "Español", "ltr"),
    "fr": LanguageInfo("fr", "French", "Français", "ltr"),
    "de": LanguageInfo("de", "German", "Deutsch", "ltr"),
    "pt": LanguageInfo("pt", "Portuguese", "Português", "ltr"),
    "it": LanguageInfo("it", "Italian", "Italiano", "ltr"),
    "zh": LanguageInfo("zh", "Chinese", "中文", "ltr"),
    "ja": LanguageInfo("ja", "Japanese", "日本語", "ltr"),
    "ko": LanguageInfo("ko", "Korean", "한국어", "ltr"),
    "ar": LanguageInfo("ar", "Arabic", "العربية", "rtl"),
    "ru": LanguageInfo("ru", "Russian", "Русский", "ltr"),
}


class TranslationKey:
    """Translation key constants."""

    # App-wide
    APP_TITLE = "app.title"
    APP_WELCOME = "app.welcome"

    # Menu items
    MENU_FILE = "menu.file"
    MENU_EDIT = "menu.edit"
    MENU_VIEW = "menu.view"
    MENU_HELP = "menu.help"
    MENU_EXIT = "menu.exit"
    MENU_SETTINGS = "menu.settings"
    MENU_ABOUT = "menu.about"

    # Tabs
    TAB_HOME = "tab.home"
    TAB_STREAMS = "tab.streams"
    TAB_PODCASTS = "tab.podcasts"
    TAB_FAVORITES = "tab.favorites"
    TAB_PLAYLISTS = "tab.playlists"
    TAB_SEARCH = "tab.search"
    TAB_CALENDAR = "tab.calendar"

    # Buttons
    BTN_PLAY = "button.play"
    BTN_PAUSE = "button.pause"
    BTN_STOP = "button.stop"
    BTN_RECORD = "button.record"
    BTN_SAVE = "button.save"
    BTN_CANCEL = "button.cancel"
    BTN_OK = "button.ok"
    BTN_ADD = "button.add"
    BTN_REMOVE = "button.remove"
    BTN_EDIT = "button.edit"
    BTN_DELETE = "button.delete"
    BTN_DOWNLOAD = "button.download"
    BTN_REFRESH = "button.refresh"

    # Labels
    LABEL_VOLUME = "label.volume"
    LABEL_DURATION = "label.duration"
    LABEL_PLAYING = "label.playing"
    LABEL_STOPPED = "label.stopped"
    LABEL_RECORDING = "label.recording"
    LABEL_OFFLINE = "label.offline"
    LABEL_ONLINE = "label.online"
    LABEL_LOADING = "label.loading"
    LABEL_SEARCH = "label.search"
    LABEL_NO_RESULTS = "label.no_results"

    # Stream panel
    STREAM_SELECT = "stream.select"
    STREAM_TITLE = "stream.title"
    STREAM_NOW_PLAYING = "stream.now_playing"

    # Podcast panel
    PODCAST_EPISODES = "podcast.episodes"
    PODCAST_SUBSCRIBE = "podcast.subscribe"
    PODCAST_UNSUBSCRIBE = "podcast.unsubscribe"
    PODCAST_DOWNLOAD = "podcast.download"
    PODCAST_PLAY = "podcast.play"

    # Favorites
    FAVORITES_ADD = "favorites.add"
    FAVORITES_REMOVE = "favorites.remove"
    FAVORITES_EMPTY = "favorites.empty"

    # Playlists
    PLAYLIST_CREATE = "playlist.create"
    PLAYLIST_DELETE = "playlist.delete"
    PLAYLIST_ADD_TRACK = "playlist.add_track"
    PLAYLIST_SHUFFLE = "playlist.shuffle"
    PLAYLIST_REPEAT = "playlist.repeat"

    # Calendar
    CALENDAR_EVENTS = "calendar.events"
    CALENDAR_TODAY = "calendar.today"
    CALENDAR_UPCOMING = "calendar.upcoming"
    CALENDAR_REMINDER = "calendar.reminder"

    # Voice control
    VOICE_ENABLED = "voice.enabled"
    VOICE_DISABLED = "voice.disabled"
    VOICE_LISTENING = "voice.listening"
    VOICE_WAKE_WORD = "voice.wake_word"

    # Settings
    SETTINGS_GENERAL = "settings.general"
    SETTINGS_AUDIO = "settings.audio"
    SETTINGS_VOICE = "settings.voice"
    SETTINGS_LANGUAGE = "settings.language"
    SETTINGS_NOTIFICATIONS = "settings.notifications"
    SETTINGS_RECORDING = "settings.recording"
    SETTINGS_STORAGE = "settings.storage"

    # Messages
    MSG_CONFIRM_DELETE = "message.confirm_delete"
    MSG_SAVE_SUCCESS = "message.save_success"
    MSG_SAVE_ERROR = "message.save_error"
    MSG_DOWNLOAD_COMPLETE = "message.download_complete"
    MSG_DOWNLOAD_ERROR = "message.download_error"
    MSG_NETWORK_ERROR = "message.network_error"


# Default English translations
DEFAULT_TRANSLATIONS: Dict[str, str] = {
    # App-wide
    TranslationKey.APP_TITLE: "ACB Link",
    TranslationKey.APP_WELCOME: "Welcome to ACB Link",
    # Menu items
    TranslationKey.MENU_FILE: "&File",
    TranslationKey.MENU_EDIT: "&Edit",
    TranslationKey.MENU_VIEW: "&View",
    TranslationKey.MENU_HELP: "&Help",
    TranslationKey.MENU_EXIT: "E&xit",
    TranslationKey.MENU_SETTINGS: "&Settings...",
    TranslationKey.MENU_ABOUT: "&About",
    # Tabs
    TranslationKey.TAB_HOME: "Home",
    TranslationKey.TAB_STREAMS: "Streams",
    TranslationKey.TAB_PODCASTS: "Podcasts",
    TranslationKey.TAB_FAVORITES: "Favorites",
    TranslationKey.TAB_PLAYLISTS: "Playlists",
    TranslationKey.TAB_SEARCH: "Search",
    TranslationKey.TAB_CALENDAR: "Calendar",
    # Buttons
    TranslationKey.BTN_PLAY: "Play",
    TranslationKey.BTN_PAUSE: "Pause",
    TranslationKey.BTN_STOP: "Stop",
    TranslationKey.BTN_RECORD: "Record",
    TranslationKey.BTN_SAVE: "Save",
    TranslationKey.BTN_CANCEL: "Cancel",
    TranslationKey.BTN_OK: "OK",
    TranslationKey.BTN_ADD: "Add",
    TranslationKey.BTN_REMOVE: "Remove",
    TranslationKey.BTN_EDIT: "Edit",
    TranslationKey.BTN_DELETE: "Delete",
    TranslationKey.BTN_DOWNLOAD: "Download",
    TranslationKey.BTN_REFRESH: "Refresh",
    # Labels
    TranslationKey.LABEL_VOLUME: "Volume",
    TranslationKey.LABEL_DURATION: "Duration",
    TranslationKey.LABEL_PLAYING: "Playing",
    TranslationKey.LABEL_STOPPED: "Stopped",
    TranslationKey.LABEL_RECORDING: "Recording",
    TranslationKey.LABEL_OFFLINE: "Offline",
    TranslationKey.LABEL_ONLINE: "Online",
    TranslationKey.LABEL_LOADING: "Loading...",
    TranslationKey.LABEL_SEARCH: "Search",
    TranslationKey.LABEL_NO_RESULTS: "No results found",
    # Stream panel
    TranslationKey.STREAM_SELECT: "Select a stream",
    TranslationKey.STREAM_TITLE: "ACB Media Streams",
    TranslationKey.STREAM_NOW_PLAYING: "Now Playing",
    # Podcast panel
    TranslationKey.PODCAST_EPISODES: "Episodes",
    TranslationKey.PODCAST_SUBSCRIBE: "Subscribe",
    TranslationKey.PODCAST_UNSUBSCRIBE: "Unsubscribe",
    TranslationKey.PODCAST_DOWNLOAD: "Download Episode",
    TranslationKey.PODCAST_PLAY: "Play Episode",
    # Favorites
    TranslationKey.FAVORITES_ADD: "Add to Favorites",
    TranslationKey.FAVORITES_REMOVE: "Remove from Favorites",
    TranslationKey.FAVORITES_EMPTY: "No favorites yet",
    # Playlists
    TranslationKey.PLAYLIST_CREATE: "Create Playlist",
    TranslationKey.PLAYLIST_DELETE: "Delete Playlist",
    TranslationKey.PLAYLIST_ADD_TRACK: "Add to Playlist",
    TranslationKey.PLAYLIST_SHUFFLE: "Shuffle",
    TranslationKey.PLAYLIST_REPEAT: "Repeat",
    # Calendar
    TranslationKey.CALENDAR_EVENTS: "Events",
    TranslationKey.CALENDAR_TODAY: "Today",
    TranslationKey.CALENDAR_UPCOMING: "Upcoming",
    TranslationKey.CALENDAR_REMINDER: "Set Reminder",
    # Voice control
    TranslationKey.VOICE_ENABLED: "Voice control enabled",
    TranslationKey.VOICE_DISABLED: "Voice control disabled",
    TranslationKey.VOICE_LISTENING: "Listening...",
    TranslationKey.VOICE_WAKE_WORD: "Say 'Hey ACB Link' to activate",
    # Settings
    TranslationKey.SETTINGS_GENERAL: "General",
    TranslationKey.SETTINGS_AUDIO: "Audio",
    TranslationKey.SETTINGS_VOICE: "Voice Control",
    TranslationKey.SETTINGS_LANGUAGE: "Language",
    TranslationKey.SETTINGS_NOTIFICATIONS: "Notifications",
    TranslationKey.SETTINGS_RECORDING: "Recording",
    TranslationKey.SETTINGS_STORAGE: "Storage",
    # Messages
    TranslationKey.MSG_CONFIRM_DELETE: "Are you sure you want to delete this?",
    TranslationKey.MSG_SAVE_SUCCESS: "Saved successfully",
    TranslationKey.MSG_SAVE_ERROR: "Error saving",
    TranslationKey.MSG_DOWNLOAD_COMPLETE: "Download complete",
    TranslationKey.MSG_DOWNLOAD_ERROR: "Download failed",
    TranslationKey.MSG_NETWORK_ERROR: "Network error. Please check your connection.",
}


class TranslationManager:
    """
    Manages translations and language selection.
    """

    def __init__(self, translations_dir: Optional[str] = None):
        self.translations_dir = translations_dir or self._default_translations_dir()
        self._current_language = "en"
        self._translations: Dict[str, Dict[str, str]] = {"en": DEFAULT_TRANSLATIONS.copy()}
        self._fallback_language = "en"

        # Callbacks
        self.on_language_changed: Optional[Callable[[str], None]] = None

        # Load available translations
        self._load_translations()

    def _default_translations_dir(self) -> str:
        """Get default translations directory."""
        module_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(module_dir, "translations")

    def _load_translations(self):
        """Load all available translation files."""
        if not os.path.exists(self.translations_dir):
            os.makedirs(self.translations_dir, exist_ok=True)
            return

        for filename in os.listdir(self.translations_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]  # Remove .json
                filepath = os.path.join(self.translations_dir, filename)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._translations[lang_code] = json.load(f)
                except Exception:
                    pass

    def get_available_languages(self) -> List[LanguageInfo]:
        """Get list of available languages."""
        languages = []
        for code in self._translations.keys():
            if code in LANGUAGE_INFO:
                languages.append(LANGUAGE_INFO[code])
            else:
                languages.append(LanguageInfo(code, code, code, "ltr"))
        return languages

    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_language

    def set_language(self, language_code: str) -> bool:
        """Set current language."""
        if language_code not in self._translations:
            # Try to load language
            if not self._load_language(language_code):
                return False

        self._current_language = language_code

        if self.on_language_changed:
            self.on_language_changed(language_code)

        return True

    def _load_language(self, language_code: str) -> bool:
        """Load a specific language file."""
        filepath = os.path.join(self.translations_dir, f"{language_code}.json")

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._translations[language_code] = json.load(f)
            return True
        except Exception:
            return False

    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.

        Args:
            key: Translation key
            **kwargs: Format arguments for the translation

        Returns:
            Translated string or key if not found
        """
        # Get translation from current language
        translation = self._translations.get(self._current_language, {}).get(key)

        # Fall back to default language
        if translation is None:
            translation = self._translations.get(self._fallback_language, {}).get(key)

        # Return key if not found
        if translation is None:
            return key

        # Apply format arguments
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation

        return translation

    def __call__(self, key: str, **kwargs) -> str:
        """Shortcut for translate()."""
        return self.translate(key, **kwargs)

    def save_language_file(self, language_code: str, translations: Dict[str, str]):
        """Save a language file."""
        os.makedirs(self.translations_dir, exist_ok=True)

        filepath = os.path.join(self.translations_dir, f"{language_code}.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        self._translations[language_code] = translations

    def export_template(self, filepath: str):
        """Export a translation template with all keys."""
        template = {key: "" for key in DEFAULT_TRANSLATIONS.keys()}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)


# Global instance
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def _(key: str, **kwargs) -> str:
    """
    Convenience function for translation.

    Usage:
        label = _("button.play")
        message = _("message.welcome", name="User")
    """
    return get_translation_manager().translate(key, **kwargs)


class LocalizedWidget:
    """
    Mixin for wxPython widgets that support localization.
    Call update_language() when language changes.
    """

    def __init__(self):
        self._translation_keys: Dict[str, str] = {}

    def set_label_key(self, key: str):
        """Set translation key for widget label."""
        self._translation_keys["label"] = key
        self._update_label()

    def set_tooltip_key(self, key: str):
        """Set translation key for tooltip."""
        self._translation_keys["tooltip"] = key
        self._update_tooltip()

    def update_language(self):
        """Update widget text for current language."""
        self._update_label()
        self._update_tooltip()

    def _update_label(self):
        """Update label text."""
        if "label" in self._translation_keys:
            key = self._translation_keys["label"]
            if hasattr(self, "SetLabel"):
                self.SetLabel(_(key))  # type: ignore[attr-defined]

    def _update_tooltip(self):
        """Update tooltip text."""
        if "tooltip" in self._translation_keys:
            key = self._translation_keys["tooltip"]
            if hasattr(self, "SetToolTip"):
                self.SetToolTip(_(key))  # type: ignore[attr-defined]


class LanguageSelector:
    """Helper for creating language selection UI."""

    @staticmethod
    def get_language_choices() -> List[tuple]:
        """Get list of (display_name, code) tuples for UI."""
        manager = get_translation_manager()
        languages = manager.get_available_languages()

        return [(f"{lang.native_name} ({lang.name})", lang.code) for lang in languages]

    @staticmethod
    def create_language_menu(parent, on_select: Callable[[str], None]):
        """
        Create a language selection menu.

        Args:
            parent: Parent wx window
            on_select: Callback when language is selected

        Returns:
            wx.Menu with language options
        """
        import wx

        menu = wx.Menu()
        manager = get_translation_manager()

        for lang in manager.get_available_languages():
            item = menu.AppendCheckItem(wx.ID_ANY, f"{lang.native_name} ({lang.name})")
            item.Check(lang.code == manager.current_language)

            def handler(evt, code=lang.code):
                on_select(code)

            parent.Bind(wx.EVT_MENU, handler, item)

        return menu


# Spanish translations
SPANISH_TRANSLATIONS: Dict[str, str] = {
    # App-wide
    TranslationKey.APP_TITLE: "ACB Link",
    TranslationKey.APP_WELCOME: "Bienvenido a ACB Link",
    # Menu items
    TranslationKey.MENU_FILE: "&Archivo",
    TranslationKey.MENU_EDIT: "&Editar",
    TranslationKey.MENU_VIEW: "&Ver",
    TranslationKey.MENU_HELP: "A&yuda",
    TranslationKey.MENU_EXIT: "&Salir",
    TranslationKey.MENU_SETTINGS: "&Configuración...",
    TranslationKey.MENU_ABOUT: "&Acerca de",
    # Tabs
    TranslationKey.TAB_HOME: "Inicio",
    TranslationKey.TAB_STREAMS: "Transmisiones",
    TranslationKey.TAB_PODCASTS: "Podcasts",
    TranslationKey.TAB_FAVORITES: "Favoritos",
    TranslationKey.TAB_PLAYLISTS: "Listas de reproducción",
    TranslationKey.TAB_SEARCH: "Buscar",
    TranslationKey.TAB_CALENDAR: "Calendario",
    # Buttons
    TranslationKey.BTN_PLAY: "Reproducir",
    TranslationKey.BTN_PAUSE: "Pausar",
    TranslationKey.BTN_STOP: "Detener",
    TranslationKey.BTN_RECORD: "Grabar",
    TranslationKey.BTN_SAVE: "Guardar",
    TranslationKey.BTN_CANCEL: "Cancelar",
    TranslationKey.BTN_OK: "Aceptar",
    TranslationKey.BTN_ADD: "Agregar",
    TranslationKey.BTN_REMOVE: "Quitar",
    TranslationKey.BTN_EDIT: "Editar",
    TranslationKey.BTN_DELETE: "Eliminar",
    TranslationKey.BTN_DOWNLOAD: "Descargar",
    TranslationKey.BTN_REFRESH: "Actualizar",
    # Labels
    TranslationKey.LABEL_VOLUME: "Volumen",
    TranslationKey.LABEL_DURATION: "Duración",
    TranslationKey.LABEL_PLAYING: "Reproduciendo",
    TranslationKey.LABEL_STOPPED: "Detenido",
    TranslationKey.LABEL_RECORDING: "Grabando",
    TranslationKey.LABEL_OFFLINE: "Sin conexión",
    TranslationKey.LABEL_ONLINE: "En línea",
    TranslationKey.LABEL_LOADING: "Cargando...",
    TranslationKey.LABEL_SEARCH: "Buscar",
    TranslationKey.LABEL_NO_RESULTS: "No se encontraron resultados",
    # Stream panel
    TranslationKey.STREAM_SELECT: "Seleccionar transmisión",
    TranslationKey.STREAM_TITLE: "Transmisiones ACB Media",
    TranslationKey.STREAM_NOW_PLAYING: "Reproduciendo ahora",
    # Voice control
    TranslationKey.VOICE_ENABLED: "Control por voz activado",
    TranslationKey.VOICE_DISABLED: "Control por voz desactivado",
    TranslationKey.VOICE_LISTENING: "Escuchando...",
    TranslationKey.VOICE_WAKE_WORD: "Diga 'Hey ACB Link' para activar",
    # Messages
    TranslationKey.MSG_CONFIRM_DELETE: "¿Está seguro de que desea eliminar esto?",
    TranslationKey.MSG_SAVE_SUCCESS: "Guardado exitosamente",
    TranslationKey.MSG_SAVE_ERROR: "Error al guardar",
    TranslationKey.MSG_DOWNLOAD_COMPLETE: "Descarga completa",
    TranslationKey.MSG_DOWNLOAD_ERROR: "Error en la descarga",
    TranslationKey.MSG_NETWORK_ERROR: "Error de red. Por favor verifique su conexión.",
}


def init_spanish_translation():
    """Initialize Spanish translation."""
    manager = get_translation_manager()
    manager._translations["es"] = SPANISH_TRANSLATIONS
