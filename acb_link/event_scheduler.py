"""
ACB Link - Event Scheduler Module
Schedule recordings and alerts for ACB calendar events.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertType(Enum):
    """Types of event alerts."""

    NOTIFICATION = "notification"
    SOUND = "sound"
    VOICE = "voice"
    ALL = "all"


class EventAction(Enum):
    """Actions to take for scheduled events."""

    ALERT_ONLY = "alert_only"
    AUTO_TUNE = "auto_tune"
    AUTO_RECORD = "auto_record"
    TUNE_AND_RECORD = "tune_and_record"


@dataclass
class ScheduledEvent:
    """A scheduled event from the ACB calendar."""

    id: str
    calendar_event_id: str
    title: str
    description: str
    start_time: datetime
    end_time: Optional[datetime]
    stream_url: Optional[str]
    stream_name: Optional[str]

    # User configuration
    alert_enabled: bool = True
    alert_minutes_before: int = 15
    alert_type: AlertType = AlertType.NOTIFICATION
    action: EventAction = EventAction.ALERT_ONLY

    # Recording settings
    record_enabled: bool = False
    recording_format: str = "mp3"
    recording_quality: int = 128

    # Recurrence
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly

    # State
    alert_sent: bool = False
    action_executed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "id": self.id,
            "calendar_event_id": self.calendar_event_id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "stream_url": self.stream_url,
            "stream_name": self.stream_name,
            "alert_enabled": self.alert_enabled,
            "alert_minutes_before": self.alert_minutes_before,
            "alert_type": self.alert_type.value,
            "action": self.action.value,
            "record_enabled": self.record_enabled,
            "recording_format": self.recording_format,
            "recording_quality": self.recording_quality,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "alert_sent": self.alert_sent,
            "action_executed": self.action_executed,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledEvent":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            calendar_event_id=data["calendar_event_id"],
            title=data["title"],
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            stream_url=data.get("stream_url"),
            stream_name=data.get("stream_name"),
            alert_enabled=data.get("alert_enabled", True),
            alert_minutes_before=data.get("alert_minutes_before", 15),
            alert_type=AlertType(data.get("alert_type", "notification")),
            action=EventAction(data.get("action", "alert_only")),
            record_enabled=data.get("record_enabled", False),
            recording_format=data.get("recording_format", "mp3"),
            recording_quality=data.get("recording_quality", 128),
            is_recurring=data.get("is_recurring", False),
            recurrence_pattern=data.get("recurrence_pattern"),
            alert_sent=data.get("alert_sent", False),
            action_executed=data.get("action_executed", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )


@dataclass
class HomePageAlert:
    """Alert to show on home page."""

    event: ScheduledEvent
    message: str
    time_until: str
    is_live: bool
    priority: int  # Higher = more important


class EventScheduler:
    """
    Manages scheduled events from ACB calendar.
    Provides alerts and automated actions.
    """

    def __init__(
        self,
        data_path: Optional[str] = None,
        on_alert: Optional[Callable[[ScheduledEvent], None]] = None,
        on_auto_tune: Optional[Callable[[str, str], None]] = None,
        on_auto_record: Optional[Callable[[ScheduledEvent], None]] = None,
    ):
        self.data_path = data_path or self._default_data_path()
        self.on_alert = on_alert
        self.on_auto_tune = on_auto_tune
        self.on_auto_record = on_auto_record

        self.scheduled_events: Dict[str, ScheduledEvent] = {}
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._check_interval = 30  # seconds

        self._load_data()

    def _default_data_path(self) -> str:
        """Get default data path."""
        home = os.path.expanduser("~")
        return os.path.join(home, ".acb_link", "scheduled_events.json")

    def _load_data(self):
        """Load scheduled events from disk."""
        if not os.path.exists(self.data_path):
            return

        try:
            with open(self.data_path, "r") as f:
                data = json.load(f)

            for event_data in data.get("events", []):
                event = ScheduledEvent.from_dict(event_data)
                self.scheduled_events[event.id] = event

        except Exception:
            pass

    def save(self):
        """Save scheduled events to disk."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        data = {"events": [e.to_dict() for e in self.scheduled_events.values()]}

        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def start(self):
        """Start the event checker."""
        if self._running:
            return

        self._running = True
        self._check_thread = threading.Thread(
            target=self._check_loop, daemon=True, name="EventScheduler"
        )
        self._check_thread.start()

    def stop(self):
        """Stop the event checker."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=2.0)

    def _check_loop(self):
        """Background loop to check for upcoming events."""
        import time

        while self._running:
            self._check_events()
            time.sleep(self._check_interval)

    def _check_events(self):
        """Check for events that need alerts or actions."""
        now = datetime.now()

        for event in self.scheduled_events.values():
            # Skip past events
            if event.start_time < now and not event.is_recurring:
                continue

            # Check for alert
            if event.alert_enabled and not event.alert_sent:
                alert_time = event.start_time - timedelta(minutes=event.alert_minutes_before)
                if now >= alert_time and now < event.start_time:
                    self._send_alert(event)

            # Check for action execution
            if not event.action_executed:
                # Actions trigger at event start time
                if now >= event.start_time:
                    self._execute_action(event)

    def _send_alert(self, event: ScheduledEvent):
        """Send alert for an event."""
        event.alert_sent = True
        self.save()

        if self.on_alert:
            self.on_alert(event)

    def _execute_action(self, event: ScheduledEvent):
        """Execute the scheduled action for an event."""
        event.action_executed = True
        self.save()

        if event.action == EventAction.AUTO_TUNE:
            if self.on_auto_tune and event.stream_url:
                self.on_auto_tune(event.stream_name or "Event Stream", event.stream_url)

        elif event.action == EventAction.AUTO_RECORD:
            if self.on_auto_record:
                self.on_auto_record(event)

        elif event.action == EventAction.TUNE_AND_RECORD:
            if self.on_auto_tune and event.stream_url:
                self.on_auto_tune(event.stream_name or "Event Stream", event.stream_url)
            if self.on_auto_record:
                self.on_auto_record(event)

    def schedule_event(
        self,
        calendar_event,  # CalendarEvent from calendar_integration
        alert_minutes_before: int = 15,
        alert_type: AlertType = AlertType.NOTIFICATION,
        action: EventAction = EventAction.ALERT_ONLY,
        record_enabled: bool = False,
    ) -> ScheduledEvent:
        """
        Schedule an event from the ACB calendar.

        Args:
            calendar_event: Event from CalendarManager
            alert_minutes_before: Minutes before to send alert
            alert_type: Type of alert
            action: Action to take at event time
            record_enabled: Whether to record the event

        Returns:
            The scheduled event
        """
        scheduled = ScheduledEvent(
            id=str(uuid.uuid4()),
            calendar_event_id=calendar_event.id,
            title=calendar_event.title,
            description=calendar_event.description or "",
            start_time=calendar_event.start_time,
            end_time=calendar_event.end_time,
            stream_url=calendar_event.stream_url,
            stream_name=getattr(calendar_event, "stream_name", None),
            alert_enabled=True,
            alert_minutes_before=alert_minutes_before,
            alert_type=alert_type,
            action=action,
            record_enabled=record_enabled,
        )

        self.scheduled_events[scheduled.id] = scheduled
        self.save()

        return scheduled

    def remove_scheduled_event(self, event_id: str):
        """Remove a scheduled event."""
        if event_id in self.scheduled_events:
            del self.scheduled_events[event_id]
            self.save()

    def update_scheduled_event(self, event_id: str, **kwargs) -> Optional[ScheduledEvent]:
        """Update a scheduled event."""
        if event_id not in self.scheduled_events:
            return None

        event = self.scheduled_events[event_id]

        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)

        self.save()
        return event

    def get_upcoming_alerts(self, hours: int = 24) -> List[HomePageAlert]:
        """
        Get upcoming alerts for home page display.

        Args:
            hours: Number of hours to look ahead

        Returns:
            List of alerts sorted by time
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        alerts = []

        for event in self.scheduled_events.values():
            # Skip past events
            if event.start_time < now:
                continue

            # Skip events too far in the future
            if event.start_time > cutoff:
                continue

            # Calculate time until
            delta = event.start_time - now
            if delta.total_seconds() < 3600:
                time_until = f"{int(delta.total_seconds() / 60)} minutes"
            elif delta.total_seconds() < 86400:
                hours_until = int(delta.total_seconds() / 3600)
                time_until = f"{hours_until} hour{'s' if hours_until != 1 else ''}"
            else:
                days_until = int(delta.total_seconds() / 86400)
                time_until = f"{days_until} day{'s' if days_until != 1 else ''}"

            # Check if live
            is_live = event.start_time <= now
            if event.end_time:
                is_live = event.start_time <= now <= event.end_time

            # Create message
            if is_live:
                message = f"🔴 LIVE NOW: {event.title}"
                priority = 100
            elif delta.total_seconds() < 900:  # 15 minutes
                message = f"⏰ Starting soon: {event.title}"
                priority = 90
            elif delta.total_seconds() < 3600:  # 1 hour
                message = f"📅 Coming up: {event.title}"
                priority = 70
            else:
                message = f"📆 Scheduled: {event.title}"
                priority = 50

            alerts.append(
                HomePageAlert(
                    event=event,
                    message=message,
                    time_until=time_until,
                    is_live=is_live,
                    priority=priority,
                )
            )

        # Sort by priority (highest first), then by time
        alerts.sort(key=lambda a: (-a.priority, a.event.start_time))

        return alerts

    def get_all_scheduled(self) -> List[ScheduledEvent]:
        """Get all scheduled events."""
        return sorted(self.scheduled_events.values(), key=lambda e: e.start_time)

    def get_events_for_date(self, date: datetime) -> List[ScheduledEvent]:
        """Get events scheduled for a specific date."""
        return [e for e in self.scheduled_events.values() if e.start_time.date() == date.date()]

    def clear_past_events(self):
        """Remove past non-recurring events."""
        now = datetime.now()
        to_remove = [
            eid
            for eid, e in self.scheduled_events.items()
            if e.start_time < now and not e.is_recurring
        ]

        for eid in to_remove:
            del self.scheduled_events[eid]

        if to_remove:
            self.save()


