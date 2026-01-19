"""
ACB Link - Scheduled Recording System
Record streams at specified times with presets and queue management.
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Callable
from enum import Enum
import time

from .utils import get_app_data_dir, get_recordings_dir, sanitize_filename


class RecordingStatus(Enum):
    """Recording status states."""
    SCHEDULED = "scheduled"
    RECORDING = "recording"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecurrenceType(Enum):
    """Recurrence options for scheduled recordings."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"


@dataclass
class RecordingPreset:
    """Predefined recording settings."""
    id: str
    name: str
    format: str = "mp3"  # mp3, wav, ogg
    bitrate: int = 128  # kbps
    split_interval: int = 0  # minutes, 0 = no split
    output_folder: str = ""
    auto_metadata: bool = True
    
    def __post_init__(self):
        if not self.output_folder:
            self.output_folder = str(get_recordings_dir())


@dataclass
class ScheduledRecording:
    """Represents a scheduled recording."""
    id: str
    name: str
    stream_name: str
    stream_url: str
    station_id: str = ""
    # Timing
    start_time: str = ""  # ISO format
    duration_minutes: int = 60
    recurrence: RecurrenceType = RecurrenceType.ONCE
    # Settings
    preset_id: str = ""
    format: str = "mp3"
    bitrate: int = 128
    output_path: str = ""
    # State
    status: RecordingStatus = RecordingStatus.SCHEDULED
    last_run: str = ""
    next_run: str = ""
    error_message: str = ""
    # Created info
    created_date: str = ""
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        if not self.next_run and self.start_time:
            self.next_run = self.start_time


@dataclass
class RecordingQueueItem:
    """Item in the recording queue."""
    id: str
    scheduled_recording_id: str
    stream_name: str
    stream_url: str
    start_time: datetime
    end_time: datetime
    output_path: str
    format: str
    bitrate: int
    status: RecordingStatus = RecordingStatus.SCHEDULED


