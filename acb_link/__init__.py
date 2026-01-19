"""
ACB Link - Accessible Desktop Application
Developed by Blind Information Technology Solutions (BITS)
For the American Council of the Blind (ACB)

Version: 1.0.0 - Initial Release
"""

__version__ = "1.0.0"
__author__ = "Blind Information Technology Solutions (BITS)"
__copyright__ = "© 2026 American Council of the Blind"

# Accessibility (WCAG 2.2 AA)
from .accessibility import (
    ScreenReader,
    announce,
    get_screen_reader_manager,
    make_accessible,
    make_list_accessible,
)
from .admin_auth_ui import (
    AdminLoginDialog,
    AdminRequiredDialog,
    AdminSessionPanel,
    require_admin_login,
    show_admin_login_dialog,
)

# Admin configuration and authentication (server-based - legacy)
from .admin_config import AdminConfigManager, AdminToken
from .admin_config import AuditEntry as AdminAuditEntry
from .admin_config import (
    ConfigSigner,
    ConfigSyncState,
    OrganizationConfig,
    SignedConfig,
    UserPreferences,
    get_admin_config_manager,
)

# Advanced settings
# Affiliate correction admin
from .affiliate_admin import (
    AdminReviewDialog,
    AdminReviewPanel,
    AffiliateCorrection,
    AffiliateType,
    AuditLog,
    CorrectionManager,
    CorrectionQueue,
    CorrectionStatus,
    XMLUpdater,
    get_correction_manager,
    show_admin_review_dialog,
    submit_affiliate_correction,
)

# Affiliate feedback
from .affiliate_feedback import (
    AffiliateCorrectionDialog,
    AffiliateInfo,
    show_affiliate_correction_dialog,
)

# Analytics (privacy-respecting, opt-in)
from .analytics import (
    AnalyticsManager,
    AnalyticsSettings,
    ConsentLevel,
    get_analytics_manager,
    install_crash_handler,
    track_crash,
    track_feature,
    track_performance,
    track_usage,
)

# App enhancements for 1.0
from .calendar_integration import CalendarEvent, CalendarManager, EventReminder

# Configuration management
from .config import (
    AppConfig,
    DataSourceConfig,
    LiveDataConfig,
    PathConfig,
    get_config,
    reload_config,
    save_config,
)

# Data synchronization
from .data_sync import (
    DataSyncManager,
    SyncResult,
    SyncStatus,
    get_sync_manager,
    sync_all_data,
    sync_data_source,
)

# Distribution and delta updates
from .distribution import (
    DeltaUpdateManager,
    DistributionChannel,
    DistributionManager,
    get_distribution_channel,
    get_distribution_manager,
)
from .enhanced_voice import (
    EnhancedVoiceController,
    NaturalLanguageProcessor,
    VoiceState,
    WakeWordDetector,
)
from .event_scheduler import AlertType, EventAction, EventScheduler, ScheduledEvent
from .favorites import Bookmark, Favorite, FavoritesManager, FavoriteType

# User feedback
from .feedback import (
    FeedbackDialog,
    FeedbackType,
    build_github_issue_url,
    get_system_info,
    show_feedback_dialog,
)

# GitHub-based admin authentication (free, no server required)
from .github_admin import AdminPermission, AdminRole, AdminSession, AuditEntry
from .localization import Language, TranslationKey, _, get_translation_manager

# Core modules
from .main_frame import MainFrame
from .native_player import NativeAudioPlayer, PlayerState, SleepTimer
from .offline import ConnectivityMonitor, OfflineManager

# Playback enhancements
from .playback_enhancements import (
    AudioDuckingDialog,
    AudioDuckingManager,
    AudioDuckingSettings,
    AutoPlayDialog,
    AutoPlayManager,
    AutoPlaySettings,
    EnhancedSleepTimer,
    MediaKeyHandler,
    NowPlayingInfo,
    PlaybackSpeedController,
    PlaybackSpeedDialog,
    PlaybackSpeedPreset,
    QuietHoursDialog,
    QuietHoursManager,
    QuietHoursSettings,
    RecentItem,
    RecentlyPlayedDialog,
    RecentlyPlayedManager,
    ShareManager,
    SleepTimerDialog,
    SleepTimerPreset,
)
from .playlists import Playlist, PlaylistManager, PlaylistPlayer, RepeatMode

