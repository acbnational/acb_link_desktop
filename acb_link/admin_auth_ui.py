"""
ACB Link Desktop - Admin Authentication UI (GitHub-Based)

Provides dialogs for admin login using GitHub Personal Access Tokens.
WCAG 2.2 AA compliant with full keyboard navigation.

Authentication Flow:
1. User enters their GitHub Personal Access Token
2. App validates token against GitHub API
3. App checks user's repository permissions
4. Role assigned based on GitHub permissions

No passwords stored - only GitHub token in memory during session.
"""

import logging
import webbrowser
from typing import Optional, Tuple

import wx
import wx.adv

from .accessibility import announce, make_accessible, make_button_accessible
from .github_admin import AdminRole, AdminSession, get_github_admin_manager

logger = logging.getLogger(__name__)


class AdminLoginDialog(wx.Dialog):
    """Dialog for administrator login using GitHub PAT."""

    def __init__(self, parent: Optional[wx.Window] = None, context: str = "Admin Access"):
        super().__init__(
            parent,
            title="Administrator Login - ACB Link",
            size=wx.Size(500, 420),
            style=wx.DEFAULT_DIALOG_STYLE,
        )

        self.context = context
        self.manager = get_github_admin_manager()
        self.session: Optional[AdminSession] = None

        self._build_ui()
        self.Centre()

        announce(
            "Administrator login dialog. Enter your GitHub Personal Access Token to access admin features."
        )

    def _build_ui(self):
        """Build the login dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(panel, label="GitHub Administrator Login")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        make_accessible(header, "GitHub Administrator Login", "Login using GitHub token")
        main_sizer.Add(header, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        # Info text
        info = wx.StaticText(
            panel,
            label="ACB Link uses GitHub for admin authentication.\n\n"
            "Your admin role is determined by your permissions on the\n"
            "ACB Link configuration repository:\n"
            "• Organization Owner → Super Admin\n"
            "• Repository Admin → Config Admin\n"
            "• Repository Write → Affiliate Admin",
        )
        info.Wrap(450)
        main_sizer.Add(info, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Token input
        token_label = wx.StaticText(panel, label="GitHub Personal Access &Token:")
        main_sizer.Add(token_label, 0, wx.LEFT | wx.RIGHT, 15)

        self.token_ctrl = wx.TextCtrl(panel, size=wx.Size(450, -1), style=wx.TE_PASSWORD)
        make_accessible(
            self.token_ctrl,
            "GitHub Personal Access Token",
            "Enter your GitHub PAT. Requires read:org scope.",
        )
        main_sizer.Add(self.token_ctrl, 0, wx.ALL | wx.EXPAND, 15)

        # Help link
        help_sizer = wx.BoxSizer(wx.HORIZONTAL)
        help_text = wx.StaticText(panel, label="Need a token?")
        help_sizer.Add(help_text, 0, wx.ALIGN_CENTER_VERTICAL)

        help_link = wx.adv.HyperlinkCtrl(
            panel, label="Create a GitHub Personal Access Token", url=""
        )
        help_link.Bind(wx.adv.EVT_HYPERLINK, self._on_help_link)
        make_accessible(help_link, "Create token link", "Opens GitHub token creation page")
        help_sizer.Add(help_link, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        main_sizer.Add(help_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Scope info
        scope_info = wx.StaticText(
            panel, label="Required token scopes: read:org (to check membership)"
        )
        scope_info.SetForegroundColour(wx.Colour(100, 100, 100))
        main_sizer.Add(scope_info, 0, wx.LEFT | wx.RIGHT, 15)

        # Status message
        self.status_label = wx.StaticText(panel, label="")
        main_sizer.Add(self.status_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "&Cancel")
        make_button_accessible(cancel_btn, "Cancel", "Close without logging in")

        self.login_btn = wx.Button(panel, wx.ID_OK, "&Login")
        self.login_btn.SetDefault()
        make_button_accessible(self.login_btn, "Login", "Authenticate with GitHub token")

        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.login_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        panel.SetSizer(main_sizer)

        # Bind events
        self.login_btn.Bind(wx.EVT_BUTTON, self._on_login)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

        # Set focus
        self.token_ctrl.SetFocus()

    def _on_key(self, event):
        """Handle keyboard shortcuts."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        elif event.GetKeyCode() == wx.WXK_RETURN:
            self._on_login(event)
        else:
            event.Skip()

    def _on_help_link(self, event):
        """Open GitHub token creation page."""
        url = "https://github.com/settings/tokens/new?scopes=read:org&description=ACB%20Link%20Desktop%20Admin"
        webbrowser.open(url)

    def _on_login(self, event):
        """Handle login button click."""
        token = self.token_ctrl.GetValue().strip()

        if not token:
            self.status_label.SetLabel("Please enter a GitHub Personal Access Token")
            self.status_label.SetForegroundColour(wx.Colour(200, 50, 50))
            self.token_ctrl.SetFocus()
            announce("Error: Please enter a token")
            return

        if len(token) < 20:
            self.status_label.SetLabel("Token appears too short. Check your token.")
            self.status_label.SetForegroundColour(wx.Colour(200, 50, 50))
            self.token_ctrl.SetFocus()
            announce("Error: Token too short")
            return

        # Show busy state
        self.status_label.SetLabel("Verifying with GitHub...")
        self.status_label.SetForegroundColour(wx.Colour(100, 100, 100))
        self.login_btn.Disable()
        self.Update()
        wx.Yield()  # Allow UI to update

        # Attempt authentication
        try:
            success, message, session = self.manager.authenticate(token)

            if success and session:
                self.session = session

                # Show success message based on role
                role_desc = {
                    AdminRole.USER: "You have read-only access (no admin privileges).",
                    AdminRole.AFFILIATE_ADMIN: "You can review and approve affiliate corrections.",
                    AdminRole.CONFIG_ADMIN: "You can modify organization settings.",
                    AdminRole.SUPER_ADMIN: "You have full administrative access.",
                }

                if session.role == AdminRole.USER:
                    # User doesn't have admin access
                    self.status_label.SetLabel(
                        f"Logged in as {session.display_name}, but no admin permissions.\n"
                        "Contact ACB IT for admin access."
                    )
                    self.status_label.SetForegroundColour(wx.Colour(200, 100, 0))
                    self.login_btn.Enable()
                    announce("Login successful but no admin permissions")
                else:
                    announce(f"Login successful. {role_desc[session.role]}")
                    self.EndModal(wx.ID_OK)
            else:
                self.status_label.SetLabel(message)
                self.status_label.SetForegroundColour(wx.Colour(200, 50, 50))
                self.login_btn.Enable()
                self.token_ctrl.SetFocus()
                announce(f"Login failed: {message}")

        except Exception as e:
            self.status_label.SetLabel(f"Error: {str(e)}")
            self.status_label.SetForegroundColour(wx.Colour(200, 50, 50))
            self.login_btn.Enable()
            logger.error(f"Login error: {e}")
            announce(f"Login error: {str(e)}")


