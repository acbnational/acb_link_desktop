"""
ACB Link Desktop - Privacy-Respecting Analytics

Opt-in telemetry for usage statistics, crash reporting, feature tracking,
and performance monitoring. All data collection is disabled by default
and requires explicit user consent.

Privacy principles:
- Opt-in only: No data collected without user consent
- Anonymized: No personally identifiable information
- Local-first: Statistics viewable locally before any submission
- Transparent: Users can view exactly what would be sent
- Deletable: Users can clear all collected data at any time
"""

import json
import logging
import platform
import threading
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


# =============================================================================
# Analytics Settings
# =============================================================================


class ConsentLevel(Enum):
    """Levels of analytics consent."""

    NONE = "none"  # No data collection
    BASIC = "basic"  # Crash reports only
    STANDARD = "standard"  # Crashes + anonymous usage
    FULL = "full"  # All analytics including performance


@dataclass
class AnalyticsSettings:
    """User settings for analytics and telemetry."""

    # Master consent
    analytics_enabled: bool = False
    consent_level: str = "none"  # none, basic, standard, full
    consent_date: Optional[str] = None

    # Granular consent
    crash_reporting: bool = False
    usage_statistics: bool = False
    feature_tracking: bool = False
    performance_monitoring: bool = False

    # Privacy settings
    include_system_info: bool = False
    include_app_version: bool = True

    # Anonymous identifier (generated on first consent, not PII)
    anonymous_id: Optional[str] = None

    def grant_consent(self, level: ConsentLevel):
        """Grant analytics consent at specified level."""
        self.analytics_enabled = level != ConsentLevel.NONE
        self.consent_level = level.value
        self.consent_date = datetime.now().isoformat()

        if level == ConsentLevel.NONE:
            self.crash_reporting = False
            self.usage_statistics = False
            self.feature_tracking = False
            self.performance_monitoring = False
        elif level == ConsentLevel.BASIC:
            self.crash_reporting = True
            self.usage_statistics = False
            self.feature_tracking = False
            self.performance_monitoring = False
        elif level == ConsentLevel.STANDARD:
            self.crash_reporting = True
            self.usage_statistics = True
            self.feature_tracking = True
            self.performance_monitoring = False
        elif level == ConsentLevel.FULL:
            self.crash_reporting = True
            self.usage_statistics = True
            self.feature_tracking = True
            self.performance_monitoring = True

        # Generate anonymous ID on first consent
        if self.analytics_enabled and not self.anonymous_id:
            self.anonymous_id = self._generate_anonymous_id()

    def revoke_consent(self):
        """Revoke all analytics consent."""
        self.grant_consent(ConsentLevel.NONE)
        self.consent_date = None
        # Keep anonymous_id in case user re-consents (prevents duplicate counting)

    @staticmethod
    def _generate_anonymous_id() -> str:
        """Generate a random anonymous identifier (not based on hardware)."""
        return str(uuid.uuid4())


# =============================================================================
# Event Types
# =============================================================================


@dataclass
class AnalyticsEvent:
    """Base analytics event."""

    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UsageEvent(AnalyticsEvent):
    """Usage statistics event."""

    action: str = ""
    category: str = ""
    label: str = ""
    value: Optional[int] = None
    event_type: str = field(default="usage", init=False)


@dataclass
class FeatureEvent(AnalyticsEvent):
    """Feature usage tracking event."""

    feature_name: str = ""
    feature_category: str = ""
    duration_seconds: Optional[float] = None
    event_type: str = field(default="feature", init=False)


@dataclass
class PerformanceEvent(AnalyticsEvent):
    """Performance monitoring event."""

    metric_name: str = ""
    metric_value: float = 0.0
    metric_unit: str = ""
    event_type: str = field(default="performance", init=False)


@dataclass
class CrashEvent(AnalyticsEvent):
    """Crash report event."""

    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    app_version: str = ""
    os_info: str = ""
    event_type: str = field(default="crash", init=False)