# Feature modules
from .podcast_manager import Podcast, PodcastEpisode, PodcastManager
from .scheduled_recording import RecordingPreset, ScheduledRecording, ScheduledRecordingManager

# System-level scheduling
from .scheduler import (
    ScheduledTask,
    TaskType,
    cancel_task,
    get_scheduler,
    schedule_podcast_sync,
    schedule_recording,
    schedule_reminder,
)
from .search import GlobalSearch, SearchResult, SearchResultType
from .settings import AppSettings
from .shortcuts import Shortcut, ShortcutCategory, ShortcutManager
from .styles import ColorScheme, StyleManager, UIConstants, get_style_manager

# Auto-updates
from .updater import (
    AutoUpdateManager,
    UpdateChecker,
    check_for_updates_manual,
    check_for_updates_on_startup,
    get_update_manager,
)

# User experience enhancements
from .user_experience import (
    HIGH_CONTRAST_PRESETS,
    ExportImportDialog,
    FontSizeManager,
    LastPlaybackState,
    ListeningStats,
    ListeningStatsDialog,
    ListeningStatsManager,
    PanicKeyHandler,
    QuickStatusAnnouncer,
    ResumePlaybackDialog,
    ResumePlaybackManager,
    SettingsBackupManager,
    WelcomeWizard,
    is_first_run,
    show_welcome_wizard_if_needed,
)

