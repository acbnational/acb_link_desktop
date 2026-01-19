"""
ACB Link - Accessible Desktop Application
Developed by Blind Information Technology Solutions (BITS)
For the American Council of the Blind (ACB)

Version: 1.0.0 - Initial Release
"""

__version__ = "1.0.0"
__author__ = "Blind Information Technology Solutions (BITS)"
__copyright__ = "© 2026 American Council of the Blind"

# Core modules
from .main_frame import MainFrame
from .settings import AppSettings

# Feature modules
from .podcast_manager import PodcastManager, Podcast, PodcastEpisode
from .native_player import NativeAudioPlayer, SleepTimer, PlayerState
from .favorites import FavoritesManager, Favorite, Bookmark, FavoriteType
from .playlists import PlaylistManager, Playlist, PlaylistPlayer, RepeatMode
from .scheduled_recording import ScheduledRecordingManager, ScheduledRecording, RecordingPreset
from .search import GlobalSearch, SearchResult, SearchResultType
from .offline import OfflineManager, ConnectivityMonitor
from .calendar_integration import CalendarManager, CalendarEvent, EventReminder
from .enhanced_voice import EnhancedVoiceController, VoiceState, NaturalLanguageProcessor, WakeWordDetector
from .localization import get_translation_manager, _, TranslationKey, Language
from .shortcuts import ShortcutManager, Shortcut, ShortcutCategory
from .event_scheduler import EventScheduler, ScheduledEvent, AlertType, EventAction
from .styles import StyleManager, ColorScheme, UIConstants, get_style_manager

# Accessibility (WCAG 2.2 AA)
from .accessibility import (
    announce, make_accessible, make_list_accessible,
    ScreenReader, get_screen_reader_manager
)

# System-level scheduling
from .scheduler import (
    get_scheduler, schedule_recording, schedule_reminder,
    schedule_podcast_sync, cancel_task,
    TaskType, ScheduledTask
)

# Auto-updates
from .updater import (
    UpdateChecker, AutoUpdateManager, check_for_updates_manual,
    check_for_updates_on_startup, get_update_manager
)

# Configuration management
from .config import (
    AppConfig, get_config, reload_config, save_config,
    DataSourceConfig, LiveDataConfig, PathConfig
)

# Data synchronization
from .data_sync import (
    DataSyncManager, get_sync_manager, sync_all_data, sync_data_source,
    SyncResult, SyncStatus
)

# Analytics (privacy-respecting, opt-in)
from .analytics import (
    AnalyticsManager, AnalyticsSettings, ConsentLevel,
    get_analytics_manager, track_usage, track_feature, track_crash,
    track_performance, install_crash_handler
)

# Distribution and delta updates
from .distribution import (
    DistributionManager, DistributionChannel, DeltaUpdateManager,
    get_distribution_channel, get_distribution_manager
)

# User feedback
from .feedback import (
    FeedbackDialog, FeedbackType, show_feedback_dialog,
    build_github_issue_url, get_system_info
)

# Affiliate feedback
from .affiliate_feedback import (
    AffiliateCorrectionDialog, AffiliateInfo, show_affiliate_correction_dialog
)

# Affiliate correction admin
from .affiliate_admin import (
    CorrectionManager, CorrectionQueue, AuditLog, XMLUpdater,
    AffiliateCorrection, CorrectionStatus, AffiliateType,
    AdminReviewPanel, AdminReviewDialog,
    show_admin_review_dialog, get_correction_manager, submit_affiliate_correction
)

# Advanced settings
from .advanced_settings import (
    AdvancedSettingsDialog, AdvancedSettingsWarningDialog,
    show_advanced_settings, UserModeManager, FieldValidator
)

# Admin configuration and authentication (server-based - legacy)
from .admin_config import (
    AdminToken, SignedConfig, OrganizationConfig, UserPreferences,
    ConfigSigner, ConfigSyncState, AdminConfigManager,
    AuditEntry as AdminAuditEntry, get_admin_config_manager
)

# GitHub-based admin authentication (free, no server required)
from .github_admin import (
    AdminRole, AdminPermission, AdminSession, AuditEntry,
    GitHubAdminManager, GitHubClient, GitHubUser,
    get_github_admin_manager
)

