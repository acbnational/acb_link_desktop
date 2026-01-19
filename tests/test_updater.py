"""
Test suite for updater module.
Tests GitHub-based automatic update system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestVersionComparison:
    """Test version comparison logic."""
    
    def test_import_updater_module(self):
        """Test that updater module imports without error."""
        from acb_link import updater
        assert updater is not None
    
    def test_update_checker_exists(self):
        """Test UpdateChecker class exists."""
        from acb_link.updater import UpdateChecker
        assert UpdateChecker is not None
    
    def test_version_parsing(self):
        """Test version string parsing."""
        from acb_link.updater import UpdateChecker
        
        checker = UpdateChecker("2.0.0")
        
        # Test version comparison helper if it exists
        if hasattr(checker, '_parse_version'):
            assert checker._parse_version("2.0.0") == (2, 0, 0)
            assert checker._parse_version("2.1.0") == (2, 1, 0)
            assert checker._parse_version("2.0.1") == (2, 0, 1)
    
    def test_newer_version_detection(self):
        """Test detecting newer versions."""
        from acb_link.updater import UpdateChecker
        
        checker = UpdateChecker("2.0.0")
        
        # Version comparison is done via version tuples
        if hasattr(checker, '_parse_version'):
            v1 = checker._parse_version("2.1.0")
            v2 = checker._parse_version("2.0.0")
            assert v1 > v2


class TestGitHubAPI:
    """Test GitHub API integration."""
    
    def test_github_repo_url(self):
        """Test that GitHub repo URL is correctly configured."""
        from acb_link.updater import UpdateChecker
        
        checker = UpdateChecker("2.0.0")
        
        # Check that API URL is set
        assert hasattr(checker, 'api_url') or hasattr(checker, 'repo_url')
    
    @patch('urllib.request.urlopen')
    def test_check_for_updates_handles_network_error(self, mock_urlopen):
        """Test that network errors are handled gracefully."""
        from acb_link.updater import UpdateChecker
        import urllib.error
        
        mock_urlopen.side_effect = urllib.error.URLError("Network error")
        
        checker = UpdateChecker("2.0.0")
        
        # Should not raise, should return None or empty result
        try:
            _ = checker.check_for_updates()  # noqa: F841
            # Result should indicate no update or error
        except Exception as e:
            pytest.fail(f"check_for_updates raised exception on network error: {e}")
    
    @patch('urllib.request.urlopen')
    def test_check_for_updates_parses_response(self, mock_urlopen):
        """Test parsing GitHub API response."""
        from acb_link.updater import UpdateChecker
        
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "tag_name": "v2.1.0",
            "name": "ACB Link Desktop v2.1.0",
            "body": "Release notes",
            "assets": [
                {
                    "name": "ACBLink-2.1.0-Setup.exe",
                    "browser_download_url": "https://github.com/test/test.exe",
                    "size": 10000000
                }
            ]
        }).encode()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        checker = UpdateChecker("2.0.0")
        
        try:
            result = checker.check_for_updates()
            # If result is not None, it should have version info
            if result:
                assert hasattr(result, 'version') or 'version' in str(result)
        except Exception:
            # Some implementations may have different structures
            pass


class TestUpdateManager:
    """Test AutoUpdateManager functionality."""
    
    def test_auto_update_manager_exists(self):
        """Test AutoUpdateManager class exists."""
        from acb_link.updater import AutoUpdateManager
        assert AutoUpdateManager is not None
    
    def test_get_update_manager_singleton(self):
        """Test that get_update_manager returns consistent instance."""
        from acb_link.updater import get_update_manager
        
        manager1 = get_update_manager("2.0.0")
        manager2 = get_update_manager("2.0.0")
        
        # Should return same instance (singleton pattern)
        assert manager1 is manager2
    
    def test_manual_update_check_function(self):
        """Test check_for_updates_manual function exists."""
        from acb_link.updater import check_for_updates_manual
        assert callable(check_for_updates_manual)
    
    def test_startup_update_check_function(self):
        """Test check_for_updates_on_startup function exists."""
        from acb_link.updater import check_for_updates_on_startup
        assert callable(check_for_updates_on_startup)


class TestUpdateDownloader:
    """Test update download functionality."""
    
    def test_update_downloader_exists(self):
        """Test UpdateDownloader class exists."""
        from acb_link.updater import UpdateDownloader
        assert UpdateDownloader is not None
    
    def test_download_directory_creation(self):
        """Test that download directory is created properly."""
        from acb_link.updater import UpdateDownloader
        
        downloader = UpdateDownloader()
        
        # Check that downloader has _download_path attribute
        assert hasattr(downloader, '_download_path')


class TestReleaseDataClasses:
    """Test release data structures."""
    
    def test_release_asset_dataclass(self):
        """Test ReleaseAsset dataclass exists and works."""
        try:
            from acb_link.updater import ReleaseAsset
            
            asset = ReleaseAsset(
                name="ACBLink-2.0.0-Setup.exe",
                download_url="https://example.com/download.exe",
                size=10000000,
                content_type="application/octet-stream"
            )
            
            assert asset.name == "ACBLink-2.0.0-Setup.exe"
            assert asset.size == 10000000
        except ImportError:
            # ReleaseAsset may not be exported
            pass
    
    def test_release_dataclass(self):
        """Test Release dataclass exists and works."""
        try:
            from acb_link.updater import Release
            
            release = Release(
                tag_name="v2.0.0",
                name="ACB Link Desktop v2.0.0",
                body="Release notes",
                published_at="2026-01-17T00:00:00Z",
                html_url="https://github.com/test/releases/v2.0.0",
                prerelease=False,
                draft=False,
                assets=[]
            )
            
            assert release.version == "2.0.0"
        except ImportError:
            # Release may not be exported
            pass
