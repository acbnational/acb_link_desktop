"""
ACB Link - System Scheduler
Platform-independent scheduled task management for recordings and reminders.
Works at the OS level - tasks run even when the application is not running.

Supports:
- Windows Task Scheduler
- macOS launchd
- Linux cron/systemd timers
"""

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class TaskType(Enum):
    """Types of scheduled tasks."""

    RECORDING = "recording"  # Record a stream
    REMINDER = "reminder"  # Show notification
    PODCAST_DOWNLOAD = "download"  # Download podcast episode
    PODCAST_SYNC = "sync"  # Sync podcast feeds


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""

    id: str
    task_type: TaskType
    name: str
    description: str
    scheduled_time: datetime
    repeat_days: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    duration_minutes: Optional[int] = None  # For recordings
    stream_name: Optional[str] = None  # For recordings
    podcast_url: Optional[str] = None  # For downloads
    notification_message: Optional[str] = None  # For reminders
    enabled: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["task_type"] = self.task_type.value
        d["scheduled_time"] = self.scheduled_time.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ScheduledTask":
        """Create from dictionary."""
        d["task_type"] = TaskType(d["task_type"])
        d["scheduled_time"] = datetime.fromisoformat(d["scheduled_time"])
        return cls(**d)


class TaskSchedulerBase:
    """Base class for platform-specific task schedulers."""

    def __init__(self, app_path: Optional[Path] = None):
        """
        Initialize scheduler.

        Args:
            app_path: Path to the ACB Link executable/script
        """
        self.app_path = app_path or self._detect_app_path()
        self.tasks_file = Path.home() / ".acb_link" / "scheduled_tasks.json"
        self._tasks: Dict[str, ScheduledTask] = {}
        self._load_tasks()

    def _detect_app_path(self) -> Path:
        """Detect the path to the application."""
        if getattr(sys, "frozen", False):
            # Running as compiled executable
            return Path(sys.executable)
        else:
            # Running as script
            return Path(sys.argv[0]).resolve()

    def _load_tasks(self):
        """Load tasks from JSON file."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r") as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        self._tasks[task_id] = ScheduledTask.from_dict(task_data)
            except Exception as e:
                print(f"Error loading tasks: {e}")

    def _save_tasks(self):
        """Save tasks to JSON file."""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_file, "w") as f:
            json.dump({tid: task.to_dict() for tid, task in self._tasks.items()}, f, indent=2)

    def create_task(self, task: ScheduledTask) -> bool:
        """
        Create a new scheduled task.

        Args:
            task: Task to schedule

        Returns:
            True if successful
        """
        raise NotImplementedError

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a scheduled task.

        Args:
            task_id: ID of task to delete

        Returns:
            True if successful
        """
        raise NotImplementedError

    def enable_task(self, task_id: str, enabled: bool = True) -> bool:
        """Enable or disable a task."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = enabled
            self._save_tasks()
            return self._update_system_task(task_id)
        return False

    def _update_system_task(self, task_id: str) -> bool:
        """Update the system-level task."""
        raise NotImplementedError

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks."""
        return list(self._tasks.values())

    def get_tasks_by_type(self, task_type: TaskType) -> List[ScheduledTask]:
        """Get tasks of a specific type."""
        return [t for t in self._tasks.values() if t.task_type == task_type]

    def get_upcoming_tasks(self, hours: int = 24) -> List[ScheduledTask]:
        """Get tasks scheduled within the next N hours."""
        cutoff = datetime.now() + timedelta(hours=hours)
        return [t for t in self._tasks.values() if t.enabled and t.scheduled_time <= cutoff]


