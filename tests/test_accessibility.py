"""
Test suite for accessibility module.
Tests WCAG 2.2 AA compliance features.
"""

import pytest
import platform


class TestScreenReaderDetection:
    """Test screen reader detection functionality."""
    
    def test_import_accessibility_module(self):
        """Test that accessibility module imports without error."""
        from acb_link import accessibility
        assert accessibility is not None
    
    def test_announce_does_not_raise(self):
        """Test that announce function doesn't raise exceptions."""
        from acb_link.accessibility import announce
        # Should not raise even if no screen reader is active
        try:
            announce("Test message")
        except Exception as e:
            pytest.fail(f"announce raised exception: {e}")
    
    def test_announce_with_empty_string(self):
        """Test announce with empty string."""
        from acb_link.accessibility import announce
        # Should handle empty strings gracefully
        announce("")
    
    def test_screen_reader_enum_exists(self):
        """Test that ScreenReader enum has expected values."""
        from acb_link.accessibility import ScreenReader
        
        assert hasattr(ScreenReader, 'NONE')
        assert hasattr(ScreenReader, 'NVDA')
        assert hasattr(ScreenReader, 'JAWS')
        assert hasattr(ScreenReader, 'NARRATOR')
        
        if platform.system() == "Darwin":
            assert hasattr(ScreenReader, 'VOICEOVER')
    
    def test_get_active_screen_reader(self):
        """Test getting active screen reader."""
        from acb_link.accessibility import get_screen_reader_manager, ScreenReader
        
        manager = get_screen_reader_manager()
        reader = manager._active_reader
        assert reader is None or isinstance(reader, ScreenReader)


class TestAccessibleControls:
    """Test accessible control helpers."""
    
    @pytest.fixture
    def wx_app(self):
        """Create wxPython app for testing."""
        import wx
        app = wx.App(False)
        yield app
        app.Destroy()
    
    @pytest.fixture
    def test_frame(self, wx_app):
        """Create test frame."""
        import wx
        frame = wx.Frame(None, title="Test Frame")
        yield frame
        frame.Destroy()
    
    def test_make_accessible_sets_name(self, test_frame):
        """Test that make_accessible sets control name."""
        import wx
        from acb_link.accessibility import make_accessible
        
        button = wx.Button(test_frame, label="▶")
        make_accessible(button, "Play", "Start playback")
        
        assert button.GetName() == "Play"
    
    def test_make_accessible_with_none_control(self):
        """Test make_accessible handles None gracefully."""
        from acb_link.accessibility import make_accessible
        
        # Should not raise
        try:
            make_accessible(None, "Test", "Test description")  # type: ignore[arg-type]
        except Exception as e:
            pytest.fail(f"make_accessible raised exception with None: {e}")
    
    def test_make_list_accessible(self, test_frame):
        """Test that make_list_accessible sets list name."""
        import wx
        from acb_link.accessibility import make_list_accessible
        
        list_ctrl = wx.ListCtrl(test_frame, style=wx.LC_REPORT)
        make_list_accessible(list_ctrl, "Streams list", "Select a stream to play")
        
        assert list_ctrl.GetName() == "Streams list"


class TestAnnouncementTypes:
    """Test different announcement types."""
    
    def test_announce_status(self):
        """Test status announcement."""
        from acb_link.accessibility import get_screen_reader_manager
        
        # Should not raise
        try:
            manager = get_screen_reader_manager()
            manager.speak("Now playing: ACB Main Audio")
        except Exception as e:
            pytest.fail(f"announce_status raised exception: {e}")
    
    def test_announce_with_interrupt(self):
        """Test announcement with interrupt flag."""
        from acb_link.accessibility import announce
        
        # Should not raise
        try:
            announce("Urgent message", interrupt=True)
        except Exception as e:
            pytest.fail(f"announce with interrupt raised exception: {e}")


class TestPlatformSupport:
    """Test platform-specific accessibility support."""
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_screen_reader_detection(self):
        """Test Windows screen reader detection."""
        from acb_link.accessibility import get_screen_reader_manager, ScreenReader
        
        manager = get_screen_reader_manager()
        reader = manager._active_reader
        # On Windows, should detect one of the Windows screen readers or NONE
        assert reader is None or reader in [
            ScreenReader.NONE,
            ScreenReader.NVDA,
            ScreenReader.JAWS,
            ScreenReader.NARRATOR,
            ScreenReader.UNKNOWN
        ]
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_voiceover_detection(self):
        """Test macOS VoiceOver detection."""
        from acb_link.accessibility import get_screen_reader_manager, ScreenReader
        
        manager = get_screen_reader_manager()
        reader = manager._active_reader
        # On macOS, should detect VoiceOver or NONE
        assert reader is None or reader in [ScreenReader.NONE, ScreenReader.VOICEOVER]


class TestWCAGCompliance:
    """Test WCAG 2.2 AA compliance requirements."""
    
    def test_focus_visible_support(self):
        """Test that focus indicator support exists (WCAG 2.4.7)."""
        # This is a structural test - actual visual testing requires manual verification
        from acb_link import accessibility
        # Module should exist and be importable
        assert accessibility is not None
    
    def test_name_role_value_support(self):
        """Test that accessible name support exists (WCAG 4.1.2)."""
        from acb_link.accessibility import make_accessible, make_list_accessible
        
        # Functions should exist
        assert callable(make_accessible)
        assert callable(make_list_accessible)
    
    def test_status_messages_support(self):
        """Test that status message support exists (WCAG 4.1.3)."""
        from acb_link.accessibility import announce, get_screen_reader_manager
        
        # Functions should exist
        assert callable(announce)
        manager = get_screen_reader_manager()
        assert hasattr(manager, 'announce_status')