class StreamRecorderEngine:
    """
    Engine for recording audio streams.
    """
    
    def __init__(self):
        self._current_recording: Optional[RecordingQueueItem] = None
        self._stop_event = threading.Event()
        self._recording_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_recording_start: Optional[Callable[[RecordingQueueItem], None]] = None
        self.on_recording_progress: Optional[Callable[[RecordingQueueItem, int, int], None]] = None
        self.on_recording_complete: Optional[Callable[[RecordingQueueItem, str], None]] = None
        self.on_recording_error: Optional[Callable[[RecordingQueueItem, str], None]] = None
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._current_recording is not None and not self._stop_event.is_set()
    
    @property
    def current_recording(self) -> Optional[RecordingQueueItem]:
        """Get current recording item."""
        return self._current_recording
    
    def start_recording(self, item: RecordingQueueItem) -> bool:
        """Start a recording."""
        if self.is_recording:
            return False
        
        self._stop_event.clear()
        self._current_recording = item
        
        self._recording_thread = threading.Thread(
            target=self._record_thread,
            args=(item,),
            daemon=True,
            name=f"Recording-{item.id}"
        )
        self._recording_thread.start()
        
        if self.on_recording_start:
            self.on_recording_start(item)
        
        return True
    
    def stop_recording(self):
        """Stop current recording."""
        if not self.is_recording:
            return
        
        self._stop_event.set()
        
        if self._recording_thread:
            self._recording_thread.join(timeout=5.0)
        
        self._current_recording = None
    
    def _record_thread(self, item: RecordingQueueItem):
        """Recording thread."""
        try:
            import requests
            
            # Ensure output directory exists
            Path(item.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate duration
            duration_secs = (item.end_time - item.start_time).total_seconds()
            start_time = time.time()
            
            # Stream and save
            with requests.get(item.stream_url, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                with open(item.output_path, 'wb') as f:
                    bytes_written = 0
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            break
                        
                        # Check if duration exceeded
                        elapsed = time.time() - start_time
                        if elapsed >= duration_secs:
                            break
                        
                        if chunk:
                            f.write(chunk)
                            bytes_written += len(chunk)
                            
                            # Progress callback
                            if self.on_recording_progress:
                                progress_pct = int((elapsed / duration_secs) * 100)
                                self.on_recording_progress(item, progress_pct, bytes_written)
            
            item.status = RecordingStatus.COMPLETED
            
            if self.on_recording_complete:
                self.on_recording_complete(item, item.output_path)
                
        except Exception as e:
            item.status = RecordingStatus.FAILED
            
            if self.on_recording_error:
                self.on_recording_error(item, str(e))
        finally:
            self._current_recording = None


class ScheduledRecordingManager:
    """
    Manages scheduled recordings with support for presets and recurrence.
    """
    
    def __init__(self):
        self._data_file = get_app_data_dir() / "scheduled_recordings.json"
        self._presets_file = get_app_data_dir() / "recording_presets.json"
        
        self.scheduled_recordings: Dict[str, ScheduledRecording] = {}
        self.presets: Dict[str, RecordingPreset] = {}
        self.queue: List[RecordingQueueItem] = []
        
        self.recorder = StreamRecorderEngine()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_scheduler = threading.Event()
        
        # Callbacks
        self.on_recording_start: Optional[Callable[[ScheduledRecording], None]] = None
        self.on_recording_complete: Optional[Callable[[ScheduledRecording, str], None]] = None
        self.on_recording_error: Optional[Callable[[ScheduledRecording, str], None]] = None
        
        self._load()
        self._ensure_default_presets()
    
    def _load(self):
        """Load data from disk."""
        # Load recordings
        if self._data_file.exists():
            try:
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for rec_data in data.get('recordings', []):
                    rec_data['status'] = RecordingStatus(rec_data.get('status', 'scheduled'))
                    rec_data['recurrence'] = RecurrenceType(rec_data.get('recurrence', 'once'))
                    rec = ScheduledRecording(**rec_data)
                    self.scheduled_recordings[rec.id] = rec
            except Exception:
                pass
        
        # Load presets
        if self._presets_file.exists():
            try:
                with open(self._presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for preset_data in data.get('presets', []):
                    preset = RecordingPreset(**preset_data)
                    self.presets[preset.id] = preset
            except Exception:
                pass
    
    def _save(self):
        """Save data to disk."""
        try:
            # Save recordings
            data = {
                'recordings': [
                    {
                        **asdict(rec),
                        'status': rec.status.value,
                        'recurrence': rec.recurrence.value
                    }
                    for rec in self.scheduled_recordings.values()
                ]
            }
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Save presets
            preset_data = {
                'presets': [asdict(p) for p in self.presets.values()]
            }
            with open(self._presets_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2)
        except Exception:
            pass
    
    def _ensure_default_presets(self):
        """Create default recording presets."""
        defaults = [
            ("standard", "Standard Quality", "mp3", 128),
            ("high", "High Quality", "mp3", 320),
            ("voice", "Voice/Speech", "mp3", 64),
            ("lossless", "Lossless (WAV)", "wav", 0),
        ]
        
        for preset_id, name, fmt, bitrate in defaults:
            if preset_id not in self.presets:
                self.presets[preset_id] = RecordingPreset(
                    id=preset_id,
                    name=name,
                    format=fmt,
                    bitrate=bitrate
                )
        self._save()
    
    # Preset Management
    
    def create_preset(
        self,
        name: str,
        format: str = "mp3",
        bitrate: int = 128,
        split_interval: int = 0,
        output_folder: str = ""
    ) -> RecordingPreset:
        """Create a new recording preset."""
        import uuid
        preset_id = uuid.uuid4().hex[:8]
        
        preset = RecordingPreset(
            id=preset_id,
            name=name,
            format=format,
            bitrate=bitrate,
            split_interval=split_interval,
            output_folder=output_folder or str(get_recordings_dir())
        )
        self.presets[preset_id] = preset
        self._save()
        return preset
    
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset."""
        # Don't delete default presets
        if preset_id in ["standard", "high", "voice", "lossless"]:
            return False
        
        if preset_id in self.presets:
            del self.presets[preset_id]
            self._save()
            return True
        return False
    
    def get_preset(self, preset_id: str) -> Optional[RecordingPreset]:
        """Get a preset by ID."""
        return self.presets.get(preset_id)
    
    def get_all_presets(self) -> List[RecordingPreset]:
        """Get all presets."""
        return list(self.presets.values())
    
    # Scheduled Recording Management
    
    def schedule_recording(
        self,
        name: str,
        stream_name: str,
        stream_url: str,
        start_time: datetime,
        duration_minutes: int = 60,
        recurrence: RecurrenceType = RecurrenceType.ONCE,
        preset_id: str = "standard",
        station_id: str = ""
    ) -> ScheduledRecording:
        """Schedule a new recording."""
        import uuid
        rec_id = uuid.uuid4().hex[:12]
        
        preset = self.presets.get(preset_id, self.presets.get("standard"))
        
        # Generate output path
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(stream_name)}_{timestamp}.{preset.format}"  # type: ignore[union-attr]
        output_path = str(Path(preset.output_folder) / filename)  # type: ignore[union-attr]
        
        recording = ScheduledRecording(
            id=rec_id,
            name=name,
            stream_name=stream_name,
            stream_url=stream_url,
            station_id=station_id,
            start_time=start_time.isoformat(),
            duration_minutes=duration_minutes,
            recurrence=recurrence,
            preset_id=preset_id,
            format=preset.format,  # type: ignore[union-attr]
            bitrate=preset.bitrate,  # type: ignore[union-attr]
            output_path=output_path,
            next_run=start_time.isoformat()
        )
        
        self.scheduled_recordings[rec_id] = recording
        self._save()
        
        return recording
    
    def cancel_recording(self, recording_id: str) -> bool:
        """Cancel a scheduled recording."""
        if recording_id in self.scheduled_recordings:
            recording = self.scheduled_recordings[recording_id]
            recording.status = RecordingStatus.CANCELLED
            self._save()
            return True
        return False
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete a scheduled recording."""
        if recording_id in self.scheduled_recordings:
            del self.scheduled_recordings[recording_id]
            self._save()
            return True
        return False
    
    def get_recording(self, recording_id: str) -> Optional[ScheduledRecording]:
        """Get a recording by ID."""
        return self.scheduled_recordings.get(recording_id)
    
    def get_upcoming_recordings(self) -> List[ScheduledRecording]:
        """Get all upcoming recordings."""
        now = datetime.now()
        return sorted(
            [
                r for r in self.scheduled_recordings.values()
                if r.status == RecordingStatus.SCHEDULED and 
                   r.next_run and datetime.fromisoformat(r.next_run) > now
            ],
            key=lambda r: r.next_run
        )
    
    def get_all_recordings(self) -> List[ScheduledRecording]:
        """Get all scheduled recordings."""
        return list(self.scheduled_recordings.values())
    
    def get_recording_history(self) -> List[ScheduledRecording]:
        """Get completed/failed recordings."""
        return [
            r for r in self.scheduled_recordings.values()
            if r.status in [RecordingStatus.COMPLETED, RecordingStatus.FAILED]
        ]
    
    # Scheduler
    
    def start_scheduler(self):
        """Start the recording scheduler."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        
        self._stop_scheduler.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="RecordingScheduler"
        )
        self._scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the recording scheduler."""
        self._stop_scheduler.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while not self._stop_scheduler.is_set():
            try:
                self._check_scheduled_recordings()
            except Exception:
                pass
            
            # Check every 30 seconds
            self._stop_scheduler.wait(30)
    
    def _check_scheduled_recordings(self):
        """Check for recordings that should start."""
        now = datetime.now()
        
        for recording in self.scheduled_recordings.values():
            if recording.status != RecordingStatus.SCHEDULED:
                continue
            
            if not recording.next_run:
                continue
            
            next_run = datetime.fromisoformat(recording.next_run)
            
            # Check if it's time to start (within 1 minute window)
            if now >= next_run and now <= next_run + timedelta(minutes=1):
                self._start_scheduled_recording(recording)
    
    def _start_scheduled_recording(self, recording: ScheduledRecording):
        """Start a scheduled recording."""
        # Create queue item
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=recording.duration_minutes)
        
        queue_item = RecordingQueueItem(
            id=f"q_{recording.id}_{start_time.strftime('%Y%m%d%H%M%S')}",
            scheduled_recording_id=recording.id,
            stream_name=recording.stream_name,
            stream_url=recording.stream_url,
            start_time=start_time,
            end_time=end_time,
            output_path=recording.output_path,
            format=recording.format,
            bitrate=recording.bitrate
        )
        
        # Update recording status
        recording.status = RecordingStatus.RECORDING
        recording.last_run = start_time.isoformat()
        
        # Calculate next run for recurring recordings
        if recording.recurrence != RecurrenceType.ONCE:
            recording.next_run = self._calculate_next_run(recording).isoformat()
            recording.status = RecordingStatus.SCHEDULED
        
        self._save()
        
        # Set up callbacks
        def on_complete(item, path):
            recording.status = RecordingStatus.COMPLETED
            self._save()
            if self.on_recording_complete:
                self.on_recording_complete(recording, path)
        
        def on_error(item, error):
            recording.status = RecordingStatus.FAILED
            recording.error_message = error
            self._save()
            if self.on_recording_error:
                self.on_recording_error(recording, error)
        
        self.recorder.on_recording_complete = on_complete
        self.recorder.on_recording_error = on_error
        
        # Start recording
        self.recorder.start_recording(queue_item)
        
        if self.on_recording_start:
            self.on_recording_start(recording)
    
    def _calculate_next_run(self, recording: ScheduledRecording) -> datetime:
        """Calculate next run time for recurring recording."""
        current = datetime.fromisoformat(recording.start_time)
        now = datetime.now()
        
        while current <= now:
            if recording.recurrence == RecurrenceType.DAILY:
                current += timedelta(days=1)
            elif recording.recurrence == RecurrenceType.WEEKLY:
                current += timedelta(weeks=1)
            elif recording.recurrence == RecurrenceType.WEEKDAYS:
                current += timedelta(days=1)
                while current.weekday() >= 5:  # Skip weekends
                    current += timedelta(days=1)
            elif recording.recurrence == RecurrenceType.WEEKENDS:
                current += timedelta(days=1)
                while current.weekday() < 5:  # Skip weekdays
                    current += timedelta(days=1)
            else:
                break
        
        return current
    
    # Recording Queue
    
    def add_to_queue(
        self,
        stream_name: str,
        stream_url: str,
        duration_minutes: int = 60,
        preset_id: str = "standard"
    ) -> RecordingQueueItem:
        """Add an immediate recording to the queue."""
        import uuid
        
        preset = self.presets.get(preset_id, self.presets.get("standard"))
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(stream_name)}_{timestamp}.{preset.format}"  # type: ignore[union-attr]
        output_path = str(Path(preset.output_folder) / filename)  # type: ignore[union-attr]
        
        item = RecordingQueueItem(
            id=uuid.uuid4().hex[:12],
            scheduled_recording_id="",
            stream_name=stream_name,
            stream_url=stream_url,
            start_time=start_time,
            end_time=end_time,
            output_path=output_path,
            format=preset.format,  # type: ignore[union-attr]
            bitrate=preset.bitrate  # type: ignore[union-attr]
        )
        
        self.queue.append(item)
        return item
    
    def start_next_in_queue(self) -> bool:
        """Start the next recording in queue."""
        if not self.queue:
            return False
        
        if self.recorder.is_recording:
            return False
        
        item = self.queue.pop(0)
        return self.recorder.start_recording(item)
    
    def clear_queue(self):
        """Clear the recording queue."""
        self.queue.clear()