class AdminSessionPanel(wx.Panel):
    """Panel showing current admin session status."""

    def __init__(self, parent: wx.Window):
        super().__init__(parent)

        self.manager = get_github_admin_manager()
        self._build_ui()

    def _build_ui(self):
        """Build the session panel UI."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Session info
        self.session_label = wx.StaticText(self, label="")
        sizer.Add(self.session_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        # Login/Logout button
        self.auth_btn = wx.Button(self, label="Login")
        make_button_accessible(self.auth_btn, "Login/Logout", "Login or logout as administrator")
        self.auth_btn.Bind(wx.EVT_BUTTON, self._on_auth_button)
        sizer.Add(self.auth_btn, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        self._update_display()

    def _update_display(self):
        """Update the session display."""
        session = self.manager.current_session
        if session and session.role != AdminRole.USER:
            self.session_label.SetLabel(f"Logged in: {session.display_name} ({session.role.name})")
            self.session_label.SetForegroundColour(wx.Colour(0, 100, 0))
            self.auth_btn.SetLabel("Logout")
        else:
            self.session_label.SetLabel("Not logged in (read-only mode)")
            self.session_label.SetForegroundColour(wx.Colour(100, 100, 100))
            self.auth_btn.SetLabel("Admin Login")

    def _on_auth_button(self, event):
        """Handle login/logout button."""
        if self.manager.is_authenticated:
            # Logout
            self.manager.logout()
            self._update_display()
            announce("Logged out")
        else:
            # Show login dialog
            dialog = AdminLoginDialog(self.GetTopLevelParent())
            if dialog.ShowModal() == wx.ID_OK:
                self._update_display()
            dialog.Destroy()


class AdminRequiredDialog(wx.Dialog):
    """Dialog shown when admin access is required for an action."""

    def __init__(
        self,
        parent: Optional[wx.Window],
        context: str = "this action",
        required_role: AdminRole = AdminRole.AFFILIATE_ADMIN,
    ):
        super().__init__(
            parent,
            title="Administrator Access Required",
            size=wx.Size(500, 320),
            style=wx.DEFAULT_DIALOG_STYLE,
        )

        self.required_role = required_role
        self.context = context
        self._build_ui()
        self.Centre()

    def _build_ui(self):
        """Build the dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Icon and message
        icon_sizer = wx.BoxSizer(wx.HORIZONTAL)

        icon = wx.StaticBitmap(
            panel,
            bitmap=wx.BitmapBundle.FromBitmap(
                wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX, wx.Size(48, 48))
            ),
        )
        icon_sizer.Add(icon, 0, wx.ALL, 10)

        role_desc = {
            AdminRole.AFFILIATE_ADMIN: "Affiliate Admin (repository write access)",
            AdminRole.CONFIG_ADMIN: "Config Admin (repository admin access)",
            AdminRole.SUPER_ADMIN: "Super Admin (organization owner)",
        }

        msg = wx.StaticText(
            panel,
            label=f"Administrator access is required for {self.context}.\n\n"
            f"Required role: {role_desc.get(self.required_role, self.required_role.name)}\n\n"
            f"You'll need to log in with a GitHub account that has the\n"
            f"appropriate permissions on the ACB Link config repository.",
        )
        msg.Wrap(400)
        icon_sizer.Add(msg, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        sizer.Add(icon_sizer, 1, wx.EXPAND)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "&Cancel")
        make_button_accessible(cancel_btn, "Cancel", "Cancel this action")

        login_btn = wx.Button(panel, wx.ID_OK, "&Login with GitHub")
        login_btn.SetDefault()
        make_button_accessible(login_btn, "Login with GitHub", "Open GitHub login dialog")

        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(login_btn, 0)

        sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        panel.SetSizer(sizer)