from .admin_auth_ui import (
    AdminLoginDialog, AdminSessionPanel, AdminRequiredDialog,
    require_admin_login, show_admin_login_dialog
)

# App enhancements for 1.0
from .app_enhancements import (
    PerformanceMonitor, PerformanceMetrics,
    StatusBar, StatusLevel, StatusMessage,
    NotificationCenter, NotificationType, Notification, get_notification_center,
    SessionManager, SessionInfo, get_session_manager,
    AppStateManager, AppState, get_app_state_manager,
    StartupOptimizer, LazyLoader, MemoryOptimizer,
    WelcomeDialog, FocusTracker, QuickAction, QuickActionsPanel
)

# User experience enhancements
from .user_experience import (
    ListeningStats, ListeningStatsManager,
    ResumePlaybackManager, LastPlaybackState,
    SettingsBackupManager,
    QuickStatusAnnouncer, PanicKeyHandler, FontSizeManager,
    ListeningStatsDialog, ExportImportDialog, ResumePlaybackDialog,
    WelcomeWizard, show_welcome_wizard_if_needed, is_first_run,
    HIGH_CONTRAST_PRESETS
)

# Playback enhancements
from .playback_enhancements import (
    EnhancedSleepTimer, SleepTimerDialog, SleepTimerPreset,
    AutoPlayManager, AutoPlaySettings, AutoPlayDialog,
    PlaybackSpeedController, PlaybackSpeedDialog, PlaybackSpeedPreset,
    NowPlayingInfo, ShareManager,
    RecentlyPlayedManager, RecentlyPlayedDialog, RecentItem,
    MediaKeyHandler,
    AudioDuckingManager, AudioDuckingSettings, AudioDuckingDialog,
    QuietHoursManager, QuietHoursSettings, QuietHoursDialog
)