# =============================================================================
# Local Analytics Storage
# =============================================================================


class LocalAnalyticsStore:
    """
    Stores analytics data locally before optional submission.
    Users can view and delete this data at any time.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path.home() / ".acb_link" / "analytics"
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._events_file = self.storage_path / "events.json"
        self._crashes_file = self.storage_path / "crashes.json"
        self._stats_file = self.storage_path / "statistics.json"
        self._lock = threading.Lock()

    def store_event(self, event: AnalyticsEvent):
        """Store an analytics event locally."""
        with self._lock:
            events = self._load_events()
            events.append(event.to_dict())

            # Keep only last 1000 events
            if len(events) > 1000:
                events = events[-1000:]

            self._save_events(events)

    def store_crash(self, crash: CrashEvent):
        """Store a crash report locally."""
        with self._lock:
            crashes = self._load_crashes()
            crashes.append(crash.to_dict())

            # Keep only last 50 crashes
            if len(crashes) > 50:
                crashes = crashes[-50:]

            self._save_crashes(crashes)

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get stored events, optionally filtered by type."""
        events = self._load_events()
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        return events

    def get_crashes(self) -> List[Dict[str, Any]]:
        """Get stored crash reports."""
        return self._load_crashes()

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get a summary of collected statistics."""
        events = self._load_events()
        crashes = self._load_crashes()

        return {
            "total_events": len(events),
            "total_crashes": len(crashes),
            "event_types": self._count_by_key(events, "event_type"),
            "features_used": self._count_by_key(
                [e for e in events if e.get("event_type") == "feature"], "feature_name"
            ),
            "oldest_event": events[0]["timestamp"] if events else None,
            "newest_event": events[-1]["timestamp"] if events else None,
        }

    def clear_all(self):
        """Delete all stored analytics data."""
        with self._lock:
            if self._events_file.exists():
                self._events_file.unlink()
            if self._crashes_file.exists():
                self._crashes_file.unlink()
            if self._stats_file.exists():
                self._stats_file.unlink()

    def export_data(self) -> Dict[str, Any]:
        """Export all stored data for user review."""
        return {
            "events": self._load_events(),
            "crashes": self._load_crashes(),
            "exported_at": datetime.now().isoformat(),
        }

    def _load_events(self) -> List[Dict[str, Any]]:
        if self._events_file.exists():
            try:
                with open(self._events_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_events(self, events: List[Dict[str, Any]]):
        with open(self._events_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)

    def _load_crashes(self) -> List[Dict[str, Any]]:
        if self._crashes_file.exists():
            try:
                with open(self._crashes_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_crashes(self, crashes: List[Dict[str, Any]]):
        with open(self._crashes_file, "w", encoding="utf-8") as f:
            json.dump(crashes, f, indent=2)

    @staticmethod
    def _count_by_key(items: List[Dict], key: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in items:
            value = item.get(key, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# =============================================================================
# Analytics Manager
# =============================================================================


class AnalyticsManager:
    """
    Main analytics manager with privacy-first design.

    All analytics are:
    - Opt-in only (disabled by default)
    - Stored locally first
    - Viewable by the user before submission
    - Deletable at any time
    """

    # Submission endpoint (placeholder - would be ACB's analytics server)
    ANALYTICS_ENDPOINT = "https://analytics.acb.org/v1/events"

    def __init__(
        self,
        app_version: str,
        settings: Optional[AnalyticsSettings] = None,
        storage_path: Optional[Path] = None,
    ):
        self.app_version = app_version
        self.settings = settings or AnalyticsSettings()
        self.store = LocalAnalyticsStore(storage_path)

        self._session_id = str(uuid.uuid4())
        self._session_start = datetime.now()
        self._feature_timers: Dict[str, float] = {}

    # -------------------------------------------------------------------------
    # Consent Management
    # -------------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Check if analytics are enabled."""
        return self.settings.analytics_enabled

    def get_consent_level(self) -> ConsentLevel:
        """Get current consent level."""
        try:
            return ConsentLevel(self.settings.consent_level)
        except ValueError:
            return ConsentLevel.NONE

    def set_consent(self, level: ConsentLevel):
        """Set analytics consent level."""
        self.settings.grant_consent(level)
        logger.info(f"Analytics consent set to: {level.value}")

    def revoke_consent(self):
        """Revoke all analytics consent and optionally clear data."""
        self.settings.revoke_consent()
        logger.info("Analytics consent revoked")

    # -------------------------------------------------------------------------
    # Event Tracking
    # -------------------------------------------------------------------------

    def track_usage(
        self, action: str, category: str = "", label: str = "", value: Optional[int] = None
    ):
        """Track a usage event (requires standard or full consent)."""
        if not self.settings.usage_statistics:
            return

        event = UsageEvent(
            action=action,
            category=category,
            label=label,
            value=value,
            session_id=self._session_id,
        )
        self.store.store_event(event)

    def track_feature(self, feature_name: str, category: str = ""):
        """Track feature usage (requires standard or full consent)."""
        if not self.settings.feature_tracking:
            return

        event = FeatureEvent(
            feature_name=feature_name,
            feature_category=category,
            session_id=self._session_id,
        )
        self.store.store_event(event)

    def start_feature_timer(self, feature_name: str):
        """Start timing feature usage."""
        if not self.settings.feature_tracking:
            return
        self._feature_timers[feature_name] = time.time()

    def end_feature_timer(self, feature_name: str, category: str = ""):
        """End feature timing and record duration."""
        if not self.settings.feature_tracking:
            return

        start_time = self._feature_timers.pop(feature_name, None)
        if start_time:
            duration = time.time() - start_time
            event = FeatureEvent(
                feature_name=feature_name,
                feature_category=category,
                duration_seconds=round(duration, 2),
                session_id=self._session_id,
            )
            self.store.store_event(event)

    def track_performance(self, metric_name: str, metric_value: float, metric_unit: str = "ms"):
        """Track a performance metric (requires full consent)."""
        if not self.settings.performance_monitoring:
            return

        event = PerformanceEvent(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            session_id=self._session_id,
        )
        self.store.store_event(event)

    def track_crash(self, error: Exception, context: str = ""):
        """Track a crash or unhandled exception (requires basic+ consent)."""
        if not self.settings.crash_reporting:
            return

        # Sanitize stack trace (remove file paths that might contain usernames)
        stack = traceback.format_exc()
        sanitized_stack = self._sanitize_stack_trace(stack)

        os_info = ""
        if self.settings.include_system_info:
            os_info = f"{platform.system()} {platform.release()}"

        crash = CrashEvent(
            error_type=type(error).__name__,
            error_message=str(error)[:500],  # Truncate long messages
            stack_trace=sanitized_stack,
            app_version=self.app_version if self.settings.include_app_version else "",
            os_info=os_info,
            session_id=self._session_id,
        )
        self.store.store_crash(crash)
        logger.info(f"Crash recorded: {type(error).__name__}")

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    def start_session(self):
        """Record session start."""
        self._session_id = str(uuid.uuid4())
        self._session_start = datetime.now()

        self.track_usage(
            action="session_start",
            category="app",
        )

    def end_session(self):
        """Record session end with duration."""
        duration = (datetime.now() - self._session_start).total_seconds()

        self.track_usage(
            action="session_end",
            category="app",
            value=int(duration),
        )

    # -------------------------------------------------------------------------
    # Data Access and Export
    # -------------------------------------------------------------------------

    def get_collected_data(self) -> Dict[str, Any]:
        """Get all collected data for user review."""
        return self.store.export_data()

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary of collected statistics."""
        return self.store.get_statistics_summary()

    def clear_all_data(self):
        """Delete all collected analytics data."""
        self.store.clear_all()
        logger.info("All analytics data cleared")

    def export_to_file(self, filepath: Path) -> bool:
        """Export collected data to a JSON file for user review."""
        try:
            data = self.get_collected_data()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return False

    # -------------------------------------------------------------------------
    # Data Submission (Optional)
    # -------------------------------------------------------------------------

    def submit_data(self, callback: Optional[Callable[[bool, str], None]] = None):
        """
        Submit collected data to analytics server.

        This is entirely optional and only happens when explicitly
        requested by the user.
        """
        if not self.is_enabled():
            if callback:
                callback(False, "Analytics not enabled")
            return

        if not HAS_REQUESTS:
            if callback:
                callback(False, "Network library not available")
            return

        def _submit():
            try:
                data = self._prepare_submission()

                response = requests.post(
                    self.ANALYTICS_ENDPOINT,
                    json=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": f"ACBLink/{self.app_version}",
                    },
                    timeout=30,
                )

                if response.ok:
                    # Clear submitted data
                    self.store.clear_all()
                    if callback:
                        callback(True, "Data submitted successfully")
                else:
                    if callback:
                        callback(False, f"Server error: {response.status_code}")

            except Exception as e:
                logger.error(f"Analytics submission failed: {e}")
                if callback:
                    callback(False, str(e))

        # Run in background thread
        thread = threading.Thread(target=_submit, daemon=True)
        thread.start()

    def _prepare_submission(self) -> Dict[str, Any]:
        """Prepare data for submission with anonymization."""
        data = self.store.export_data()

        # Add metadata
        data["anonymous_id"] = self.settings.anonymous_id
        data["consent_level"] = self.settings.consent_level
        data["app_version"] = self.app_version if self.settings.include_app_version else None

        return data

    @staticmethod
    def _sanitize_stack_trace(stack: str) -> str:
        """Remove potentially identifying information from stack traces."""
        lines = stack.split("\n")
        sanitized = []

        for line in lines:
            # Replace user paths with generic placeholder
            if "Users/" in line or "home/" in line:
                # Keep only the relative path from the project
                if "acb_link" in line:
                    idx = line.find("acb_link")
                    line = '  File ".../' + line[idx:]
            sanitized.append(line)

        return "\n".join(sanitized)


# =============================================================================
# Global Instance
# =============================================================================

_analytics_manager: Optional[AnalyticsManager] = None


def get_analytics_manager(
    app_version: str = "2.0.0", settings: Optional[AnalyticsSettings] = None
) -> AnalyticsManager:
    """Get or create the global analytics manager."""
    global _analytics_manager
    if _analytics_manager is None:
        _analytics_manager = AnalyticsManager(app_version, settings)
    return _analytics_manager


def track_usage(action: str, category: str = "", label: str = "", value: Optional[int] = None):
    """Convenience function for tracking usage."""
    if _analytics_manager:
        _analytics_manager.track_usage(action, category, label, value)


def track_feature(feature_name: str, category: str = ""):
    """Convenience function for tracking feature usage."""
    if _analytics_manager:
        _analytics_manager.track_feature(feature_name, category)


def track_crash(error: Exception, context: str = ""):
    """Convenience function for tracking crashes."""
    if _analytics_manager:
        _analytics_manager.track_crash(error, context)


def track_performance(metric_name: str, metric_value: float, metric_unit: str = "ms"):
    """Convenience function for tracking performance."""
    if _analytics_manager:
        _analytics_manager.track_performance(metric_name, metric_value, metric_unit)


# =============================================================================
# Exception Handler Integration
# =============================================================================


def install_crash_handler():
    """Install global exception handler for crash reporting."""
    import sys

    original_excepthook = sys.excepthook

    def crash_handler(exc_type, exc_value, exc_traceback):
        # Log the crash
        if _analytics_manager and _analytics_manager.settings.crash_reporting:
            _analytics_manager.track_crash(exc_value)

        # Call original handler
        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = crash_handler
    logger.info("Crash handler installed")