# View settings and pane navigation
from .view_settings import (
    COLOR_SCHEMES,
    FavoritesQuickDial,
    FocusModeManager,
    FocusModeSettings,
    LowVisionSettings,
    NavigablePane,
    PaneNavigator,
    PaneType,
    ScheduleEntry,
    SchedulePreviewDialog,
    StreamScheduleManager,
    ViewSettings,
    ViewSettingsDialog,
    ViewSettingsManager,
    VisualSettingsManager,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__copyright__",
    # Core
    "MainFrame",
    "AppSettings",
    # Podcasts
    "PodcastManager",
    "Podcast",
    "PodcastEpisode",
    # Audio player
    "NativeAudioPlayer",
    "SleepTimer",
    "PlayerState",
    # Favorites
    "FavoritesManager",
    "Favorite",
    "Bookmark",
    "FavoriteType",
    # Playlists
    "PlaylistManager",
    "Playlist",
    "PlaylistPlayer",
    "RepeatMode",
    # Recording
    "ScheduledRecordingManager",
    "ScheduledRecording",
    "RecordingPreset",
    # Search
    "GlobalSearch",
    "SearchResult",
    "SearchResultType",
    # Offline
    "OfflineManager",
    "ConnectivityMonitor",
    # Calendar
    "CalendarManager",
    "CalendarEvent",
    "EventReminder",
    # Voice control
    "EnhancedVoiceController",
    "VoiceState",
    "NaturalLanguageProcessor",
    "WakeWordDetector",
    # Localization
    "get_translation_manager",
    "_",
    "TranslationKey",
    "Language",
    # Shortcuts
    "ShortcutManager",
    "Shortcut",
    "ShortcutCategory",
    # Event Scheduler
    "EventScheduler",
    "ScheduledEvent",
    "AlertType",
    "EventAction",
    # Styles
    "StyleManager",
    "ColorScheme",
    "UIConstants",
    "get_style_manager",
    # Accessibility
    "announce",
    "make_accessible",
    "make_list_accessible",
    "ScreenReader",
    "get_screen_reader_manager",
    # System Scheduling
    "get_scheduler",
    "schedule_recording",
    "schedule_reminder",
    "schedule_podcast_sync",
    "cancel_task",
    "TaskType",
    "ScheduledTask",
    # Auto-Updates
    "UpdateChecker",
    "AutoUpdateManager",
    "check_for_updates_manual",
    "check_for_updates_on_startup",
    "get_update_manager",
    # Configuration
    "AppConfig",
    "get_config",
    "reload_config",
    "save_config",
    "DataSourceConfig",
    "LiveDataConfig",
    "PathConfig",
    # Data Sync
    "DataSyncManager",
    "get_sync_manager",
    "sync_all_data",
    "sync_data_source",
    "SyncResult",
    "SyncStatus",
    # Analytics
    "AnalyticsManager",
    "AnalyticsSettings",
    "ConsentLevel",
    "get_analytics_manager",
    "track_usage",
    "track_feature",
    "track_crash",
    "track_performance",
    "install_crash_handler",
    # Distribution
    "DistributionManager",
    "DistributionChannel",
    "DeltaUpdateManager",
    "get_distribution_channel",
    "get_distribution_manager",
    # User Feedback
    "FeedbackDialog",
    "FeedbackType",
    "show_feedback_dialog",
    "build_github_issue_url",
    "get_system_info",
    # Affiliate Feedback
    "AffiliateCorrectionDialog",
    "AffiliateInfo",
    "show_affiliate_correction_dialog",
    # Affiliate Admin
    "CorrectionManager",
    "CorrectionQueue",
    "AuditLog",
    "XMLUpdater",
    "AffiliateCorrection",
    "CorrectionStatus",
    "AffiliateType",
    "AdminReviewPanel",
    "AdminReviewDialog",
    "show_admin_review_dialog",
    "get_correction_manager",
    "submit_affiliate_correction",
    # Admin Configuration and Authentication
    "AdminRole",
    "AdminPermission",
    "AdminToken",
    "AdminSession",
    "SignedConfig",
    "OrganizationConfig",
    "UserPreferences",
    "ConfigSigner",
    "ConfigSyncState",
    "AdminConfigManager",
    "AuditEntry",
    "AdminAuditEntry",
    "get_admin_config_manager",
    "AdminLoginDialog",
    "AdminSessionPanel",
    "AdminRequiredDialog",
    "require_admin_login",
    "show_admin_login_dialog",
    # User Experience
    "ListeningStats",
    "ListeningStatsManager",
    "ResumePlaybackManager",
    "LastPlaybackState",
    "SettingsBackupManager",
    "QuickStatusAnnouncer",
    "PanicKeyHandler",
    "FontSizeManager",
    "ListeningStatsDialog",
    "ExportImportDialog",
    "ResumePlaybackDialog",
    "WelcomeWizard",
    "show_welcome_wizard_if_needed",
    "is_first_run",
    "HIGH_CONTRAST_PRESETS",
    # Playback Enhancements
    "EnhancedSleepTimer",
    "SleepTimerDialog",
    "SleepTimerPreset",
    "AutoPlayManager",
    "AutoPlaySettings",
    "AutoPlayDialog",
    "PlaybackSpeedController",
    "PlaybackSpeedDialog",
    "PlaybackSpeedPreset",
    "NowPlayingInfo",
    "ShareManager",
    "RecentlyPlayedManager",
    "RecentlyPlayedDialog",
    "RecentItem",
    "MediaKeyHandler",
    "AudioDuckingManager",
    "AudioDuckingSettings",
    "AudioDuckingDialog",
    "QuietHoursManager",
    "QuietHoursSettings",
    "QuietHoursDialog",
    # View Settings and Layout
    "ViewSettings",
    "ViewSettingsManager",
    "ViewSettingsDialog",
    "PaneNavigator",
    "PaneType",
    "NavigablePane",
    "FocusModeManager",
    "FocusModeSettings",
    "LowVisionSettings",
    "VisualSettingsManager",
    "COLOR_SCHEMES",
    "StreamScheduleManager",
    "ScheduleEntry",
    "SchedulePreviewDialog",
    "FavoritesQuickDial",
]