# View settings and pane navigation
from .view_settings import (
    ViewSettings, ViewSettingsManager, ViewSettingsDialog,
    PaneNavigator, PaneType, NavigablePane,
    FocusModeManager, FocusModeSettings,
    LowVisionSettings, VisualSettingsManager, COLOR_SCHEMES,
    StreamScheduleManager, ScheduleEntry, SchedulePreviewDialog,
    FavoritesQuickDial
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__copyright__',
    
    # Core
    'MainFrame',
    'AppSettings',
    
    # Podcasts
    'PodcastManager',
    'Podcast',
    'PodcastEpisode',
    
    # Audio player
    'NativeAudioPlayer',
    'SleepTimer',
    'PlayerState',
    
    # Favorites
    'FavoritesManager',
    'Favorite',
    'Bookmark',
    'FavoriteType',
    
    # Playlists
    'PlaylistManager',
    'Playlist',
    'PlaylistPlayer',
    'RepeatMode',
    
    # Recording
    'ScheduledRecordingManager',
    'ScheduledRecording',
    'RecordingPreset',
    
    # Search
    'GlobalSearch',
    'SearchResult',
    'SearchResultType',
    
    # Offline
    'OfflineManager',
    'ConnectivityMonitor',
    
    # Calendar
    'CalendarManager',
    'CalendarEvent',
    'EventReminder',
    
    # Voice control
    'EnhancedVoiceController',
    'VoiceState',
    'NaturalLanguageProcessor',
    'WakeWordDetector',
    
    # Localization
    'get_translation_manager',
    '_',
    'TranslationKey',
    'Language',
    
    # Shortcuts
    'ShortcutManager',
    'Shortcut',
    'ShortcutCategory',
    
    # Event Scheduler
    'EventScheduler',
    'ScheduledEvent',
    'AlertType',
    'EventAction',
    
    # Styles
    'StyleManager',
    'ColorScheme',
    'UIConstants',
    'get_style_manager',
    
    # Accessibility
    'announce',
    'make_accessible',
    'make_list_accessible',
    'ScreenReader',
    'get_screen_reader_manager',
    
    # System Scheduling
    'get_scheduler',
    'schedule_recording',
    'schedule_reminder',
    'schedule_podcast_sync',
    'cancel_task',
    'TaskType',
    'ScheduledTask',
    
    # Auto-Updates
    'UpdateChecker',
    'AutoUpdateManager',
    'check_for_updates_manual',
    'check_for_updates_on_startup',
    'get_update_manager',
    
    # Configuration
    'AppConfig',
    'get_config',
    'reload_config',
    'save_config',
    'DataSourceConfig',
    'LiveDataConfig',
    'PathConfig',
    
    # Data Sync
    'DataSyncManager',
    'get_sync_manager',
    'sync_all_data',
    'sync_data_source',
    'SyncResult',
    'SyncStatus',
    
    # Analytics
    'AnalyticsManager',
    'AnalyticsSettings',
    'ConsentLevel',
    'get_analytics_manager',
    'track_usage',
    'track_feature',
    'track_crash',
    'track_performance',
    'install_crash_handler',
    
    # Distribution
    'DistributionManager',
    'DistributionChannel',
    'DeltaUpdateManager',
    'get_distribution_channel',
    'get_distribution_manager',
    
    # User Feedback
    'FeedbackDialog',
    'FeedbackType',
    'show_feedback_dialog',
    'build_github_issue_url',
    'get_system_info',
    
    # Affiliate Feedback
    'AffiliateCorrectionDialog',
    'AffiliateInfo',
    'show_affiliate_correction_dialog',
    
    # Affiliate Admin
    'CorrectionManager',
    'CorrectionQueue',
    'AuditLog',
    'XMLUpdater',
    'AffiliateCorrection',
    'CorrectionStatus',
    'AffiliateType',
    'AdminReviewPanel',
    'AdminReviewDialog',
    'show_admin_review_dialog',
    'get_correction_manager',
    'submit_affiliate_correction',
    
    # Admin Configuration and Authentication
    'AdminRole',
    'AdminPermission',
    'AdminToken',
    'AdminSession',
    'SignedConfig',
    'OrganizationConfig',
    'UserPreferences',
    'ConfigSigner',
    'ConfigSyncState',
    'AdminConfigManager',
    'AuditEntry',
    'AdminAuditEntry',
    'get_admin_config_manager',
    'AdminLoginDialog',
    'AdminSessionPanel',
    'AdminRequiredDialog',
    'require_admin_login',
    'show_admin_login_dialog',
    
    # User Experience
    'ListeningStats',
    'ListeningStatsManager',
    'ResumePlaybackManager',
    'LastPlaybackState',
    'SettingsBackupManager',
    'QuickStatusAnnouncer',
    'PanicKeyHandler',
    'FontSizeManager',
    'ListeningStatsDialog',
    'ExportImportDialog',
    'ResumePlaybackDialog',
    'WelcomeWizard',
    'show_welcome_wizard_if_needed',
    'is_first_run',
    'HIGH_CONTRAST_PRESETS',
    
    # Playback Enhancements
    'EnhancedSleepTimer',
    'SleepTimerDialog',
    'SleepTimerPreset',
    'AutoPlayManager',
    'AutoPlaySettings',
    'AutoPlayDialog',
    'PlaybackSpeedController',
    'PlaybackSpeedDialog',
    'PlaybackSpeedPreset',
    'NowPlayingInfo',
    'ShareManager',
    'RecentlyPlayedManager',
    'RecentlyPlayedDialog',
    'RecentItem',
    'MediaKeyHandler',
    'AudioDuckingManager',
    'AudioDuckingSettings',
    'AudioDuckingDialog',
    'QuietHoursManager',
    'QuietHoursSettings',
    'QuietHoursDialog',
    
    # View Settings and Layout
    'ViewSettings',
    'ViewSettingsManager',
    'ViewSettingsDialog',
    'PaneNavigator',
    'PaneType',
    'NavigablePane',
    'FocusModeManager',
    'FocusModeSettings',
    'LowVisionSettings',
    'VisualSettingsManager',
    'COLOR_SCHEMES',
    'StreamScheduleManager',
    'ScheduleEntry',
    'SchedulePreviewDialog',
    'FavoritesQuickDial',
]
