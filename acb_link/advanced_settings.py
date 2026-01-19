"""
ACB Link Desktop - Advanced Settings Dialog (Admin-Only)

Advanced settings that affect organization-wide configuration require
administrator authentication. User-safe settings have been moved to
the regular Settings dialog.

Security:
- Data source URLs, network settings, and update configuration
  require CONFIG_ADMIN or SUPER_ADMIN role
- Changes are synced to server and distributed to all users
- All modifications are logged in the audit trail

WCAG 2.2 AA compliant.
"""

import wx
import wx.adv
import re
import json
from dataclasses import asdict, fields
from typing import Optional, Dict, Any, Callable, List, Tuple
from pathlib import Path
import logging

from .config import (
    AppConfig, get_config, save_config, reload_config,
    DataSourceConfig, LiveDataConfig, UpdateConfig,
    NetworkConfig, PathConfig, DefaultsConfig
)
from .settings import AppSettings
from .accessibility import announce, make_accessible, make_button_accessible

logger = logging.getLogger(__name__)


# =============================================================================
# Validation Framework
# =============================================================================

class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class FieldValidator:
    """Validates individual fields with type-specific rules."""
    
    @staticmethod
    def validate_url(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate URL format."""
        if not value:
            return True, ""  # Empty is valid (optional)
        
        url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
        if not re.match(url_pattern, value):
            return False, f"{field_name}: Invalid URL format. Must start with http:// or https://"
        return True, ""
    
    @staticmethod
    def validate_path(value: str, field_name: str, must_exist: bool = False) -> Tuple[bool, str]:
        """Validate file/directory path."""
        if not value:
            return True, ""
        
        try:
            path = Path(value)
            if must_exist and not path.exists():
                return False, f"{field_name}: Path does not exist"
            return True, ""
        except Exception as e:
            return False, f"{field_name}: Invalid path format - {str(e)}"
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, 
                        min_val: Optional[int] = None, 
                        max_val: Optional[int] = None) -> Tuple[bool, str]:
        """Validate integer value within range."""
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False, f"{field_name}: Value must be at least {min_val}"
            if max_val is not None and num > max_val:
                return False, f"{field_name}: Value must be at most {max_val}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}: Must be a whole number"
    
    @staticmethod
    def validate_float(value: Any, field_name: str,
                      min_val: Optional[float] = None,
                      max_val: Optional[float] = None) -> Tuple[bool, str]:
        """Validate float value within range."""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False, f"{field_name}: Value must be at least {min_val}"
            if max_val is not None and num > max_val:
                return False, f"{field_name}: Value must be at most {max_val}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}: Must be a number"
    
    @staticmethod
    def validate_choice(value: str, field_name: str, 
                       choices: List[str]) -> Tuple[bool, str]:
        """Validate value is one of allowed choices."""
        if value not in choices:
            return False, f"{field_name}: Must be one of: {', '.join(choices)}"
        return True, ""
    
    @staticmethod
    def validate_non_empty(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate non-empty string."""
        if not value or not value.strip():
            return False, f"{field_name}: Cannot be empty"
        return True, ""


# =============================================================================
# Warning Dialog
# =============================================================================

class AdvancedSettingsWarningDialog(wx.Dialog):
    """Warning dialog before entering advanced settings (admin only)."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Advanced Settings - Administrator Access",
            size=(550, 400),
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self._build_ui()
        self.Centre()
    
    def _build_ui(self):
        """Build the warning dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Warning icon and message
        icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create warning icon
        warning_bmp = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX, (48, 48))
        icon = wx.StaticBitmap(panel, bitmap=warning_bmp)
        icon_sizer.Add(icon, 0, wx.ALL, 10)
        
        # Warning text
        warning_text = wx.StaticText(panel, label="Administrator Access: Advanced Settings")
        warning_font = warning_text.GetFont()
        warning_font.SetPointSize(14)
        warning_font.SetWeight(wx.FONTWEIGHT_BOLD)
        warning_text.SetFont(warning_font)
        warning_text.SetForegroundColour(wx.Colour(200, 50, 50))
        icon_sizer.Add(warning_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        
        sizer.Add(icon_sizer, 0, wx.ALL, 10)
        
        # Detailed warning message
        message = (
            "You are accessing the Advanced Settings area as an administrator.\n\n"
            "Changes made here will affect ALL ACB Link users:\n"
            "• Data source URLs (server connections)\n"
            "• Network configuration (timeouts, proxy settings)\n"
            "• Update server configuration\n"
            "• Organization-wide default values\n\n"
            "IMPORTANT:\n"
            "• All changes are logged and audited\n"
            "• Changes sync to server and distribute to all users\n"
            "• Invalid settings could disrupt service for all users\n\n"
            "A 'Reset to Defaults' option is available if needed.\n\n"
            "Do you wish to proceed?"
        )
        
        msg_text = wx.StaticText(panel, label=message)
        msg_text.Wrap(450)
        sizer.Add(msg_text, 1, wx.EXPAND | wx.ALL, 15)
        
        # Checkbox to not show again
        self.chk_dont_show = wx.CheckBox(panel, label="Don't show this warning again")
        make_accessible(self.chk_dont_show, 
                       "Don't show this warning again", 
                       "Check to skip this warning in future")
        sizer.Add(self.chk_dont_show, 0, wx.LEFT | wx.BOTTOM, 15)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_proceed = wx.Button(panel, wx.ID_OK, "Proceed to Advanced Settings")
        make_button_accessible(btn_proceed, "Proceed to Advanced Settings",
                              "Open the advanced settings dialog")
        btn_proceed.SetDefault()
        
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Go Back")
        make_button_accessible(btn_cancel, "Go Back", "Return without opening advanced settings")
        
        btn_sizer.Add(btn_cancel, 0, wx.RIGHT, 10)
        btn_sizer.Add(btn_proceed, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 15)
        
        panel.SetSizer(sizer)
        
        # Announce for screen readers
        announce("Warning: You are about to access Advanced Settings. "
                "Changing these values incorrectly could affect application operation.")
    
    def should_show_again(self) -> bool:
        """Return whether to show warning in future."""
        return not self.chk_dont_show.GetValue()


# =============================================================================
# Advanced Settings Dialog (Multi-Tab)
# =============================================================================

class AdvancedSettingsDialog(wx.Dialog):
    """Multi-tab dialog for editing all configuration values."""
    
    def __init__(self, parent, config: AppConfig, settings: AppSettings):
        super().__init__(
            parent,
            title="Advanced Settings - ACB Link Desktop",
            size=(750, 650),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.config = config
        self.settings = settings
        
        # Store original for reset
        self._original_config_dict = config.to_dict()
        
        # Validation errors
        self._validation_errors: List[str] = []
        
        # Track modified fields
        self._modified_fields: Dict[str, Any] = {}
        
        self._build_ui()
        self.Centre()
        
        announce("Advanced Settings dialog opened. Use arrow keys to navigate tabs.")
    
    def _build_ui(self):
        """Build the advanced settings dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header with warning banner
        header = wx.Panel(self)
        header.SetBackgroundColour(wx.Colour(255, 250, 230))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        warning_icon = wx.StaticBitmap(header, 
            bitmap=wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_TOOLBAR, (24, 24)))
        header_sizer.Add(warning_icon, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        header_text = wx.StaticText(header, 
            label="Expert Mode: Changes here affect core application behavior")
        header_text.SetForegroundColour(wx.Colour(150, 100, 0))
        header_sizer.Add(header_text, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        header.SetSizer(header_sizer)
        main_sizer.Add(header, 0, wx.EXPAND)
        
        # Create notebook for tabs
        self.notebook = wx.Notebook(self)
        make_accessible(self.notebook, "Advanced settings categories", 
                       "Use arrow keys to navigate between settings tabs")
        
        # Add tabs
        self._add_data_sources_tab()
        self._add_network_tab()
        self._add_paths_tab()
        self._add_updates_tab()
        self._add_defaults_tab()
        self._add_experimental_tab()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Validation status
        self.validation_status = wx.StaticText(self, label="")
        self.validation_status.SetForegroundColour(wx.Colour(200, 50, 50))
        main_sizer.Add(self.validation_status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # Buttons
        btn_sizer = self._create_buttons()
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _add_data_sources_tab(self):
        """Add data sources configuration tab."""
        panel = wx.ScrolledWindow(self.notebook)
        panel.SetScrollRate(0, 20)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Base URL
        base_box = wx.StaticBox(panel, label="ACB Link Server")
        base_sizer = wx.StaticBoxSizer(base_box, wx.VERTICAL)
        
        base_row = wx.BoxSizer(wx.HORIZONTAL)
        base_row.Add(wx.StaticText(panel, label="Base URL:"), 0, 
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.base_url = wx.TextCtrl(panel, value=self.config.live_data.base_url, size=(400, -1))
        make_accessible(self.base_url, "Base URL", "Primary server address for ACB Link data")
        base_row.Add(self.base_url, 1)
        base_sizer.Add(base_row, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(base_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Data sources
        sources_box = wx.StaticBox(panel, label="Data Source URLs")
        sources_sizer = wx.StaticBoxSizer(sources_box, wx.VERTICAL)
        
        help_text = wx.StaticText(panel, 
            label="These URLs determine where ACB Link fetches its content. "
                  "Only change if directed by ACB support.")
        help_text.Wrap(600)
        sources_sizer.Add(help_text, 0, wx.ALL, 5)
        
        # Create controls for each data source
        self.data_source_controls: Dict[str, Dict[str, wx.Control]] = {}
        
        sources = [
            ("streams", "Streams", self.config.live_data.streams),
            ("podcasts", "Podcasts", self.config.live_data.podcasts),
            ("state_affiliates", "State Affiliates", self.config.live_data.state_affiliates),
            ("special_interest_groups", "Special Interest Groups", self.config.live_data.special_interest_groups),
            ("publications", "Publications", self.config.live_data.publications),
            ("categories", "Categories", self.config.live_data.categories),
            ("acb_sites", "ACB Sites", self.config.live_data.acb_sites),
        ]
        
        for key, label, source in sources:
            source_panel = wx.Panel(panel)
            source_sizer_inner = wx.FlexGridSizer(2, 3, 5, 10)
            source_sizer_inner.AddGrowableCol(1, 1)
            
            source_sizer_inner.Add(wx.StaticText(source_panel, label=f"{label} URL:"), 
                                  0, wx.ALIGN_CENTER_VERTICAL)
            url_ctrl = wx.TextCtrl(source_panel, value=source.live_url, size=(350, -1))
            make_accessible(url_ctrl, f"{label} URL", f"URL for fetching {label.lower()} data")
            source_sizer_inner.Add(url_ctrl, 1, wx.EXPAND)
            
            enabled_chk = wx.CheckBox(source_panel, label="Enabled")
            enabled_chk.SetValue(source.enabled)
            make_accessible(enabled_chk, f"{label} enabled", 
                          f"Enable or disable {label.lower()} data fetching")
            source_sizer_inner.Add(enabled_chk, 0, wx.ALIGN_CENTER_VERTICAL)
            
            source_sizer_inner.Add(wx.StaticText(source_panel, label="Cache (hours):"), 
                                  0, wx.ALIGN_CENTER_VERTICAL)
            cache_ctrl = wx.SpinCtrl(source_panel, value=str(source.cache_duration_hours), 
                                    min=1, max=720)
            make_accessible(cache_ctrl, f"{label} cache duration", 
                          "Hours to cache data before refreshing")
            source_sizer_inner.Add(cache_ctrl, 0)
            source_sizer_inner.Add(wx.StaticText(source_panel, label=""), 0)  # Spacer
            
            source_panel.SetSizer(source_sizer_inner)
            sources_sizer.Add(source_panel, 0, wx.EXPAND | wx.ALL, 5)
            
            self.data_source_controls[key] = {
                "url": url_ctrl,
                "enabled": enabled_chk,
                "cache": cache_ctrl
            }
        
        sizer.Add(sources_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Data Sources")
    
    def _add_network_tab(self):
        """Add network configuration tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Timeouts
        timeout_box = wx.StaticBox(panel, label="Connection Settings")
        timeout_sizer = wx.StaticBoxSizer(timeout_box, wx.VERTICAL)
        
        timeout_row = wx.BoxSizer(wx.HORIZONTAL)
        timeout_row.Add(wx.StaticText(panel, label="Connection timeout:"), 0, 
                       wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.timeout = wx.SpinCtrl(panel, value=str(self.config.network.timeout_seconds), 
                                  min=5, max=120)
        make_accessible(self.timeout, "Connection timeout", "Seconds to wait for connections")
        timeout_row.Add(self.timeout, 0)
        timeout_row.Add(wx.StaticText(panel, label="seconds"), 0, 
                       wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        timeout_sizer.Add(timeout_row, 0, wx.ALL, 5)
        
        retry_row = wx.BoxSizer(wx.HORIZONTAL)
        retry_row.Add(wx.StaticText(panel, label="Retry count:"), 0, 
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.retry_count = wx.SpinCtrl(panel, value=str(self.config.network.retry_count), 
                                      min=0, max=10)
        make_accessible(self.retry_count, "Retry count", "Number of times to retry failed connections")
        retry_row.Add(self.retry_count, 0)
        retry_row.Add(wx.StaticText(panel, label="(0 = no retries)"), 0, 
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        timeout_sizer.Add(retry_row, 0, wx.ALL, 5)
        
        delay_row = wx.BoxSizer(wx.HORIZONTAL)
        delay_row.Add(wx.StaticText(panel, label="Retry delay:"), 0, 
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.retry_delay = wx.SpinCtrl(panel, value=str(self.config.network.retry_delay_seconds), 
                                      min=1, max=60)
        make_accessible(self.retry_delay, "Retry delay", "Seconds to wait between retries")
        delay_row.Add(self.retry_delay, 0)
        delay_row.Add(wx.StaticText(panel, label="seconds"), 0, 
                     wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        timeout_sizer.Add(delay_row, 0, wx.ALL, 5)
        
        sizer.Add(timeout_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # User agent
        ua_box = wx.StaticBox(panel, label="User Agent")
        ua_sizer = wx.StaticBoxSizer(ua_box, wx.VERTICAL)
        
        ua_help = wx.StaticText(panel, 
            label="The user agent identifies ACB Link to servers. "
                  "Only change if experiencing connection issues.")
        ua_help.Wrap(600)
        ua_sizer.Add(ua_help, 0, wx.ALL, 5)
        
        self.user_agent = wx.TextCtrl(panel, value=self.config.network.user_agent, size=(400, -1))
        make_accessible(self.user_agent, "User agent string", 
                       "Identifier sent to servers when connecting")
        ua_sizer.Add(self.user_agent, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(ua_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Proxy settings
        proxy_box = wx.StaticBox(panel, label="Proxy Settings")
        proxy_sizer = wx.StaticBoxSizer(proxy_box, wx.VERTICAL)
        
        self.proxy_enabled = wx.CheckBox(panel, label="Use proxy server")
        self.proxy_enabled.SetValue(self.config.network.proxy_enabled)
        make_accessible(self.proxy_enabled, "Use proxy server", 
                       "Route connections through a proxy server")
        proxy_sizer.Add(self.proxy_enabled, 0, wx.ALL, 5)
        
        proxy_row = wx.BoxSizer(wx.HORIZONTAL)
        proxy_row.Add(wx.StaticText(panel, label="Proxy URL:"), 0, 
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.proxy_url = wx.TextCtrl(panel, 
                                    value=self.config.network.proxy_url or "", 
                                    size=(400, -1))
        make_accessible(self.proxy_url, "Proxy URL", 
                       "Proxy server address, e.g., http://proxy:8080")
        proxy_row.Add(self.proxy_url, 1)
        proxy_sizer.Add(proxy_row, 0, wx.EXPAND | wx.ALL, 5)
        
        # Enable/disable proxy URL based on checkbox
        self.proxy_enabled.Bind(wx.EVT_CHECKBOX, 
            lambda e: self.proxy_url.Enable(self.proxy_enabled.GetValue()))
        self.proxy_url.Enable(self.proxy_enabled.GetValue())
        
        sizer.Add(proxy_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Network")
    
    def _add_paths_tab(self):
        """Add paths configuration tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # App data
        app_box = wx.StaticBox(panel, label="Application Data")
        app_sizer = wx.StaticBoxSizer(app_box, wx.VERTICAL)
        
        warning = wx.StaticText(panel, 
            label="⚠️ Changing these paths will not move existing data. "
                  "You must manually move files to new locations.")
        warning.SetForegroundColour(wx.Colour(200, 100, 0))
        warning.Wrap(600)
        app_sizer.Add(warning, 0, wx.ALL, 5)
        
        paths = [
            ("app_data", "App data directory:", self.config.paths.app_data_dir),
            ("cache", "Cache directory:", self.config.paths.cache_dir),
            ("logs", "Logs directory:", self.config.paths.logs_dir),
        ]
        
        self.path_controls: Dict[str, wx.TextCtrl] = {}
        
        for key, label, value in paths:
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.Add(wx.StaticText(panel, label=label), 0, 
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            ctrl = wx.TextCtrl(panel, value=value, size=(400, -1))
            make_accessible(ctrl, label.replace(":", ""), f"Path for {label.lower()}")
            row.Add(ctrl, 1, wx.RIGHT, 5)
            
            btn = wx.Button(panel, label="Browse...")
            btn.Bind(wx.EVT_BUTTON, lambda e, c=ctrl: self._browse_folder(c))
            make_button_accessible(btn, "Browse", f"Browse for {label.lower()}")
            row.Add(btn, 0)
            
            app_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 5)
            self.path_controls[key] = ctrl
        
        sizer.Add(app_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # User content
        user_box = wx.StaticBox(panel, label="User Content")
        user_sizer = wx.StaticBoxSizer(user_box, wx.VERTICAL)
        
        user_paths = [
            ("downloads", "Podcast downloads:", self.config.paths.downloads_dir),
            ("recordings", "Stream recordings:", self.config.paths.recordings_dir),
        ]
        
        for key, label, value in user_paths:
            row = wx.BoxSizer(wx.HORIZONTAL)
            row.Add(wx.StaticText(panel, label=label), 0, 
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            ctrl = wx.TextCtrl(panel, value=value, size=(400, -1))
            make_accessible(ctrl, label.replace(":", ""), f"Path for {label.lower()}")
            row.Add(ctrl, 1, wx.RIGHT, 5)
            
            btn = wx.Button(panel, label="Browse...")
            btn.Bind(wx.EVT_BUTTON, lambda e, c=ctrl: self._browse_folder(c))
            make_button_accessible(btn, "Browse", f"Browse for {label.lower()}")
            row.Add(btn, 0)
            
            user_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 5)
            self.path_controls[key] = ctrl
        
        sizer.Add(user_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Open buttons
        open_box = wx.StaticBox(panel, label="Quick Access")
        open_sizer = wx.StaticBoxSizer(open_box, wx.HORIZONTAL)
        
        btn_open_data = wx.Button(panel, label="Open App Data Folder")
        btn_open_data.Bind(wx.EVT_BUTTON, 
            lambda e: self._open_folder(self.path_controls["app_data"].GetValue()))
        make_button_accessible(btn_open_data, "Open App Data Folder", 
                              "Open the app data folder in Explorer")
        open_sizer.Add(btn_open_data, 0, wx.ALL, 5)
        
        btn_open_downloads = wx.Button(panel, label="Open Downloads Folder")
        btn_open_downloads.Bind(wx.EVT_BUTTON,
            lambda e: self._open_folder(self.path_controls["downloads"].GetValue()))
        make_button_accessible(btn_open_downloads, "Open Downloads Folder",
                              "Open the downloads folder in Explorer")
        open_sizer.Add(btn_open_downloads, 0, wx.ALL, 5)
        
        sizer.Add(open_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Paths")
    
    def _add_updates_tab(self):
        """Add updates configuration tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Update settings
        update_box = wx.StaticBox(panel, label="Automatic Updates")
        update_sizer = wx.StaticBoxSizer(update_box, wx.VERTICAL)
        
        self.updates_enabled = wx.CheckBox(panel, label="Enable automatic updates")
        self.updates_enabled.SetValue(self.config.updates.enabled)
        make_accessible(self.updates_enabled, "Enable automatic updates",
                       "Allow the app to check for and download updates")
        update_sizer.Add(self.updates_enabled, 0, wx.ALL, 5)
        
        self.check_startup = wx.CheckBox(panel, label="Check for updates on startup")
        self.check_startup.SetValue(self.config.updates.check_on_startup)
        make_accessible(self.check_startup, "Check for updates on startup",
                       "Check for new versions when the app starts")
        update_sizer.Add(self.check_startup, 0, wx.ALL, 5)
        
        interval_row = wx.BoxSizer(wx.HORIZONTAL)
        interval_row.Add(wx.StaticText(panel, label="Check interval:"), 0,
                        wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.check_interval = wx.SpinCtrl(panel, 
                                         value=str(self.config.updates.check_interval_hours),
                                         min=1, max=168)
        make_accessible(self.check_interval, "Update check interval",
                       "Hours between automatic update checks")
        interval_row.Add(self.check_interval, 0)
        interval_row.Add(wx.StaticText(panel, label="hours"), 0,
                        wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        update_sizer.Add(interval_row, 0, wx.ALL, 5)
        
        sizer.Add(update_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # GitHub repository
        repo_box = wx.StaticBox(panel, label="Update Source (Advanced)")
        repo_sizer = wx.StaticBoxSizer(repo_box, wx.VERTICAL)
        
        repo_help = wx.StaticText(panel,
            label="These settings control where updates are downloaded from. "
                  "Do not modify unless directed by ACB technical support.")
        repo_help.Wrap(600)
        repo_sizer.Add(repo_help, 0, wx.ALL, 5)
        
        repo_row = wx.BoxSizer(wx.HORIZONTAL)
        repo_row.Add(wx.StaticText(panel, label="GitHub repository:"), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.github_repo = wx.TextCtrl(panel, value=self.config.updates.github_repo, 
                                      size=(300, -1))
        make_accessible(self.github_repo, "GitHub repository",
                       "Repository name in owner/repo format")
        repo_row.Add(self.github_repo, 1)
        repo_sizer.Add(repo_row, 0, wx.EXPAND | wx.ALL, 5)
        
        api_row = wx.BoxSizer(wx.HORIZONTAL)
        api_row.Add(wx.StaticText(panel, label="API URL:"), 0,
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.github_api = wx.TextCtrl(panel, value=self.config.updates.github_api_url,
                                     size=(400, -1))
        make_accessible(self.github_api, "GitHub API URL",
                       "URL for checking releases")
        api_row.Add(self.github_api, 1)
        repo_sizer.Add(api_row, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(repo_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Skipped version
        skip_box = wx.StaticBox(panel, label="Skipped Version")
        skip_sizer = wx.StaticBoxSizer(skip_box, wx.VERTICAL)
        
        skipped = self.config.updates.skipped_version or "None"
        self.skipped_label = wx.StaticText(panel, 
            label=f"Currently skipped version: {skipped}")
        skip_sizer.Add(self.skipped_label, 0, wx.ALL, 5)
        
        btn_clear_skip = wx.Button(panel, label="Clear Skipped Version")
        btn_clear_skip.Bind(wx.EVT_BUTTON, self._on_clear_skipped_version)
        make_button_accessible(btn_clear_skip, "Clear Skipped Version",
                              "Allow the skipped version to be offered again")
        skip_sizer.Add(btn_clear_skip, 0, wx.ALL, 5)
        
        sizer.Add(skip_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Updates")
    
    def _add_defaults_tab(self):
        """Add application defaults configuration tab."""
        panel = wx.ScrolledWindow(self.notebook)
        panel.SetScrollRate(0, 20)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Audio defaults
        audio_box = wx.StaticBox(panel, label="Audio Defaults")
        audio_sizer = wx.StaticBoxSizer(audio_box, wx.VERTICAL)
        
        vol_row = wx.BoxSizer(wx.HORIZONTAL)
        vol_row.Add(wx.StaticText(panel, label="Default volume:"), 0,
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_volume = wx.SpinCtrl(panel, 
                                         value=str(self.config.defaults.default_volume),
                                         min=0, max=100)
        make_accessible(self.default_volume, "Default volume", "Volume level 0-100")
        vol_row.Add(self.default_volume, 0)
        vol_row.Add(wx.StaticText(panel, label="%"), 0,
                   wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        audio_sizer.Add(vol_row, 0, wx.ALL, 5)
        
        speed_row = wx.BoxSizer(wx.HORIZONTAL)
        speed_row.Add(wx.StaticText(panel, label="Default playback speed:"), 0,
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_speed = wx.Choice(panel, 
            choices=["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"])
        speed_map = {0.5: 0, 0.75: 1, 1.0: 2, 1.25: 3, 1.5: 4, 1.75: 5, 2.0: 6}
        self.default_speed.SetSelection(speed_map.get(self.config.defaults.default_playback_speed, 2))
        make_accessible(self.default_speed, "Default playback speed",
                       "Speed for audio playback")
        speed_row.Add(self.default_speed, 0)
        audio_sizer.Add(speed_row, 0, wx.ALL, 5)
        
        skip_grid = wx.FlexGridSizer(2, 3, 5, 10)
        
        skip_grid.Add(wx.StaticText(panel, label="Skip forward:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.skip_forward = wx.SpinCtrl(panel, 
                                       value=str(self.config.defaults.default_skip_forward),
                                       min=5, max=120)
        make_accessible(self.skip_forward, "Skip forward seconds", "Seconds to skip forward")
        skip_grid.Add(self.skip_forward, 0)
        skip_grid.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL)
        
        skip_grid.Add(wx.StaticText(panel, label="Skip backward:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.skip_backward = wx.SpinCtrl(panel,
                                        value=str(self.config.defaults.default_skip_backward),
                                        min=5, max=120)
        make_accessible(self.skip_backward, "Skip backward seconds", "Seconds to skip backward")
        skip_grid.Add(self.skip_backward, 0)
        skip_grid.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL)
        
        audio_sizer.Add(skip_grid, 0, wx.ALL, 5)
        sizer.Add(audio_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # UI defaults
        ui_box = wx.StaticBox(panel, label="Interface Defaults")
        ui_sizer = wx.StaticBoxSizer(ui_box, wx.VERTICAL)
        
        tab_row = wx.BoxSizer(wx.HORIZONTAL)
        tab_row.Add(wx.StaticText(panel, label="Default tab:"), 0,
                   wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_tab = wx.Choice(panel, choices=[
            "Home", "Streams", "Podcasts", "Affiliates", "Resources",
            "Favorites", "Playlists", "Search", "Calendar"
        ])
        tab_map = {"home": 0, "streams": 1, "podcasts": 2, "affiliates": 3,
                  "resources": 4, "favorites": 5, "playlists": 6, "search": 7, "calendar": 8}
        self.default_tab.SetSelection(tab_map.get(self.config.defaults.default_tab, 0))
        make_accessible(self.default_tab, "Default tab", "Tab shown when app starts")
        tab_row.Add(self.default_tab, 0)
        ui_sizer.Add(tab_row, 0, wx.ALL, 5)
        
        theme_row = wx.BoxSizer(wx.HORIZONTAL)
        theme_row.Add(wx.StaticText(panel, label="Default theme:"), 0,
                     wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_theme = wx.Choice(panel, choices=[
            "System", "Light", "Dark", "High Contrast Light", "High Contrast Dark"
        ])
        theme_map = {"system": 0, "light": 1, "dark": 2, 
                    "high_contrast_light": 3, "high_contrast_dark": 4}
        self.default_theme.SetSelection(theme_map.get(self.config.defaults.default_theme, 0))
        make_accessible(self.default_theme, "Default theme", "Color theme for interface")
        theme_row.Add(self.default_theme, 0)
        ui_sizer.Add(theme_row, 0, wx.ALL, 5)
        
        font_row = wx.BoxSizer(wx.HORIZONTAL)
        font_row.Add(wx.StaticText(panel, label="Default font size:"), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_font_size = wx.SpinCtrl(panel,
                                            value=str(self.config.defaults.default_font_size),
                                            min=8, max=32)
        make_accessible(self.default_font_size, "Default font size", "Font size in points")
        font_row.Add(self.default_font_size, 0)
        font_row.Add(wx.StaticText(panel, label="pt"), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        ui_sizer.Add(font_row, 0, wx.ALL, 5)
        
        sizer.Add(ui_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Behavior defaults
        behavior_box = wx.StaticBox(panel, label="Behavior Defaults")
        behavior_sizer = wx.StaticBoxSizer(behavior_box, wx.VERTICAL)
        
        self.start_minimized = wx.CheckBox(panel, label="Start minimized")
        self.start_minimized.SetValue(self.config.defaults.start_minimized)
        make_accessible(self.start_minimized, "Start minimized",
                       "Start app minimized to system tray")
        behavior_sizer.Add(self.start_minimized, 0, wx.ALL, 5)
        
        self.minimize_to_tray = wx.CheckBox(panel, label="Minimize to system tray")
        self.minimize_to_tray.SetValue(self.config.defaults.minimize_to_tray)
        make_accessible(self.minimize_to_tray, "Minimize to system tray",
                       "Minimize to tray instead of taskbar")
        behavior_sizer.Add(self.minimize_to_tray, 0, wx.ALL, 5)
        
        self.close_to_tray = wx.CheckBox(panel, label="Close to system tray")
        self.close_to_tray.SetValue(self.config.defaults.close_to_tray)
        make_accessible(self.close_to_tray, "Close to system tray",
                       "Closing window hides to tray instead of exiting")
        behavior_sizer.Add(self.close_to_tray, 0, wx.ALL, 5)
        
        self.remember_position = wx.CheckBox(panel, label="Remember window position")
        self.remember_position.SetValue(self.config.defaults.remember_window_position)
        make_accessible(self.remember_position, "Remember window position",
                       "Save and restore window position between sessions")
        behavior_sizer.Add(self.remember_position, 0, wx.ALL, 5)
        
        self.auto_sync = wx.CheckBox(panel, label="Auto-sync data on startup")
        self.auto_sync.SetValue(self.config.defaults.auto_sync_on_startup)
        make_accessible(self.auto_sync, "Auto-sync data on startup",
                       "Automatically refresh content when app starts")
        behavior_sizer.Add(self.auto_sync, 0, wx.ALL, 5)
        
        sizer.Add(behavior_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Defaults")
    
    def _add_experimental_tab(self):
        """Add experimental/developer features tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Warning
        warn_box = wx.StaticBox(panel, label="⚠️ Experimental Features")
        warn_sizer = wx.StaticBoxSizer(warn_box, wx.VERTICAL)
        
        warn_text = wx.StaticText(panel,
            label="These features are experimental and may not work correctly. "
                  "Enable at your own risk. They may be removed in future versions.")
        warn_text.SetForegroundColour(wx.Colour(200, 100, 0))
        warn_text.Wrap(600)
        warn_sizer.Add(warn_text, 0, wx.ALL, 5)
        
        sizer.Add(warn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Debug options
        debug_box = wx.StaticBox(panel, label="Developer Options")
        debug_sizer = wx.StaticBoxSizer(debug_box, wx.VERTICAL)
        
        self.debug_logging = wx.CheckBox(panel, label="Enable debug logging")
        make_accessible(self.debug_logging, "Enable debug logging",
                       "Write detailed logs for troubleshooting")
        debug_sizer.Add(self.debug_logging, 0, wx.ALL, 5)
        
        self.show_perf = wx.CheckBox(panel, label="Show performance metrics in status bar")
        make_accessible(self.show_perf, "Show performance metrics",
                       "Display memory and CPU usage")
        debug_sizer.Add(self.show_perf, 0, wx.ALL, 5)
        
        sizer.Add(debug_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Export/Import config
        config_box = wx.StaticBox(panel, label="Configuration Backup")
        config_sizer = wx.StaticBoxSizer(config_box, wx.HORIZONTAL)
        
        btn_export = wx.Button(panel, label="Export Configuration...")
        btn_export.Bind(wx.EVT_BUTTON, self._on_export_config)
        make_button_accessible(btn_export, "Export Configuration",
                              "Save all settings to a file")
        config_sizer.Add(btn_export, 0, wx.ALL, 5)
        
        btn_import = wx.Button(panel, label="Import Configuration...")
        btn_import.Bind(wx.EVT_BUTTON, self._on_import_config)
        make_button_accessible(btn_import, "Import Configuration",
                              "Load settings from a backup file")
        config_sizer.Add(btn_import, 0, wx.ALL, 5)
        
        sizer.Add(config_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Experimental")
    
    def _create_buttons(self) -> wx.BoxSizer:
        """Create dialog buttons."""
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Reset button
        btn_reset = wx.Button(self, label="Reset All to Defaults")
        btn_reset.Bind(wx.EVT_BUTTON, self._on_reset_defaults)
        btn_reset.SetForegroundColour(wx.Colour(180, 50, 50))
        make_button_accessible(btn_reset, "Reset All to Defaults",
                              "Restore all advanced settings to original values")
        btn_sizer.Add(btn_reset, 0, wx.RIGHT, 20)
        
        btn_sizer.AddStretchSpacer()
        
        # Validate button
        btn_validate = wx.Button(self, label="Validate")
        btn_validate.Bind(wx.EVT_BUTTON, self._on_validate)
        make_button_accessible(btn_validate, "Validate",
                              "Check all settings for errors without saving")
        btn_sizer.Add(btn_validate, 0, wx.RIGHT, 5)
        
        # Standard buttons
        btn_ok = wx.Button(self, wx.ID_OK, "Save Changes")
        btn_ok.Bind(wx.EVT_BUTTON, self._on_save)
        make_button_accessible(btn_ok, "Save Changes",
                              "Save all advanced settings")
        
        btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        make_button_accessible(btn_cancel, "Cancel",
                              "Close without saving changes")
        
        btn_ok.SetDefault()
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)
        
        return btn_sizer
    
    def _browse_folder(self, text_ctrl: wx.TextCtrl):
        """Open folder browser dialog."""
        dlg = wx.DirDialog(self, "Choose a directory:", 
                          defaultPath=text_ctrl.GetValue(),
                          style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            text_ctrl.SetValue(dlg.GetPath())
            announce(f"Selected: {dlg.GetPath()}")
        dlg.Destroy()
    
    def _open_folder(self, path: str):
        """Open folder in file explorer."""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", path], check=False)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            wx.MessageBox(f"Could not open folder: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_clear_skipped_version(self, event):
        """Clear the skipped version."""
        self.config.updates.skipped_version = None
        self.skipped_label.SetLabel("Currently skipped version: None")
        announce("Skipped version cleared")
    
    def _on_export_config(self, event):
        """Export configuration to file."""
        with wx.FileDialog(self, "Export Configuration",
                          wildcard="JSON files (*.json)|*.json",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    path = dlg.GetPath()
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
                    wx.MessageBox(f"Configuration exported to:\n{path}", 
                                "Export Successful", wx.OK | wx.ICON_INFORMATION)
                    announce("Configuration exported successfully")
                except Exception as e:
                    wx.MessageBox(f"Export failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_import_config(self, event):
        """Import configuration from file."""
        with wx.FileDialog(self, "Import Configuration",
                          wildcard="JSON files (*.json)|*.json",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                if wx.MessageBox(
                    "Importing will replace all current settings.\n\n"
                    "Do you want to continue?",
                    "Confirm Import",
                    wx.YES_NO | wx.ICON_WARNING
                ) == wx.YES:
                    try:
                        path = dlg.GetPath()
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Close and reopen dialog with imported config
                        self.config = AppConfig.from_dict(data)
                        wx.MessageBox("Configuration imported. Please restart "
                                    "the application for changes to take effect.",
                                    "Import Successful", wx.OK | wx.ICON_INFORMATION)
                        self.EndModal(wx.ID_OK)
                        
                    except Exception as e:
                        wx.MessageBox(f"Import failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_validate(self, event):
        """Validate all settings."""
        errors = self._validate_all()
        if errors:
            self.validation_status.SetLabel(f"⚠️ {len(errors)} validation error(s)")
            error_text = "\n".join(f"• {e}" for e in errors)
            wx.MessageBox(f"Validation errors found:\n\n{error_text}",
                        "Validation Failed", wx.OK | wx.ICON_WARNING)
            announce(f"{len(errors)} validation errors found")
        else:
            self.validation_status.SetLabel("✓ All settings valid")
            wx.MessageBox("All settings are valid.", "Validation Passed",
                        wx.OK | wx.ICON_INFORMATION)
            announce("All settings are valid")
    
    def _validate_all(self) -> List[str]:
        """Validate all settings and return list of errors."""
        errors = []
        
        # Validate base URL
        valid, msg = FieldValidator.validate_url(self.base_url.GetValue(), "Base URL")
        if not valid:
            errors.append(msg)
        
        # Validate data source URLs
        for key, controls in self.data_source_controls.items():
            valid, msg = FieldValidator.validate_url(
                controls["url"].GetValue(), f"{key.replace('_', ' ').title()} URL")
            if not valid:
                errors.append(msg)
        
        # Validate proxy URL if enabled
        if self.proxy_enabled.GetValue():
            valid, msg = FieldValidator.validate_url(
                self.proxy_url.GetValue(), "Proxy URL")
            if not valid:
                errors.append(msg)
            if not self.proxy_url.GetValue().strip():
                errors.append("Proxy URL: Cannot be empty when proxy is enabled")
        
        # Validate paths
        for key, ctrl in self.path_controls.items():
            valid, msg = FieldValidator.validate_path(
                ctrl.GetValue(), f"{key.replace('_', ' ').title()} path")
            if not valid:
                errors.append(msg)
        
        # Validate GitHub repo format
        repo = self.github_repo.GetValue()
        if repo and "/" not in repo:
            errors.append("GitHub repository: Must be in 'owner/repo' format")
        
        return errors
    
    def _on_reset_defaults(self, event):
        """Reset all settings to defaults."""
        if wx.MessageBox(
            "This will reset ALL advanced settings to their default values.\n\n"
            "This action cannot be undone. Continue?",
            "Reset to Defaults",
            wx.YES_NO | wx.ICON_WARNING
        ) == wx.YES:
            # Create fresh default config
            default_config = AppConfig()
            
            # Update all controls
            self.base_url.SetValue(default_config.live_data.base_url)
            
            # Data sources
            default_sources = {
                "streams": default_config.live_data.streams,
                "podcasts": default_config.live_data.podcasts,
                "state_affiliates": default_config.live_data.state_affiliates,
                "special_interest_groups": default_config.live_data.special_interest_groups,
                "publications": default_config.live_data.publications,
                "categories": default_config.live_data.categories,
                "acb_sites": default_config.live_data.acb_sites,
            }
            
            for key, source in default_sources.items():
                self.data_source_controls[key]["url"].SetValue(source.live_url)
                self.data_source_controls[key]["enabled"].SetValue(source.enabled)
                self.data_source_controls[key]["cache"].SetValue(source.cache_duration_hours)
            
            # Network
            self.timeout.SetValue(default_config.network.timeout_seconds)
            self.retry_count.SetValue(default_config.network.retry_count)
            self.retry_delay.SetValue(default_config.network.retry_delay_seconds)
            self.user_agent.SetValue(default_config.network.user_agent)
            self.proxy_enabled.SetValue(default_config.network.proxy_enabled)
            self.proxy_url.SetValue(default_config.network.proxy_url or "")
            
            # Paths
            self.path_controls["app_data"].SetValue(default_config.paths.app_data_dir)
            self.path_controls["cache"].SetValue(default_config.paths.cache_dir)
            self.path_controls["logs"].SetValue(default_config.paths.logs_dir)
            self.path_controls["downloads"].SetValue(default_config.paths.downloads_dir)
            self.path_controls["recordings"].SetValue(default_config.paths.recordings_dir)
            
            # Updates
            self.updates_enabled.SetValue(default_config.updates.enabled)
            self.check_startup.SetValue(default_config.updates.check_on_startup)
            self.check_interval.SetValue(default_config.updates.check_interval_hours)
            self.github_repo.SetValue(default_config.updates.github_repo)
            self.github_api.SetValue(default_config.updates.github_api_url)
            
            # Defaults
            self.default_volume.SetValue(default_config.defaults.default_volume)
            speed_map = {0.5: 0, 0.75: 1, 1.0: 2, 1.25: 3, 1.5: 4, 1.75: 5, 2.0: 6}
            self.default_speed.SetSelection(
                speed_map.get(default_config.defaults.default_playback_speed, 2))
            self.skip_forward.SetValue(default_config.defaults.default_skip_forward)
            self.skip_backward.SetValue(default_config.defaults.default_skip_backward)
            
            tab_map = {"home": 0, "streams": 1, "podcasts": 2, "affiliates": 3,
                      "resources": 4, "favorites": 5, "playlists": 6, "search": 7, "calendar": 8}
            self.default_tab.SetSelection(tab_map.get(default_config.defaults.default_tab, 0))
            
            theme_map = {"system": 0, "light": 1, "dark": 2,
                        "high_contrast_light": 3, "high_contrast_dark": 4}
            self.default_theme.SetSelection(
                theme_map.get(default_config.defaults.default_theme, 0))
            
            self.default_font_size.SetValue(default_config.defaults.default_font_size)
            self.start_minimized.SetValue(default_config.defaults.start_minimized)
            self.minimize_to_tray.SetValue(default_config.defaults.minimize_to_tray)
            self.close_to_tray.SetValue(default_config.defaults.close_to_tray)
            self.remember_position.SetValue(default_config.defaults.remember_window_position)
            self.auto_sync.SetValue(default_config.defaults.auto_sync_on_startup)
            
            announce("All settings reset to defaults")
            wx.MessageBox("All settings have been reset to defaults.\n\n"
                        "Click Save to apply, or Cancel to discard.",
                        "Reset Complete", wx.OK | wx.ICON_INFORMATION)
    
    def _on_save(self, event):
        """Save all settings."""
        # Validate first
        errors = self._validate_all()
        if errors:
            self.validation_status.SetLabel(f"⚠️ {len(errors)} validation error(s)")
            error_text = "\n".join(f"• {e}" for e in errors[:5])
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more"
            
            if wx.MessageBox(
                f"The following validation errors were found:\n\n{error_text}\n\n"
                "Save anyway?",
                "Validation Errors",
                wx.YES_NO | wx.ICON_WARNING
            ) != wx.YES:
                return
        
        # Save all values to config
        self._apply_to_config()
        
        # Save to file
        if save_config():
            announce("Advanced settings saved successfully")
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox("Failed to save configuration file.",
                        "Save Error", wx.OK | wx.ICON_ERROR)
    
    def _apply_to_config(self):
        """Apply UI values to configuration object."""
        # Base URL
        self.config.live_data.base_url = self.base_url.GetValue()
        
        # Data sources
        source_attrs = {
            "streams": self.config.live_data.streams,
            "podcasts": self.config.live_data.podcasts,
            "state_affiliates": self.config.live_data.state_affiliates,
            "special_interest_groups": self.config.live_data.special_interest_groups,
            "publications": self.config.live_data.publications,
            "categories": self.config.live_data.categories,
            "acb_sites": self.config.live_data.acb_sites,
        }
        
        for key, source in source_attrs.items():
            source.live_url = self.data_source_controls[key]["url"].GetValue()
            source.enabled = self.data_source_controls[key]["enabled"].GetValue()
            source.cache_duration_hours = self.data_source_controls[key]["cache"].GetValue()
        
        # Network
        self.config.network.timeout_seconds = self.timeout.GetValue()
        self.config.network.retry_count = self.retry_count.GetValue()
        self.config.network.retry_delay_seconds = self.retry_delay.GetValue()
        self.config.network.user_agent = self.user_agent.GetValue()
        self.config.network.proxy_enabled = self.proxy_enabled.GetValue()
        self.config.network.proxy_url = self.proxy_url.GetValue() or None
        
        # Paths
        self.config.paths.app_data_dir = self.path_controls["app_data"].GetValue()
        self.config.paths.cache_dir = self.path_controls["cache"].GetValue()
        self.config.paths.logs_dir = self.path_controls["logs"].GetValue()
        self.config.paths.downloads_dir = self.path_controls["downloads"].GetValue()
        self.config.paths.recordings_dir = self.path_controls["recordings"].GetValue()
        
        # Updates
        self.config.updates.enabled = self.updates_enabled.GetValue()
        self.config.updates.check_on_startup = self.check_startup.GetValue()
        self.config.updates.check_interval_hours = self.check_interval.GetValue()
        self.config.updates.github_repo = self.github_repo.GetValue()
        self.config.updates.github_api_url = self.github_api.GetValue()
        
        # Defaults
        self.config.defaults.default_volume = self.default_volume.GetValue()
        speed_values = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        self.config.defaults.default_playback_speed = speed_values[self.default_speed.GetSelection()]
        self.config.defaults.default_skip_forward = self.skip_forward.GetValue()
        self.config.defaults.default_skip_backward = self.skip_backward.GetValue()
        
        tab_names = ["home", "streams", "podcasts", "affiliates", "resources",
                    "favorites", "playlists", "search", "calendar"]
        self.config.defaults.default_tab = tab_names[self.default_tab.GetSelection()]
        
        theme_names = ["system", "light", "dark", "high_contrast_light", "high_contrast_dark"]
        self.config.defaults.default_theme = theme_names[self.default_theme.GetSelection()]
        
        self.config.defaults.default_font_size = self.default_font_size.GetValue()
        self.config.defaults.start_minimized = self.start_minimized.GetValue()
        self.config.defaults.minimize_to_tray = self.minimize_to_tray.GetValue()
        self.config.defaults.close_to_tray = self.close_to_tray.GetValue()
        self.config.defaults.remember_window_position = self.remember_position.GetValue()
        self.config.defaults.auto_sync_on_startup = self.auto_sync.GetValue()


# =============================================================================
# Simple/Advanced Mode Manager
# =============================================================================

class UserModeManager:
    """Manages Simple vs Advanced user mode."""
    
    SIMPLE_MODE = "simple"
    ADVANCED_MODE = "advanced"
    
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._mode = self._load_mode()
    
    def _load_mode(self) -> str:
        """Load user mode from settings."""
        # Check if mode is stored in settings (we'll add this field)
        return getattr(self.settings, 'user_mode', self.SIMPLE_MODE)
    
    @property
    def mode(self) -> str:
        """Get current user mode."""
        return self._mode
    
    @property
    def is_simple_mode(self) -> bool:
        """Check if in simple mode."""
        return self._mode == self.SIMPLE_MODE
    
    @property
    def is_advanced_mode(self) -> bool:
        """Check if in advanced mode."""
        return self._mode == self.ADVANCED_MODE
    
    def set_mode(self, mode: str):
        """Set user mode."""
        if mode in (self.SIMPLE_MODE, self.ADVANCED_MODE):
            self._mode = mode
    
    def get_visible_settings_tabs(self) -> List[str]:
        """Get list of settings tabs visible in current mode."""
        base_tabs = ["General", "Appearance", "Playback", "Accessibility"]
        
        if self.is_advanced_mode:
            return base_tabs + ["Storage", "Home Tab", "System Tray", "Advanced"]
        return base_tabs
    
    def get_visible_menu_items(self) -> Dict[str, bool]:
        """Get visibility of menu items in current mode."""
        return {
            "advanced_settings": self.is_advanced_mode,
            "developer_tools": self.is_advanced_mode,
            "export_import": self.is_advanced_mode,
            "keyboard_shortcuts": True,  # Always visible
            "about": True,
        }


def show_advanced_settings(parent, config: AppConfig, settings: AppSettings,
                          skip_warning: bool = False) -> bool:
    """
    Show advanced settings dialog with admin authentication.
    
    Args:
        parent: Parent window
        config: Application configuration
        settings: User settings
        skip_warning: If True, skip the warning dialog
        
    Returns:
        True if settings were changed and saved
    """
    # Require admin authentication
    try:
        from .admin_auth_ui import require_admin_login
        from .github_admin import AdminRole
        
        success, session = require_admin_login(
            parent, 
            AdminRole.CONFIG_ADMIN,
            "modifying advanced settings"
        )
        if not success:
            announce("Admin authentication required for advanced settings")
            return False
    except ImportError:
        # Fallback if admin module not available - show warning
        pass
    
    # Show warning first
    if not skip_warning:
        warning = AdvancedSettingsWarningDialog(parent)
        result = warning.ShowModal()
        should_show_again = warning.should_show_again()
        warning.Destroy()
        
        if result != wx.ID_OK:
            return False
        
        # Store preference (would need to add this to settings)
        # settings.show_advanced_warning = should_show_again
    
    # Show advanced settings
    dialog = AdvancedSettingsDialog(parent, config, settings)
    result = dialog.ShowModal()
    dialog.Destroy()
    
    return result == wx.ID_OK