def require_admin_login(
    parent: Optional[wx.Window],
    required_role: AdminRole = AdminRole.AFFILIATE_ADMIN,
    context: str = "this action",
) -> Tuple[bool, Optional[AdminSession]]:
    """
    Ensure admin is logged in with sufficient role, prompting if needed.

    Args:
        parent: Parent window for dialogs
        required_role: Minimum role required
        context: Description of what requires admin access

    Returns:
        (success, session) - session is the AdminSession if successful
    """
    manager = get_github_admin_manager()

    # Check if already authenticated with sufficient role
    session = manager.current_session
    if session and session.has_role(required_role):
        return True, session

    # Show the required dialog
    dialog = AdminRequiredDialog(parent, context, required_role)
    result = dialog.ShowModal()
    dialog.Destroy()

    if result == wx.ID_OK:
        # Show login dialog
        login_dialog = AdminLoginDialog(parent, context)
        if login_dialog.ShowModal() == wx.ID_OK:
            session = login_dialog.session
            if session and session.has_role(required_role):
                login_dialog.Destroy()
                return True, session
            else:
                # Show insufficient permissions message
                wx.MessageBox(
                    f"Your account doesn't have the required permissions.\n\n"
                    f"Required: {required_role.name}\n"
                    f"Your role: {session.role.name if session else 'None'}",
                    "Insufficient Permissions",
                    wx.OK | wx.ICON_WARNING,
                    parent,
                )
        login_dialog.Destroy()

    return False, None


def show_admin_login_dialog(
    parent: Optional[wx.Window] = None,
) -> Tuple[bool, Optional[AdminSession]]:
    """
    Show the admin login dialog.

    Returns:
        (success, session) - session is the AdminSession if successful
    """
    dialog = AdminLoginDialog(parent)
    result = dialog.ShowModal()
    session = dialog.session
    dialog.Destroy()

    if result == wx.ID_OK and session and session.role != AdminRole.USER:
        return True, session
    return False, None