class WindowsTaskScheduler(TaskSchedulerBase):
    """Windows Task Scheduler implementation using schtasks."""

    TASK_PREFIX = "ACBLink_"

    def create_task(self, task: ScheduledTask) -> bool:
        """Create a Windows scheduled task."""
        task_name = f"{self.TASK_PREFIX}{task.id}"

        # Build command arguments based on task type
        if task.task_type == TaskType.RECORDING:
            args = f'--record "{task.stream_name}" --duration {task.duration_minutes}'
        elif task.task_type == TaskType.REMINDER:
            args = f'--notify "{task.notification_message}"'
        elif task.task_type == TaskType.PODCAST_DOWNLOAD:
            args = f'--download "{task.podcast_url}"'
        elif task.task_type == TaskType.PODCAST_SYNC:
            args = "--sync-podcasts"
        else:
            args = ""

        # Build schtasks command
        cmd = [
            "schtasks",
            "/create",
            "/tn",
            task_name,
            "/tr",
            f'"{self.app_path}" {args}',
            "/sc",
            "once",
            "/st",
            task.scheduled_time.strftime("%H:%M"),
            "/sd",
            task.scheduled_time.strftime("%m/%d/%Y"),
            "/f",  # Force overwrite
            "/rl",
            "limited",  # Run with limited privileges
        ]

        # Add weekly schedule if repeating
        if task.repeat_days:
            days_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}
            days_str = ",".join(days_map[d] for d in task.repeat_days)
            cmd[cmd.index("once")] = "weekly"
            cmd.extend(["/d", days_str])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                ),
            )

            if result.returncode == 0:
                self._tasks[task.id] = task
                self._save_tasks()
                return True
            else:
                print(f"Task creation failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error creating task: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a Windows scheduled task."""
        task_name = f"{self.TASK_PREFIX}{task_id}"

        try:
            result = subprocess.run(
                ["schtasks", "/delete", "/tn", task_name, "/f"],
                capture_output=True,
                text=True,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                ),
            )

            if task_id in self._tasks:
                del self._tasks[task_id]
                self._save_tasks()

            return result.returncode == 0

        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def _update_system_task(self, task_id: str) -> bool:
        """Update Windows task (recreate with new settings)."""
        task = self._tasks.get(task_id)
        if task:
            self.delete_task(task_id)
            if task.enabled:
                return self.create_task(task)
        return True


class MacOSTaskScheduler(TaskSchedulerBase):
    """macOS launchd implementation for scheduled tasks."""

    PLIST_PREFIX = "org.acb.link."
    LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"

    def __init__(self, app_path: Optional[Path] = None):
        super().__init__(app_path)
        self.LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_plist_path(self, task_id: str) -> Path:
        """Get path to launchd plist file."""
        return self.LAUNCH_AGENTS_DIR / f"{self.PLIST_PREFIX}{task_id}.plist"

    def create_task(self, task: ScheduledTask) -> bool:
        """Create a macOS launchd task."""
        plist_path = self._get_plist_path(task.id)

        # Build command arguments
        if task.task_type == TaskType.RECORDING:
            args = ["--record", task.stream_name, "--duration", str(task.duration_minutes)]
        elif task.task_type == TaskType.REMINDER:
            args = ["--notify", task.notification_message]
        elif task.task_type == TaskType.PODCAST_DOWNLOAD:
            args = ["--download", task.podcast_url]
        elif task.task_type == TaskType.PODCAST_SYNC:
            args = ["--sync-podcasts"]
        else:
            args = []

        # Build launchd plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.PLIST_PREFIX}{task.id}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.app_path}</string>
        {chr(10).join(f'        <string>{arg}</string>' for arg in args)}
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{task.scheduled_time.hour}</integer>
        <key>Minute</key>
        <integer>{task.scheduled_time.minute}</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/acblink_{task.id}.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/acblink_{task.id}.out</string>
