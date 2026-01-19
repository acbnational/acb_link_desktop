"""
ACB Link - ACB Calendar Integration
Display ACB events, reminders, and quick event access.
"""

import json
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Callable

try:
    import requests  # noqa: F401
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .utils import get_app_data_dir


@dataclass
class CalendarEvent:
    """Represents an ACB calendar event."""
    id: str
    title: str
    description: str = ""
    start_time: str = ""  # ISO format
    end_time: str = ""
    location: str = ""
    event_type: str = ""  # meeting, webinar, broadcast, convention
    url: str = ""  # Join URL or event page
    stream_url: str = ""  # If it's a streaming event
    is_recurring: bool = False
    recurrence_info: str = ""
    reminder_set: bool = False
    reminder_minutes: int = 15
    
    @property
    def start_datetime(self) -> Optional[datetime]:
        """Get start time as datetime."""
        if self.start_time:
            try:
                return datetime.fromisoformat(self.start_time)
            except ValueError:
                pass
        return None
    
    @property
    def end_datetime(self) -> Optional[datetime]:
        """Get end time as datetime."""
        if self.end_time:
            try:
                return datetime.fromisoformat(self.end_time)
            except ValueError:
                pass
        return None
    
    @property
    def is_live(self) -> bool:
        """Check if event is currently live."""
        now = datetime.now()
        start = self.start_datetime
        end = self.end_datetime
        
        if start and end:
            return start <= now <= end
        elif start:
            # Assume 2 hour duration if no end time
            return start <= now <= start + timedelta(hours=2)
        return False
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming (within next 24 hours)."""
        start = self.start_datetime
        if start:
            now = datetime.now()
            return now < start <= now + timedelta(hours=24)
        return False
    
    def get_time_until(self) -> str:
        """Get formatted time until event starts."""
        start = self.start_datetime
        if not start:
            return ""
        
        now = datetime.now()
        if start <= now:
            return "Live Now" if self.is_live else "Started"
        
        delta = start - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if delta.days > 0:
            return f"In {delta.days} day{'s' if delta.days > 1 else ''}"
        elif hours > 0:
            return f"In {hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"In {minutes} minute{'s' if minutes > 1 else ''}"


class EventReminder:
    """
    Handles event reminders.
    """
    
    def __init__(self):
        self._active_reminders: Dict[str, threading.Timer] = {}
        
        # Callbacks
        self.on_reminder: Optional[Callable[[CalendarEvent], None]] = None
    
    def set_reminder(self, event: CalendarEvent, minutes_before: int = 15):
        """Set a reminder for an event."""
        if not event.start_datetime:
            return
        
        reminder_time = event.start_datetime - timedelta(minutes=minutes_before)
        now = datetime.now()
        
        if reminder_time <= now:
            return  # Already passed
        
        # Cancel existing reminder for this event
        self.cancel_reminder(event.id)
        
        delay = (reminder_time - now).total_seconds()
        
        timer = threading.Timer(
            delay,
            self._fire_reminder,
            args=(event,)
        )
        timer.daemon = True
        timer.start()
        
        self._active_reminders[event.id] = timer
        event.reminder_set = True
        event.reminder_minutes = minutes_before
    
    def cancel_reminder(self, event_id: str):
        """Cancel a reminder."""
        if event_id in self._active_reminders:
            self._active_reminders[event_id].cancel()
            del self._active_reminders[event_id]
    
    def cancel_all(self):
        """Cancel all reminders."""
        for timer in self._active_reminders.values():
            timer.cancel()
        self._active_reminders.clear()
    
    def _fire_reminder(self, event: CalendarEvent):
        """Fire a reminder callback."""
        if event.id in self._active_reminders:
            del self._active_reminders[event.id]
        
        if self.on_reminder:
            self.on_reminder(event)


class CalendarManager:
    """
    Manages ACB calendar events and integration.
    """
    
    # ACB Calendar endpoints (these would be actual ACB URLs)
    CALENDAR_FEED_URL = "https://www.acb.org/calendar/feed"
    ICAL_URL = "https://www.acb.org/calendar/ical"
    
    def __init__(self):
        self._cache_file = get_app_data_dir() / "calendar_cache.json"
        self.events: Dict[str, CalendarEvent] = {}
        self.reminder_manager = EventReminder()
        
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        # Callbacks
        self.on_events_updated: Optional[Callable[[List[CalendarEvent]], None]] = None
        self.on_live_event: Optional[Callable[[CalendarEvent], None]] = None
        self.on_event_starting: Optional[Callable[[CalendarEvent], None]] = None
        
        self._load_cache()
    
    def _load_cache(self):
        """Load cached events."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for event_data in data.get('events', []):
                    event = CalendarEvent(**event_data)
                    self.events[event.id] = event
            except Exception:
                pass
    
    def _save_cache(self):
        """Save events to cache."""
        try:
            data = {
                'events': [asdict(e) for e in self.events.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def refresh_events(
        self,
        on_complete: Optional[Callable[[List[CalendarEvent]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """Refresh events from ACB calendar (async)."""
        thread = threading.Thread(
            target=self._fetch_events,
            args=(on_complete, on_error),
            daemon=True
        )
        thread.start()
    
    def _fetch_events(
        self,
        on_complete: Optional[Callable[[List[CalendarEvent]], None]],
        on_error: Optional[Callable[[str], None]]
    ):
        """Fetch events from calendar feed."""
        if not HAS_REQUESTS:
            if on_error:
                on_error("requests library not installed")
            return
        
        try:
            # In production, this would fetch from actual ACB calendar
            # For now, create sample events
            self._create_sample_events()
            
            self._save_cache()
            
            events = list(self.events.values())
            
            if on_complete:
                on_complete(events)
            
            if self.on_events_updated:
                self.on_events_updated(events)
                
        except Exception as e:
            if on_error:
                on_error(str(e))
    
    def _create_sample_events(self):
        """Create sample events for demonstration."""
        now = datetime.now()
        
        sample_events = [
            CalendarEvent(
                id="evt_001",
                title="ACB Community Call",
                description="Weekly community discussion",
                start_time=(now + timedelta(hours=2)).isoformat(),
                end_time=(now + timedelta(hours=4)).isoformat(),
                event_type="meeting",
                url="https://www.acb.org/community-call",
                stream_url="https://live365.com/station/a50498"
            ),
            CalendarEvent(
                id="evt_002",
                title="Technology Tuesday Webinar",
                description="Learn about the latest accessibility technology",
                start_time=(now + timedelta(days=1, hours=3)).isoformat(),
                end_time=(now + timedelta(days=1, hours=5)).isoformat(),
                event_type="webinar",
                url="https://www.acb.org/tech-tuesday"
            ),
            CalendarEvent(
                id="evt_003",
                title="Main Menu Live Broadcast",
                description="Live call-in show on ACB Media 1",
                start_time=(now + timedelta(hours=5)).isoformat(),
                end_time=(now + timedelta(hours=7)).isoformat(),
                event_type="broadcast",
                stream_url="https://live365.com/station/a11911"
            ),
            CalendarEvent(
                id="evt_004",
                title="Legislative Update Call",
                description="Monthly legislative update and advocacy discussion",
                start_time=(now + timedelta(days=3)).isoformat(),
                end_time=(now + timedelta(days=3, hours=2)).isoformat(),
                event_type="meeting",
                url="https://www.acb.org/legislative"
            ),
            CalendarEvent(
                id="evt_005",
                title="ACB Annual Meeting",
                description="Annual ACB general membership meeting",
                start_time=(now + timedelta(days=180)).isoformat(),
                end_time=(now + timedelta(days=180, hours=3)).isoformat(),
                event_type="meeting",
                url="https://www.acb.org"
            ),
        ]
        
        for event in sample_events:
            self.events[event.id] = event
    
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get event by ID."""
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[CalendarEvent]:
        """Get all events sorted by start time."""
        events = list(self.events.values())
        events.sort(key=lambda e: e.start_time or "")
        return events
    
    def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """Get events in the next N days."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        events = []
        for event in self.events.values():
            start = event.start_datetime
            if start and now <= start <= cutoff:
                events.append(event)
        
        events.sort(key=lambda e: e.start_time or "")
        return events
    
    def get_live_events(self) -> List[CalendarEvent]:
        """Get currently live events."""
        return [e for e in self.events.values() if e.is_live]
    
    def get_today_events(self) -> List[CalendarEvent]:
        """Get today's events."""
        today = datetime.now().date()
        events = []
        
        for event in self.events.values():
            start = event.start_datetime
            if start and start.date() == today:
                events.append(event)
        
        events.sort(key=lambda e: e.start_time or "")
        return events
    
    def get_events_by_type(self, event_type: str) -> List[CalendarEvent]:
        """Get events of a specific type."""
        return [e for e in self.events.values() if e.event_type == event_type]
    
    def set_reminder(self, event_id: str, minutes_before: int = 15):
        """Set a reminder for an event."""
        event = self.events.get(event_id)
        if event:
            self.reminder_manager.set_reminder(event, minutes_before)
            self._save_cache()
    
    def cancel_reminder(self, event_id: str):
        """Cancel a reminder."""
        self.reminder_manager.cancel_reminder(event_id)
        if event_id in self.events:
            self.events[event_id].reminder_set = False
            self._save_cache()
    
    def start_monitoring(self, check_interval: int = 60):
        """Start monitoring for live events."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return
        
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True,
            name="CalendarMonitor"
        )
        self._refresh_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self._stop_refresh.set()
        self.reminder_manager.cancel_all()
    
    def _monitor_loop(self, check_interval: int):
        """Background monitoring loop."""
        notified_live = set()
        notified_starting = set()
        
        while not self._stop_refresh.is_set():
            now = datetime.now()
            
            for event in self.events.values():
                # Check for live events
                if event.is_live and event.id not in notified_live:
                    notified_live.add(event.id)
                    if self.on_live_event:
                        self.on_live_event(event)
                
                # Check for events starting soon (within 5 minutes)
                start = event.start_datetime
                if start:
                    time_until = (start - now).total_seconds()
                    if 0 < time_until <= 300 and event.id not in notified_starting:
                        notified_starting.add(event.id)
                        if self.on_event_starting:
                            self.on_event_starting(event)
            
            self._stop_refresh.wait(check_interval)
    
    def export_to_ical(self, filepath: str) -> bool:
        """Export events to iCal format."""
        try:
            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//ACB Link//Calendar//EN",
            ]
            
            for event in self.events.values():
                start = event.start_datetime
                end = event.end_datetime
                
                if not start:
                    continue
                
                lines.append("BEGIN:VEVENT")
                lines.append(f"UID:{event.id}@acblink")
                lines.append(f"SUMMARY:{event.title}")
                lines.append(f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}")
                
                if end:
                    lines.append(f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}")
                
                if event.description:
                    lines.append(f"DESCRIPTION:{event.description}")
                
                if event.location:
                    lines.append(f"LOCATION:{event.location}")
                
                if event.url:
                    lines.append(f"URL:{event.url}")
                
                lines.append("END:VEVENT")
            
            lines.append("END:VCALENDAR")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\r\n".join(lines))
            
            return True
        except Exception:
            return False


class QuickEventJoin:
    """
    Provides one-click access to join live events.
    """
    
    def __init__(self, calendar_manager: CalendarManager):
        self.calendar = calendar_manager
    
    def get_joinable_events(self) -> List[CalendarEvent]:
        """Get events that can be joined now."""
        events = []
        
        # Live events with URLs
        for event in self.calendar.get_live_events():
            if event.url or event.stream_url:
                events.append(event)
        
        # Events starting in next 15 minutes
        now = datetime.now()
        for event in self.calendar.get_upcoming_events(days=1):
            start = event.start_datetime
            if start and (start - now).total_seconds() <= 900:
                if event.url or event.stream_url:
                    events.append(event)
        
        return events
    
    def join_event(self, event: CalendarEvent) -> str:
        """
        Get the URL to join an event.
        
        Returns:
            URL to open or stream URL to play
        """
        if event.stream_url:
            return event.stream_url
        return event.url
    
    def can_stream(self, event: CalendarEvent) -> bool:
        """Check if event can be streamed in ACB Link."""
        return bool(event.stream_url)