class EventSchedulerSettings:
    """Settings for event scheduler on home page."""

    def __init__(self):
        self.show_on_home_page = True
        self.max_alerts_shown = 5
        self.default_alert_minutes = 15
        self.default_alert_type = AlertType.NOTIFICATION
        self.default_action = EventAction.ALERT_ONLY
        self.auto_sync_calendar = True
        self.sync_interval_minutes = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "show_on_home_page": self.show_on_home_page,
            "max_alerts_shown": self.max_alerts_shown,
            "default_alert_minutes": self.default_alert_minutes,
            "default_alert_type": self.default_alert_type.value,
            "default_action": self.default_action.value,
            "auto_sync_calendar": self.auto_sync_calendar,
            "sync_interval_minutes": self.sync_interval_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventSchedulerSettings":
        settings = cls()
        settings.show_on_home_page = data.get("show_on_home_page", True)
        settings.max_alerts_shown = data.get("max_alerts_shown", 5)
        settings.default_alert_minutes = data.get("default_alert_minutes", 15)
        settings.default_alert_type = AlertType(data.get("default_alert_type", "notification"))
        settings.default_action = EventAction(data.get("default_action", "alert_only"))
        settings.auto_sync_calendar = data.get("auto_sync_calendar", True)
        settings.sync_interval_minutes = data.get("sync_interval_minutes", 30)
        return settings