</dict>
</plist>
"""

        try:
            # Write plist file
            with open(plist_path, "w") as f:
                f.write(plist_content)

            # Load the task
            subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)

            self._tasks[task.id] = task
            self._save_tasks()
            return True

        except Exception as e:
            print(f"Error creating task: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a macOS launchd task."""
        plist_path = self._get_plist_path(task_id)

        try:
            # Unload the task
            subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)

            # Remove plist file
            if plist_path.exists():
                plist_path.unlink()

            if task_id in self._tasks:
                del self._tasks[task_id]
                self._save_tasks()

            return True

        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def _update_system_task(self, task_id: str) -> bool:
        """Update macOS task."""
        task = self._tasks.get(task_id)
        if task:
            self.delete_task(task_id)
            if task.enabled:
                return self.create_task(task)
        return True


def get_scheduler(app_path: Optional[Path] = None) -> TaskSchedulerBase:
    """
    Get the appropriate scheduler for the current platform.

    Args:
        app_path: Optional path to the application executable

    Returns:
        Platform-specific task scheduler
    """
    system = platform.system().lower()

    if system == "windows":
        return WindowsTaskScheduler(app_path)
    elif system == "darwin":
        return MacOSTaskScheduler(app_path)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


# Convenience functions


def schedule_recording(
    stream_name: str,
    start_time: datetime,
    duration_minutes: int,
    name: Optional[str] = None,
    repeat_days: Optional[List[int]] = None,
) -> Optional[str]:
    """
    Schedule a stream recording.

    Args:
        stream_name: Name of the stream to record
        start_time: When to start recording
        duration_minutes: How long to record
        name: Optional task name
        repeat_days: Optional list of days to repeat (0=Mon, 6=Sun)

    Returns:
        Task ID if successful, None otherwise
    """
    scheduler = get_scheduler()

    task = ScheduledTask(
        id=str(uuid.uuid4())[:8],
        task_type=TaskType.RECORDING,
        name=name or f"Record {stream_name}",
        description=f"Record {stream_name} for {duration_minutes} minutes",
        scheduled_time=start_time,
        repeat_days=repeat_days,
        duration_minutes=duration_minutes,
        stream_name=stream_name,
    )

    if scheduler.create_task(task):
        return task.id
    return None


def schedule_reminder(
    message: str, reminder_time: datetime, name: Optional[str] = None
) -> Optional[str]:
    """
    Schedule a notification reminder.

    Args:
        message: Notification message
        reminder_time: When to show reminder
        name: Optional task name

    Returns:
        Task ID if successful, None otherwise
    """
    scheduler = get_scheduler()

    task = ScheduledTask(
        id=str(uuid.uuid4())[:8],
        task_type=TaskType.REMINDER,
        name=name or "ACB Link Reminder",
        description=message[:50] + "..." if len(message) > 50 else message,
        scheduled_time=reminder_time,
        notification_message=message,
    )

    if scheduler.create_task(task):
        return task.id
    return None


def schedule_podcast_sync(
    sync_time: datetime, repeat_days: Optional[List[int]] = None
) -> Optional[str]:
    """
    Schedule automatic podcast feed sync.

    Args:
        sync_time: When to sync
        repeat_days: Days to repeat (default: daily)

    Returns:
        Task ID if successful, None otherwise
    """
    scheduler = get_scheduler()

    task = ScheduledTask(
        id=str(uuid.uuid4())[:8],
        task_type=TaskType.PODCAST_SYNC,
        name="Sync Podcast Feeds",
        description="Automatically check for new podcast episodes",
        scheduled_time=sync_time,
        repeat_days=repeat_days or [0, 1, 2, 3, 4, 5, 6],  # Daily
    )

    if scheduler.create_task(task):
        return task.id
    return None


def cancel_task(task_id: str) -> bool:
    """Cancel a scheduled task."""
    scheduler = get_scheduler()
    return scheduler.delete_task(task_id)


def get_scheduled_recordings() -> List[ScheduledTask]:
    """Get all scheduled recordings."""
    scheduler = get_scheduler()
    return scheduler.get_tasks_by_type(TaskType.RECORDING)


def get_upcoming_events(hours: int = 24) -> List[ScheduledTask]:
    """Get tasks scheduled within the next N hours."""
    scheduler = get_scheduler()
    return scheduler.get_upcoming_tasks(hours)
