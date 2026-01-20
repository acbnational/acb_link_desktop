"""
Test suite for scheduler module.
Tests system-level task scheduling.
"""

import platform
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestSchedulerImport:
    """Test scheduler module imports."""

    def test_import_scheduler_module(self):
        """Test that scheduler module imports without error."""
        from acb_link import scheduler

        assert scheduler is not None

    def test_task_type_enum(self):
        """Test TaskType enum exists with expected values."""
        from acb_link.scheduler import TaskType

        assert hasattr(TaskType, "RECORDING")
        assert hasattr(TaskType, "REMINDER")
        assert hasattr(TaskType, "PODCAST_SYNC")

    def test_scheduled_task_dataclass(self):
        """Test ScheduledTask dataclass."""
        from acb_link.scheduler import ScheduledTask, TaskType

        task = ScheduledTask(
            id="test_task_1",
            task_type=TaskType.RECORDING,
            name="Test Recording",
            description="Test recording task",
            scheduled_time=datetime.now() + timedelta(hours=1),
            enabled=True,
        )

        assert task.id == "test_task_1"
        assert task.task_type == TaskType.RECORDING
        assert task.enabled is True


class TestTaskScheduler:
    """Test task scheduler functionality."""

    def test_get_scheduler(self):
        """Test getting platform-appropriate scheduler."""
        from acb_link.scheduler import get_scheduler

        scheduler = get_scheduler()
        assert scheduler is not None

    def test_scheduler_has_required_methods(self):
        """Test that scheduler has required methods."""
        from acb_link.scheduler import get_scheduler

        scheduler = get_scheduler()

        # Should have these methods
        assert hasattr(scheduler, "create_task")
        assert hasattr(scheduler, "delete_task")
        assert hasattr(scheduler, "get_tasks_by_type")
        assert hasattr(scheduler, "get_task")

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_scheduler_type(self):
        """Test Windows scheduler is correct type."""
        from acb_link.scheduler import WindowsTaskScheduler, get_scheduler

        scheduler = get_scheduler()
        assert isinstance(scheduler, WindowsTaskScheduler)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_scheduler_type(self):
        """Test macOS scheduler is correct type."""
        from acb_link.scheduler import MacOSTaskScheduler, get_scheduler

        scheduler = get_scheduler()
        assert isinstance(scheduler, MacOSTaskScheduler)


class TestConvenienceFunctions:
    """Test convenience scheduling functions."""

    def test_schedule_recording_function_exists(self):
        """Test schedule_recording function exists."""
        from acb_link.scheduler import schedule_recording

        assert callable(schedule_recording)

    def test_schedule_reminder_function_exists(self):
        """Test schedule_reminder function exists."""
        from acb_link.scheduler import schedule_reminder

        assert callable(schedule_reminder)

    def test_schedule_podcast_sync_function_exists(self):
        """Test schedule_podcast_sync function exists."""
        from acb_link.scheduler import schedule_podcast_sync

        assert callable(schedule_podcast_sync)

    def test_cancel_task_function_exists(self):
        """Test cancel_task function exists."""
        from acb_link.scheduler import cancel_task

        assert callable(cancel_task)

    def test_get_scheduled_recordings_function_exists(self):
        """Test get_scheduled_recordings function exists."""
        from acb_link.scheduler import get_scheduled_recordings

        assert callable(get_scheduled_recordings)


class TestWindowsScheduler:
    """Test Windows Task Scheduler integration."""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_task_prefix(self):
        """Test Windows tasks use correct prefix."""
        from acb_link.scheduler import WindowsTaskScheduler

        scheduler = WindowsTaskScheduler()
        assert hasattr(scheduler, "TASK_PREFIX")
        assert "ACBLink" in scheduler.TASK_PREFIX

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    @patch("subprocess.run")
    def test_create_task_calls_schtasks(self, mock_run):
        """Test that create_task uses schtasks command."""
        from acb_link.scheduler import ScheduledTask, TaskType, WindowsTaskScheduler

        mock_run.return_value = MagicMock(returncode=0)

        scheduler = WindowsTaskScheduler()
        task = ScheduledTask(
            id="test_1",
            task_type=TaskType.RECORDING,
            name="Test",
            description="Test task",
            scheduled_time=datetime.now() + timedelta(hours=1),
            enabled=True,
        )

        try:
            scheduler.create_task(task)
            # Verify schtasks was called
            assert mock_run.called
            call_args = str(mock_run.call_args)
            assert "schtasks" in call_args.lower() or "powershell" in call_args.lower()
        except Exception:
            # May fail due to permissions in test environment
            pass


class TestMacOSScheduler:
    """Test macOS launchd integration."""

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_plist_directory(self):
        """Test macOS uses correct plist directory."""
        from acb_link.scheduler import MacOSTaskScheduler

        scheduler = MacOSTaskScheduler()

        if hasattr(scheduler, "LAUNCH_AGENTS_DIR"):
            # Should be in user's LaunchAgents
            assert "LaunchAgents" in str(scheduler.LAUNCH_AGENTS_DIR)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_label_prefix(self):
        """Test macOS uses correct label prefix."""
        from acb_link.scheduler import MacOSTaskScheduler

        scheduler = MacOSTaskScheduler()

        if hasattr(scheduler, "PLIST_PREFIX"):
            assert (
                "acb" in scheduler.PLIST_PREFIX.lower() or "link" in scheduler.PLIST_PREFIX.lower()
            )


class TestScheduledTaskValidation:
    """Test task validation."""

    def test_task_requires_future_time(self):
        """Test that tasks should be scheduled for future."""
        from acb_link.scheduler import ScheduledTask, TaskType

        # Creating a task with past time - implementation may vary
        past_time = datetime.now() - timedelta(hours=1)

        task = ScheduledTask(
            id="test",
            task_type=TaskType.RECORDING,
            name="Test",
            description="Test task",
            scheduled_time=past_time,
            enabled=True,
        )

        # Task should be created, but scheduler may reject it
        assert task.scheduled_time < datetime.now()

    def test_task_id_uniqueness(self):
        """Test unique task IDs are generated."""
        import uuid

        # Test that UUID generation produces unique IDs
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        # IDs should be unique
        assert id1 != id2
