"""
Announcement UI components for ACB Link Desktop.

Provides:
- Announcement widget for home page
- Announcement history dialog
- Critical announcement popup dialog
- Admin announcement publisher dialog
- Announcement detail viewer
"""

import logging
import webbrowser
from datetime import datetime
from typing import List, Optional

import wx
import wx.html2
import wx.adv

from .announcements import (
    Announcement,
    AnnouncementCategory,
    AnnouncementManager,
    AnnouncementPriority,
    AnnouncementSettings,
    CATEGORY_LABELS,
    CATEGORY_ICONS,
    PRIORITY_LABELS,
    get_announcement_manager,
)

try:
    from .accessibility import make_accessible, make_button_accessible, make_list_accessible, announce
except ImportError:
    def make_accessible(ctrl, name, desc=""): pass
    def make_button_accessible(btn, name, desc=""): pass
    def make_list_accessible(lst, name, desc=""): pass
    def announce(msg): pass

logger = logging.getLogger(__name__)


class AnnouncementWidget(wx.Panel):
    """
    Widget displaying announcements on the home page.

    Shows unread announcements with priority indicators.
    Always appears first when there are unread announcements.
    """

    def __init__(
        self,
        parent: wx.Window,
        manager: Optional[AnnouncementManager] = None,
        max_items: int = 5,
    ):
        """
        Initialize the announcement widget.

        Args:
            parent: Parent window
            manager: Announcement manager (uses global if None)
            max_items: Maximum announcements to show
        """
        super().__init__(parent)

        self.manager = manager or get_announcement_manager()
        self.max_items = max_items
        self._announcement_buttons: List[wx.Button] = []

        self._create_ui()
        self._bind_events()
        self.refresh()

        # Register for updates
        self.manager.add_new_announcements_callback(self._on_new_announcements)

    def _create_ui(self):
        """Create the widget UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header with icon and title
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.header_icon = wx.StaticText(self, label="📢")
        self.header_icon.SetFont(
            self.header_icon.GetFont().Larger().Larger()
        )
        header_sizer.Add(self.header_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        self.header_label = wx.StaticText(self, label="Announcements")
        self.header_label.SetFont(
            self.header_label.GetFont().Bold().Larger()
        )
        header_sizer.Add(self.header_label, 1, wx.ALIGN_CENTER_VERTICAL)

        # Unread count badge
        self.unread_badge = wx.StaticText(self, label="")
        self.unread_badge.SetForegroundColour(wx.Colour(255, 255, 255))
        self.unread_badge.SetBackgroundColour(wx.Colour(220, 53, 69))
        header_sizer.Add(self.unread_badge, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        # View all button
        self.view_all_btn = wx.Button(self, label="View All")
        make_button_accessible(
            self.view_all_btn,
            "View all announcements",
            "Opens the announcement history dialog"
        )
        header_sizer.Add(self.view_all_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        # Mark all read button
        self.mark_read_btn = wx.Button(self, label="Mark All Read")
        make_button_accessible(
            self.mark_read_btn,
            "Mark all announcements as read",
            "Marks all current announcements as read"
        )
        header_sizer.Add(self.mark_read_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # Separator
        main_sizer.Add(
            wx.StaticLine(self),
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT,
            8,
        )

        # Announcements list panel
        self.list_panel = wx.Panel(self)
        self.list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_panel.SetSizer(self.list_sizer)

        main_sizer.Add(self.list_panel, 1, wx.EXPAND | wx.ALL, 8)

        # No announcements message
        self.no_announcements_label = wx.StaticText(
            self.list_panel,
            label="No new announcements",
            style=wx.ALIGN_CENTER,
        )
        self.no_announcements_label.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.list_sizer.Add(
            self.no_announcements_label,
            0,
            wx.EXPAND | wx.ALL,
            16,
        )

        self.SetSizer(main_sizer)

        # Accessibility
        make_accessible(
            self,
            "Announcements widget",
            "Shows recent announcements from ACB Link"
        )

    def _bind_events(self):
        """Bind event handlers."""
        self.view_all_btn.Bind(wx.EVT_BUTTON, self._on_view_all)
        self.mark_read_btn.Bind(wx.EVT_BUTTON, self._on_mark_all_read)

    def _on_new_announcements(self, announcements: List[Announcement]):
        """Handle new announcements."""
        self.refresh()

    def _on_view_all(self, event):
        """Open announcement history dialog."""
        dialog = AnnouncementHistoryDialog(self.GetTopLevelParent(), self.manager)
        dialog.ShowModal()
        dialog.Destroy()
        self.refresh()

    def _on_mark_all_read(self, event):
        """Mark all announcements as read."""
        self.manager.mark_all_as_read()
        self.refresh()
        announce("All announcements marked as read")

    def _on_announcement_click(self, announcement: Announcement):
        """Handle announcement click."""
        dialog = AnnouncementDetailDialog(
            self.GetTopLevelParent(),
            announcement,
            self.manager,
        )
        dialog.ShowModal()
        dialog.Destroy()
        self.refresh()

    def refresh(self):
        """Refresh the announcement list."""
        # Clear existing items
        for btn in self._announcement_buttons:
            btn.Destroy()
        self._announcement_buttons.clear()

        # Get unread announcements
        announcements = self.manager.get_unread_announcements()
        unread_count = len(announcements)

        # Update badge
        if unread_count > 0:
            self.unread_badge.SetLabel(f" {unread_count} ")
            self.unread_badge.Show()
        else:
            self.unread_badge.Hide()

        # Update mark read button
        self.mark_read_btn.Enable(unread_count > 0)

        # Show/hide no announcements message
        self.no_announcements_label.Show(unread_count == 0)

        # Add announcement items
        for announcement in announcements[: self.max_items]:
            item = self._create_announcement_item(announcement)
            self.list_sizer.Add(item, 0, wx.EXPAND | wx.BOTTOM, 8)
            self._announcement_buttons.append(item)

        self.list_panel.Layout()
        self.Layout()

    def _create_announcement_item(self, announcement: Announcement) -> wx.Button:
        """Create a button for an announcement."""
        # Create label with priority indicator
        priority_indicator = ""
        if announcement.priority == AnnouncementPriority.CRITICAL:
            priority_indicator = "🚨 "
        elif announcement.priority == AnnouncementPriority.HIGH:
            priority_indicator = "❗ "

        label = (
            f"{priority_indicator}{announcement.category_icon} "
            f"{announcement.title}\n"
            f"{announcement.summary[:100]}{'...' if len(announcement.summary) > 100 else ''}\n"
            f"{announcement.age_display}"
        )

        btn = wx.Button(self.list_panel, label=label, style=wx.BU_LEFT)
        btn.SetMinSize((-1, 70))

        # Color by priority
        if announcement.priority == AnnouncementPriority.CRITICAL:
            btn.SetBackgroundColour(wx.Colour(255, 235, 235))
        elif announcement.priority == AnnouncementPriority.HIGH:
            btn.SetBackgroundColour(wx.Colour(255, 248, 225))

        # Bind click
        btn.Bind(
            wx.EVT_BUTTON,
            lambda e, a=announcement: self._on_announcement_click(a),
        )

        make_button_accessible(
            btn,
            f"{announcement.priority_label} priority: {announcement.title}",
            f"{announcement.category_label}. {announcement.summary}. {announcement.age_display}",
        )

        return btn

    def has_unread(self) -> bool:
        """Check if there are unread announcements."""
        return self.manager.get_unread_count() > 0


class AnnouncementDetailDialog(wx.Dialog):
    """Dialog showing full announcement details."""

    def __init__(
        self,
        parent: wx.Window,
        announcement: Announcement,
        manager: AnnouncementManager,
    ):
        """
        Initialize the detail dialog.

        Args:
            parent: Parent window
            announcement: Announcement to display
            manager: Announcement manager
        """
        super().__init__(
            parent,
            title=announcement.title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(600, 500),
        )

        self.announcement = announcement
        self.manager = manager

        self._create_ui()
        self._bind_events()

        # Mark as read when viewed
        self.manager.mark_as_read(announcement.id)

        self.CenterOnParent()

    def _create_ui(self):
        """Create the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header panel
        header_panel = wx.Panel(self)
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        # Category and priority
        meta_sizer = wx.BoxSizer(wx.HORIZONTAL)

        category_label = wx.StaticText(
            header_panel,
            label=f"{self.announcement.category_icon} {self.announcement.category_label}",
        )
        meta_sizer.Add(category_label, 0, wx.ALIGN_CENTER_VERTICAL)

        meta_sizer.Add((16, 0))

        priority_label = wx.StaticText(
            header_panel,
            label=f"Priority: {self.announcement.priority_label}",
        )
        if self.announcement.priority == AnnouncementPriority.CRITICAL:
            priority_label.SetForegroundColour(wx.Colour(220, 53, 69))
        elif self.announcement.priority == AnnouncementPriority.HIGH:
            priority_label.SetForegroundColour(wx.Colour(255, 193, 7))
        meta_sizer.Add(priority_label, 0, wx.ALIGN_CENTER_VERTICAL)

        meta_sizer.AddStretchSpacer()

        date_label = wx.StaticText(
            header_panel,
            label=self.announcement.age_display,
        )
        date_label.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        meta_sizer.Add(date_label, 0, wx.ALIGN_CENTER_VERTICAL)

        header_sizer.Add(meta_sizer, 0, wx.EXPAND | wx.BOTTOM, 8)

        # Title
        title_label = wx.StaticText(header_panel, label=self.announcement.title)
        title_label.SetFont(title_label.GetFont().Bold().Larger().Larger())
        header_sizer.Add(title_label, 0, wx.EXPAND | wx.BOTTOM, 4)

        # Author
        author_label = wx.StaticText(
            header_panel,
            label=f"By {self.announcement.author}",
        )
        author_label.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        header_sizer.Add(author_label, 0, wx.EXPAND)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 16)

        # Separator
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

        # Content - try to use HTML view for Markdown rendering
        try:
            self.content_view = wx.html2.WebView.New(self)
            html_content = self._markdown_to_html(self.announcement.content)
            self.content_view.SetPage(html_content, "")
            main_sizer.Add(self.content_view, 1, wx.EXPAND | wx.ALL, 16)
        except Exception:
            # Fallback to plain text
            self.content_view = wx.TextCtrl(
                self,
                value=self.announcement.content,
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
            )
            main_sizer.Add(self.content_view, 1, wx.EXPAND | wx.ALL, 16)

        # Link button (if available)
        if self.announcement.link_url:
            link_btn = wx.Button(
                self,
                label=self.announcement.link_text or "Learn More",
            )
            link_btn.Bind(
                wx.EVT_BUTTON,
                lambda e: webbrowser.open(self.announcement.link_url),
            )
            main_sizer.Add(link_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if not self.manager.is_read(self.announcement.id):
            self.mark_unread_btn = wx.Button(self, label="Mark as Unread")
            self.mark_unread_btn.Bind(wx.EVT_BUTTON, self._on_mark_unread)
            btn_sizer.Add(self.mark_unread_btn, 0, wx.RIGHT, 8)

        btn_sizer.AddStretchSpacer()

        close_btn = wx.Button(self, wx.ID_CLOSE, label="Close")
        close_btn.SetDefault()
        btn_sizer.Add(close_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 16)

        self.SetSizer(main_sizer)

        # Accessibility
        make_accessible(
            self,
            f"Announcement: {self.announcement.title}",
            self.announcement.summary,
        )

    def _bind_events(self):
        """Bind event handlers."""
        self.Bind(wx.EVT_BUTTON, self._on_close, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_key(self, event):
        """Handle key press."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CLOSE)
        else:
            event.Skip()

    def _on_close(self, event):
        """Handle close button."""
        self.EndModal(wx.ID_CLOSE)

    def _on_mark_unread(self, event):
        """Mark announcement as unread."""
        self.manager.mark_as_unread(self.announcement.id)
        announce("Marked as unread")

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert Markdown to HTML (basic conversion)."""
        # Basic Markdown to HTML conversion
        import html
        import re

        text = html.escape(markdown_text)

        # Headers
        text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
        text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)

        # Bold and italic
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

        # Links
        text = re.sub(
            r"\[(.+?)\]\((.+?)\)",
            r'<a href="\2">\1</a>',
            text,
        )

        # Lists
        text = re.sub(r"^- (.+)$", r"<li>\1</li>", text, flags=re.MULTILINE)
        text = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", text)

        # Paragraphs
        text = re.sub(r"\n\n", "</p><p>", text)
        text = f"<p>{text}</p>"

        # Wrap in HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    padding: 8px;
                    color: #333;
                }}
                h1, h2, h3 {{ margin-top: 16px; margin-bottom: 8px; }}
                ul {{ padding-left: 20px; }}
                a {{ color: #0066cc; }}
            </style>
        </head>
        <body>{text}</body>
        </html>
        """


class AnnouncementHistoryDialog(wx.Dialog):
    """Dialog showing announcement history."""

    def __init__(
        self,
        parent: wx.Window,
        manager: AnnouncementManager,
    ):
        """
        Initialize the history dialog.

        Args:
            parent: Parent window
            manager: Announcement manager
        """
        super().__init__(
            parent,
            title="Announcement History",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(700, 550),
        )

        self.manager = manager

        self._create_ui()
        self._bind_events()
        self._refresh_list()

        self.CenterOnParent()

    def _create_ui(self):
        """Create the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Filter bar
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Show read/unread filter
        filter_sizer.Add(
            wx.StaticText(self, label="Show:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )

        self.filter_choice = wx.Choice(
            self,
            choices=["All", "Unread Only", "Read Only"],
        )
        self.filter_choice.SetSelection(0)
        make_accessible(
            self.filter_choice,
            "Filter announcements",
            "Choose which announcements to show",
        )
        filter_sizer.Add(self.filter_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)

        # Category filter
        filter_sizer.Add(
            wx.StaticText(self, label="Category:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )

        categories = ["All Categories"] + [
            f"{CATEGORY_ICONS[cat]} {CATEGORY_LABELS[cat]}"
            for cat in AnnouncementCategory
        ]
        self.category_choice = wx.Choice(self, choices=categories)
        self.category_choice.SetSelection(0)
        make_accessible(
            self.category_choice,
            "Filter by category",
            "Choose which category of announcements to show",
        )
        filter_sizer.Add(self.category_choice, 0, wx.ALIGN_CENTER_VERTICAL)

        filter_sizer.AddStretchSpacer()

        # Refresh button
        self.refresh_btn = wx.Button(self, label="Check for New")
        make_button_accessible(
            self.refresh_btn,
            "Check for new announcements",
            "Fetch latest announcements from server",
        )
        filter_sizer.Add(self.refresh_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        main_sizer.Add(filter_sizer, 0, wx.EXPAND | wx.ALL, 12)

        # Announcement list
        self.list_ctrl = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
        )
        self.list_ctrl.AppendColumn("", width=30)  # Icon
        self.list_ctrl.AppendColumn("Title", width=250)
        self.list_ctrl.AppendColumn("Category", width=100)
        self.list_ctrl.AppendColumn("Priority", width=80)
        self.list_ctrl.AppendColumn("Date", width=120)
        self.list_ctrl.AppendColumn("Status", width=70)

        make_list_accessible(
            self.list_ctrl,
            "Announcement list",
            "List of all announcements. Press Enter to view details.",
        )

        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)

        # Action buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.view_btn = wx.Button(self, label="View")
        make_button_accessible(self.view_btn, "View announcement", "View full announcement details")
        action_sizer.Add(self.view_btn, 0, wx.RIGHT, 8)

        self.mark_read_btn = wx.Button(self, label="Mark as Read")
        make_button_accessible(self.mark_read_btn, "Mark as read", "Mark selected announcement as read")
        action_sizer.Add(self.mark_read_btn, 0, wx.RIGHT, 8)

        self.mark_unread_btn = wx.Button(self, label="Mark as Unread")
        make_button_accessible(self.mark_unread_btn, "Mark as unread", "Mark selected announcement as unread")
        action_sizer.Add(self.mark_unread_btn, 0)

        action_sizer.AddStretchSpacer()

        self.mark_all_btn = wx.Button(self, label="Mark All as Read")
        make_button_accessible(self.mark_all_btn, "Mark all as read", "Mark all announcements as read")
        action_sizer.Add(self.mark_all_btn, 0)

        main_sizer.Add(action_sizer, 0, wx.EXPAND | wx.ALL, 12)

        # Close button
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        close_btn = wx.Button(self, wx.ID_CLOSE, label="Close")
        close_btn.SetDefault()
        btn_sizer.Add(close_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(main_sizer)

        # Accessibility
        make_accessible(
            self,
            "Announcement History",
            "View and manage all announcements",
        )

    def _bind_events(self):
        """Bind event handlers."""
        self.filter_choice.Bind(wx.EVT_CHOICE, self._on_filter_change)
        self.category_choice.Bind(wx.EVT_CHOICE, self._on_filter_change)
        self.refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh)
        self.view_btn.Bind(wx.EVT_BUTTON, self._on_view)
        self.mark_read_btn.Bind(wx.EVT_BUTTON, self._on_mark_read)
        self.mark_unread_btn.Bind(wx.EVT_BUTTON, self._on_mark_unread)
        self.mark_all_btn.Bind(wx.EVT_BUTTON, self._on_mark_all_read)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection_change)
        self.Bind(wx.EVT_BUTTON, self._on_close, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_key(self, event):
        """Handle key press."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CLOSE)
        else:
            event.Skip()

    def _on_close(self, event):
        """Handle close button."""
        self.EndModal(wx.ID_CLOSE)

    def _on_filter_change(self, event):
        """Handle filter change."""
        self._refresh_list()

    def _on_refresh(self, event):
        """Handle refresh button."""
        self.refresh_btn.Disable()
        announce("Checking for new announcements")

        def on_complete(success, message):
            self.refresh_btn.Enable()
            self._refresh_list()
            if success:
                announce(message)
            else:
                announce(f"Failed to check announcements: {message}")

        self.manager.fetch_announcements(callback=on_complete)

    def _on_view(self, event):
        """View selected announcement."""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            return

        announcement_id = self.list_ctrl.GetItemData(selected)
        announcement = self.manager.get_announcement_by_id(
            self._announcements[announcement_id].id
        )

        if announcement:
            dialog = AnnouncementDetailDialog(self, announcement, self.manager)
            dialog.ShowModal()
            dialog.Destroy()
            self._refresh_list()

    def _on_item_activated(self, event):
        """Handle item double-click."""
        self._on_view(event)

    def _on_selection_change(self, event):
        """Handle selection change."""
        has_selection = self.list_ctrl.GetFirstSelected() != -1
        self.view_btn.Enable(has_selection)
        self.mark_read_btn.Enable(has_selection)
        self.mark_unread_btn.Enable(has_selection)

    def _on_mark_read(self, event):
        """Mark selected as read."""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            return

        announcement = self._announcements[self.list_ctrl.GetItemData(selected)]
        self.manager.mark_as_read(announcement.id)
        self._refresh_list()
        announce("Marked as read")

    def _on_mark_unread(self, event):
        """Mark selected as unread."""
        selected = self.list_ctrl.GetFirstSelected()
        if selected == -1:
            return

        announcement = self._announcements[self.list_ctrl.GetItemData(selected)]
        self.manager.mark_as_unread(announcement.id)
        self._refresh_list()
        announce("Marked as unread")

    def _on_mark_all_read(self, event):
        """Mark all as read."""
        self.manager.mark_all_as_read()
        self._refresh_list()
        announce("All announcements marked as read")

    def _refresh_list(self):
        """Refresh the announcement list."""
        self.list_ctrl.DeleteAllItems()

        # Get filter settings
        filter_type = self.filter_choice.GetSelection()
        category_index = self.category_choice.GetSelection()

        # Get announcements based on filter
        if filter_type == 1:  # Unread only
            announcements = self.manager.get_all_announcements(
                include_expired=True, include_read=False
            )
        elif filter_type == 2:  # Read only
            all_announcements = self.manager.get_all_announcements(
                include_expired=True, include_read=True
            )
            announcements = [
                a for a in all_announcements if self.manager.is_read(a.id)
            ]
        else:  # All
            announcements = self.manager.get_all_announcements(
                include_expired=True, include_read=True
            )

        # Filter by category
        if category_index > 0:
            category = AnnouncementCategory(category_index - 1)
            announcements = [a for a in announcements if a.category == category]

        self._announcements = announcements

        # Populate list
        for i, announcement in enumerate(announcements):
            # Icon column
            status_icon = "●" if not self.manager.is_read(announcement.id) else "○"
            index = self.list_ctrl.InsertItem(i, status_icon)

            # Title
            self.list_ctrl.SetItem(index, 1, announcement.title)

            # Category
            self.list_ctrl.SetItem(
                index, 2,
                f"{announcement.category_icon} {announcement.category_label}"
            )

            # Priority
            self.list_ctrl.SetItem(index, 3, announcement.priority_label)

            # Date
            self.list_ctrl.SetItem(index, 4, announcement.age_display)

            # Status
            status = "Unread" if not self.manager.is_read(announcement.id) else "Read"
            self.list_ctrl.SetItem(index, 5, status)

            # Store index for retrieval
            self.list_ctrl.SetItemData(index, i)

            # Color by priority
            if announcement.priority == AnnouncementPriority.CRITICAL:
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(255, 235, 235))
            elif announcement.priority == AnnouncementPriority.HIGH:
                self.list_ctrl.SetItemBackgroundColour(index, wx.Colour(255, 248, 225))

        # Update button states
        self._on_selection_change(None)


class CriticalAnnouncementDialog(wx.Dialog):
    """
    Modal dialog for critical announcements.

    Requires user acknowledgment before dismissing.
    """

    def __init__(
        self,
        parent: wx.Window,
        announcement: Announcement,
        manager: AnnouncementManager,
    ):
        """
        Initialize the critical announcement dialog.

        Args:
            parent: Parent window
            announcement: Critical announcement to display
            manager: Announcement manager
        """
        super().__init__(
            parent,
            title="⚠️ Critical Announcement",
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP,
            size=(500, 400),
        )

        self.announcement = announcement
        self.manager = manager

        # Set background to highlight urgency
        self.SetBackgroundColour(wx.Colour(255, 235, 235))

        self._create_ui()
        self._bind_events()

        self.CenterOnParent()

        # Play alert sound
        try:
            wx.Bell()
        except Exception:
            pass

    def _create_ui(self):
        """Create the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Warning icon and header
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        warning_label = wx.StaticText(self, label="🚨")
        warning_label.SetFont(
            warning_label.GetFont().Larger().Larger().Larger()
        )
        header_sizer.Add(warning_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)

        header_text = wx.BoxSizer(wx.VERTICAL)

        title_label = wx.StaticText(self, label=self.announcement.title)
        title_label.SetFont(title_label.GetFont().Bold().Larger().Larger())
        title_label.SetForegroundColour(wx.Colour(180, 0, 0))
        header_text.Add(title_label, 0, wx.EXPAND)

        category_label = wx.StaticText(
            self,
            label=f"{self.announcement.category_label} • {self.announcement.age_display}",
        )
        category_label.SetForegroundColour(wx.Colour(100, 100, 100))
        header_text.Add(category_label, 0, wx.EXPAND | wx.TOP, 4)

        header_sizer.Add(header_text, 1, wx.EXPAND)
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 16)

        # Content
        content_text = wx.TextCtrl(
            self,
            value=self.announcement.content,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.BORDER_NONE,
        )
        content_text.SetBackgroundColour(self.GetBackgroundColour())
        main_sizer.Add(content_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)

        # Link if available
        if self.announcement.link_url:
            link_btn = wx.Button(
                self,
                label=self.announcement.link_text or "More Information",
            )
            link_btn.Bind(
                wx.EVT_BUTTON,
                lambda e: webbrowser.open(self.announcement.link_url),
            )
            main_sizer.Add(link_btn, 0, wx.LEFT | wx.RIGHT | wx.TOP, 16)

        # Acknowledgment
        main_sizer.Add((0, 16))

        if self.announcement.requires_acknowledgment:
            self.ack_checkbox = wx.CheckBox(
                self,
                label="I understand and acknowledge this announcement",
            )
            main_sizer.Add(self.ack_checkbox, 0, wx.LEFT | wx.RIGHT, 16)
            main_sizer.Add((0, 8))

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()

        self.acknowledge_btn = wx.Button(self, label="Acknowledge")
        self.acknowledge_btn.SetDefault()
        if self.announcement.requires_acknowledgment:
            self.acknowledge_btn.Disable()
        btn_sizer.Add(self.acknowledge_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 16)

        self.SetSizer(main_sizer)

        # Accessibility
        make_accessible(
            self,
            f"Critical announcement: {self.announcement.title}",
            self.announcement.summary,
        )

        # Announce for screen readers
        announce(
            f"Critical announcement: {self.announcement.title}. "
            f"{self.announcement.summary}"
        )

    def _bind_events(self):
        """Bind event handlers."""
        self.acknowledge_btn.Bind(wx.EVT_BUTTON, self._on_acknowledge)
        if hasattr(self, "ack_checkbox"):
            self.ack_checkbox.Bind(wx.EVT_CHECKBOX, self._on_checkbox)

    def _on_checkbox(self, event):
        """Handle checkbox change."""
        self.acknowledge_btn.Enable(self.ack_checkbox.IsChecked())

    def _on_acknowledge(self, event):
        """Handle acknowledge button."""
        self.manager.acknowledge_critical(self.announcement.id)
        announce("Announcement acknowledged")
        self.EndModal(wx.ID_OK)


class AdminAnnouncementDialog(wx.Dialog):
    """
    Dialog for administrators to create and publish announcements.
    """

    def __init__(
        self,
        parent: wx.Window,
        manager: AnnouncementManager,
        announcement: Optional[Announcement] = None,
    ):
        """
        Initialize the admin dialog.

        Args:
            parent: Parent window
            manager: Announcement manager
            announcement: Existing announcement to edit (None for new)
        """
        title = "Edit Announcement" if announcement else "Create Announcement"
        super().__init__(
            parent,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(650, 700),
        )

        self.manager = manager
        self.announcement = announcement

        self._create_ui()
        self._bind_events()

        if announcement:
            self._populate_from_announcement(announcement)

        self.CenterOnParent()

    def _create_ui(self):
        """Create the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Scrolled panel for form
        scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll.SetScrollRate(0, 20)
        form_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        form_sizer.Add(wx.StaticText(scroll, label="Title:"), 0, wx.BOTTOM, 4)
        self.title_ctrl = wx.TextCtrl(scroll)
        make_accessible(self.title_ctrl, "Announcement title", "Enter the title for this announcement")
        form_sizer.Add(self.title_ctrl, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Summary
        form_sizer.Add(wx.StaticText(scroll, label="Summary (shown in widget):"), 0, wx.BOTTOM, 4)
        self.summary_ctrl = wx.TextCtrl(scroll, style=wx.TE_MULTILINE, size=(-1, 60))
        make_accessible(self.summary_ctrl, "Summary", "Brief summary shown in the widget")
        form_sizer.Add(self.summary_ctrl, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Content
        form_sizer.Add(wx.StaticText(scroll, label="Content (Markdown supported):"), 0, wx.BOTTOM, 4)
        self.content_ctrl = wx.TextCtrl(scroll, style=wx.TE_MULTILINE, size=(-1, 150))
        make_accessible(self.content_ctrl, "Content", "Full announcement content with Markdown formatting")
        form_sizer.Add(self.content_ctrl, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Category and Priority row
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Category
        cat_sizer = wx.BoxSizer(wx.VERTICAL)
        cat_sizer.Add(wx.StaticText(scroll, label="Category:"), 0, wx.BOTTOM, 4)
        self.category_choice = wx.Choice(
            scroll,
            choices=[
                f"{CATEGORY_ICONS[cat]} {CATEGORY_LABELS[cat]}"
                for cat in AnnouncementCategory
            ],
        )
        self.category_choice.SetSelection(0)
        make_accessible(self.category_choice, "Category", "Select the announcement category")
        cat_sizer.Add(self.category_choice, 0, wx.EXPAND)
        row_sizer.Add(cat_sizer, 1, wx.RIGHT, 16)

        # Priority
        pri_sizer = wx.BoxSizer(wx.VERTICAL)
        pri_sizer.Add(wx.StaticText(scroll, label="Priority:"), 0, wx.BOTTOM, 4)
        self.priority_choice = wx.Choice(
            scroll,
            choices=[PRIORITY_LABELS[p] for p in AnnouncementPriority],
        )
        self.priority_choice.SetSelection(2)  # Normal
        make_accessible(self.priority_choice, "Priority", "Select the announcement priority level")
        pri_sizer.Add(self.priority_choice, 0, wx.EXPAND)
        row_sizer.Add(pri_sizer, 1)

        form_sizer.Add(row_sizer, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Author
        form_sizer.Add(wx.StaticText(scroll, label="Author:"), 0, wx.BOTTOM, 4)
        self.author_ctrl = wx.TextCtrl(scroll, value="ACB Link Team")
        make_accessible(self.author_ctrl, "Author", "Author name for this announcement")
        form_sizer.Add(self.author_ctrl, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Version (optional)
        form_sizer.Add(wx.StaticText(scroll, label="Version (optional, for updates):"), 0, wx.BOTTOM, 4)
        self.version_ctrl = wx.TextCtrl(scroll)
        make_accessible(self.version_ctrl, "Version", "Associated app version for update announcements")
        form_sizer.Add(self.version_ctrl, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Link row
        link_row = wx.BoxSizer(wx.HORIZONTAL)

        link_url_sizer = wx.BoxSizer(wx.VERTICAL)
        link_url_sizer.Add(wx.StaticText(scroll, label="Link URL (optional):"), 0, wx.BOTTOM, 4)
        self.link_url_ctrl = wx.TextCtrl(scroll)
        make_accessible(self.link_url_ctrl, "Link URL", "Optional URL for more information")
        link_url_sizer.Add(self.link_url_ctrl, 0, wx.EXPAND)
        link_row.Add(link_url_sizer, 2, wx.RIGHT, 16)

        link_text_sizer = wx.BoxSizer(wx.VERTICAL)
        link_text_sizer.Add(wx.StaticText(scroll, label="Link Text:"), 0, wx.BOTTOM, 4)
        self.link_text_ctrl = wx.TextCtrl(scroll, value="Learn More")
        make_accessible(self.link_text_ctrl, "Link text", "Text to display for the link")
        link_text_sizer.Add(self.link_text_ctrl, 0, wx.EXPAND)
        link_row.Add(link_text_sizer, 1)

        form_sizer.Add(link_row, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Expiration
        form_sizer.Add(wx.StaticText(scroll, label="Expiration:"), 0, wx.BOTTOM, 4)
        exp_row = wx.BoxSizer(wx.HORIZONTAL)

        self.expires_checkbox = wx.CheckBox(scroll, label="Expires on:")
        make_accessible(self.expires_checkbox, "Set expiration", "Check to set an expiration date")
        exp_row.Add(self.expires_checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        self.expires_picker = wx.adv.DatePickerCtrl(scroll)
        self.expires_picker.Disable()
        make_accessible(self.expires_picker, "Expiration date", "Date when announcement expires")
        exp_row.Add(self.expires_picker, 0, wx.ALIGN_CENTER_VERTICAL)

        form_sizer.Add(exp_row, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Options
        form_sizer.Add(wx.StaticText(scroll, label="Options:"), 0, wx.BOTTOM, 8)

        self.dismissible_checkbox = wx.CheckBox(scroll, label="User can dismiss (mark as read)")
        self.dismissible_checkbox.SetValue(True)
        make_accessible(self.dismissible_checkbox, "Dismissible", "Allow users to mark as read")
        form_sizer.Add(self.dismissible_checkbox, 0, wx.BOTTOM, 4)

        self.requires_ack_checkbox = wx.CheckBox(
            scroll, label="Requires explicit acknowledgment (critical only)"
        )
        make_accessible(
            self.requires_ack_checkbox,
            "Requires acknowledgment",
            "User must explicitly acknowledge before dismissing",
        )
        form_sizer.Add(self.requires_ack_checkbox, 0, wx.BOTTOM, 4)

        self.show_in_widget_checkbox = wx.CheckBox(scroll, label="Show in home widget")
        self.show_in_widget_checkbox.SetValue(True)
        make_accessible(self.show_in_widget_checkbox, "Show in widget", "Display in home page widget")
        form_sizer.Add(self.show_in_widget_checkbox, 0, wx.BOTTOM, 12)

        scroll.SetSizer(form_sizer)
        main_sizer.Add(scroll, 1, wx.EXPAND | wx.ALL, 16)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.preview_btn = wx.Button(self, label="Preview")
        make_button_accessible(self.preview_btn, "Preview", "Preview the announcement")
        btn_sizer.Add(self.preview_btn, 0, wx.RIGHT, 8)

        btn_sizer.AddStretchSpacer()

        cancel_btn = wx.Button(self, wx.ID_CANCEL, label="Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 8)

        self.publish_btn = wx.Button(self, label="Publish")
        self.publish_btn.SetDefault()
        make_button_accessible(self.publish_btn, "Publish", "Publish this announcement")
        btn_sizer.Add(self.publish_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        self.SetSizer(main_sizer)

        # Accessibility
        make_accessible(
            self,
            "Create Announcement" if not self.announcement else "Edit Announcement",
            "Form for creating or editing an announcement",
        )

    def _bind_events(self):
        """Bind event handlers."""
        self.expires_checkbox.Bind(wx.EVT_CHECKBOX, self._on_expires_toggle)
        self.preview_btn.Bind(wx.EVT_BUTTON, self._on_preview)
        self.publish_btn.Bind(wx.EVT_BUTTON, self._on_publish)
        self.priority_choice.Bind(wx.EVT_CHOICE, self._on_priority_change)

    def _on_expires_toggle(self, event):
        """Handle expiration toggle."""
        self.expires_picker.Enable(self.expires_checkbox.IsChecked())

    def _on_priority_change(self, event):
        """Handle priority change."""
        is_critical = self.priority_choice.GetSelection() == 4
        self.requires_ack_checkbox.Enable(is_critical)
        if not is_critical:
            self.requires_ack_checkbox.SetValue(False)

    def _on_preview(self, event):
        """Preview the announcement."""
        announcement = self._build_announcement()
        if announcement:
            dialog = AnnouncementDetailDialog(self, announcement, self.manager)
            dialog.ShowModal()
            dialog.Destroy()

    def _on_publish(self, event):
        """Publish the announcement."""
        announcement = self._build_announcement()
        if announcement:
            if self.manager.publish_announcement(announcement):
                announce("Announcement published")
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox(
                    "Failed to publish announcement",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )

    def _build_announcement(self) -> Optional[Announcement]:
        """Build announcement from form data."""
        title = self.title_ctrl.GetValue().strip()
        summary = self.summary_ctrl.GetValue().strip()
        content = self.content_ctrl.GetValue().strip()

        if not title:
            wx.MessageBox("Title is required", "Validation Error", wx.OK | wx.ICON_WARNING)
            self.title_ctrl.SetFocus()
            return None

        if not summary:
            wx.MessageBox("Summary is required", "Validation Error", wx.OK | wx.ICON_WARNING)
            self.summary_ctrl.SetFocus()
            return None

        if not content:
            wx.MessageBox("Content is required", "Validation Error", wx.OK | wx.ICON_WARNING)
            self.content_ctrl.SetFocus()
            return None

        # Get expiration
        expires_at = None
        if self.expires_checkbox.IsChecked():
            exp_date = self.expires_picker.GetValue()
            expires_at = datetime(
                exp_date.GetYear(),
                exp_date.GetMonth() + 1,
                exp_date.GetDay(),
            ).isoformat()

        # Build announcement
        return self.manager.create_announcement(
            title=title,
            summary=summary,
            content=content,
            priority=AnnouncementPriority(self.priority_choice.GetSelection()),
            category=AnnouncementCategory(self.category_choice.GetSelection()),
            author=self.author_ctrl.GetValue().strip() or "ACB Link Team",
            version=self.version_ctrl.GetValue().strip() or None,
            link_url=self.link_url_ctrl.GetValue().strip() or None,
            link_text=self.link_text_ctrl.GetValue().strip() or None,
            expires_at=expires_at,
            dismissible=self.dismissible_checkbox.IsChecked(),
            requires_acknowledgment=self.requires_ack_checkbox.IsChecked(),
            show_in_widget=self.show_in_widget_checkbox.IsChecked(),
        )

    def _populate_from_announcement(self, announcement: Announcement):
        """Populate form from existing announcement."""
        self.title_ctrl.SetValue(announcement.title)
        self.summary_ctrl.SetValue(announcement.summary)
        self.content_ctrl.SetValue(announcement.content)
        self.category_choice.SetSelection(int(announcement.category))
        self.priority_choice.SetSelection(int(announcement.priority))
        self.author_ctrl.SetValue(announcement.author)

        if announcement.version:
            self.version_ctrl.SetValue(announcement.version)

        if announcement.link_url:
            self.link_url_ctrl.SetValue(announcement.link_url)

        if announcement.link_text:
            self.link_text_ctrl.SetValue(announcement.link_text)

        if announcement.expires_at:
            self.expires_checkbox.SetValue(True)
            self.expires_picker.Enable(True)
            # Set date from ISO string
            try:
                exp_date = datetime.fromisoformat(announcement.expires_at)
                wx_date = wx.DateTime(
                    exp_date.day,
                    exp_date.month - 1,
                    exp_date.year,
                )
                self.expires_picker.SetValue(wx_date)
            except ValueError:
                pass

        self.dismissible_checkbox.SetValue(announcement.dismissible)
        self.requires_ack_checkbox.SetValue(announcement.requires_acknowledgment)
        self.show_in_widget_checkbox.SetValue(announcement.show_in_widget)


class AnnouncementSettingsPanel(wx.Panel):
    """Panel for announcement settings in the settings dialog."""

    def __init__(self, parent: wx.Window, settings: AnnouncementSettings):
        """
        Initialize the settings panel.

        Args:
            parent: Parent window
            settings: Current announcement settings
        """
        super().__init__(parent)

        self.settings = settings
        self._create_ui()

    def _create_ui(self):
        """Create the panel UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Checking section
        check_box = wx.StaticBox(self, label="Checking for Announcements")
        check_sizer = wx.StaticBoxSizer(check_box, wx.VERTICAL)

        self.check_startup_cb = wx.CheckBox(self, label="Check for announcements on startup")
        self.check_startup_cb.SetValue(self.settings.check_on_startup)
        make_accessible(
            self.check_startup_cb,
            "Check on startup",
            "Check for new announcements when the app starts",
        )
        check_sizer.Add(self.check_startup_cb, 0, wx.ALL, 8)

        interval_row = wx.BoxSizer(wx.HORIZONTAL)
        interval_row.Add(
            wx.StaticText(self, label="Check interval (minutes, 0 = manual only):"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.interval_spin = wx.SpinCtrl(self, min=0, max=1440, initial=self.settings.check_interval_minutes)
        make_accessible(self.interval_spin, "Check interval", "How often to check for announcements in minutes")
        interval_row.Add(self.interval_spin, 0)
        check_sizer.Add(interval_row, 0, wx.ALL, 8)

        main_sizer.Add(check_sizer, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Notifications section
        notif_box = wx.StaticBox(self, label="Notifications")
        notif_sizer = wx.StaticBoxSizer(notif_box, wx.VERTICAL)

        self.native_notif_cb = wx.CheckBox(self, label="Show native OS notifications")
        self.native_notif_cb.SetValue(self.settings.show_native_notifications)
        make_accessible(
            self.native_notif_cb,
            "Native notifications",
            "Show notifications in the system notification area",
        )
        notif_sizer.Add(self.native_notif_cb, 0, wx.ALL, 8)

        self.critical_dialog_cb = wx.CheckBox(self, label="Show popup dialog for critical announcements")
        self.critical_dialog_cb.SetValue(self.settings.show_critical_dialogs)
        make_accessible(
            self.critical_dialog_cb,
            "Critical dialogs",
            "Show a popup dialog for critical announcements",
        )
        notif_sizer.Add(self.critical_dialog_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.sound_cb = wx.CheckBox(self, label="Play sound for notifications")
        self.sound_cb.SetValue(self.settings.notification_sound)
        make_accessible(self.sound_cb, "Notification sound", "Play a sound when new announcements arrive")
        notif_sizer.Add(self.sound_cb, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Minimum priority for notification
        priority_row = wx.BoxSizer(wx.HORIZONTAL)
        priority_row.Add(
            wx.StaticText(self, label="Minimum priority for notification:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.min_priority_choice = wx.Choice(
            self,
            choices=[PRIORITY_LABELS[p] for p in AnnouncementPriority],
        )
        self.min_priority_choice.SetSelection(int(self.settings.min_priority_for_notification))
        make_accessible(
            self.min_priority_choice,
            "Minimum notification priority",
            "Only show notifications for announcements at or above this priority",
        )
        priority_row.Add(self.min_priority_choice, 0)
        notif_sizer.Add(priority_row, 0, wx.ALL, 8)

        main_sizer.Add(notif_sizer, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Widget section
        widget_box = wx.StaticBox(self, label="Home Widget")
        widget_sizer = wx.StaticBoxSizer(widget_box, wx.VERTICAL)

        self.show_widget_cb = wx.CheckBox(self, label="Show announcements widget on home page")
        self.show_widget_cb.SetValue(self.settings.show_widget)
        make_accessible(self.show_widget_cb, "Show widget", "Display the announcements widget on the home page")
        widget_sizer.Add(self.show_widget_cb, 0, wx.ALL, 8)

        max_row = wx.BoxSizer(wx.HORIZONTAL)
        max_row.Add(
            wx.StaticText(self, label="Maximum announcements in widget:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.max_items_spin = wx.SpinCtrl(self, min=1, max=20, initial=self.settings.widget_max_items)
        make_accessible(self.max_items_spin, "Max widget items", "Maximum announcements to show in the widget")
        max_row.Add(self.max_items_spin, 0)
        widget_sizer.Add(max_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        main_sizer.Add(widget_sizer, 0, wx.EXPAND | wx.BOTTOM, 12)

        # History section
        history_box = wx.StaticBox(self, label="History")
        history_sizer = wx.StaticBoxSizer(history_box, wx.VERTICAL)

        days_row = wx.BoxSizer(wx.HORIZONTAL)
        days_row.Add(
            wx.StaticText(self, label="Keep read announcements for (days):"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.history_days_spin = wx.SpinCtrl(self, min=7, max=365, initial=self.settings.keep_history_days)
        make_accessible(self.history_days_spin, "History retention", "How long to keep read announcements")
        days_row.Add(self.history_days_spin, 0)
        history_sizer.Add(days_row, 0, wx.ALL, 8)

        main_sizer.Add(history_sizer, 0, wx.EXPAND)

        self.SetSizer(main_sizer)

    def get_settings(self) -> AnnouncementSettings:
        """Get settings from the panel."""
        return AnnouncementSettings(
            check_on_startup=self.check_startup_cb.IsChecked(),
            check_interval_minutes=self.interval_spin.GetValue(),
            show_native_notifications=self.native_notif_cb.IsChecked(),
            show_critical_dialogs=self.critical_dialog_cb.IsChecked(),
            notification_sound=self.sound_cb.IsChecked(),
            show_widget=self.show_widget_cb.IsChecked(),
            widget_max_items=self.max_items_spin.GetValue(),
            min_priority_for_notification=AnnouncementPriority(
                self.min_priority_choice.GetSelection()
            ),
            enabled_categories=self.settings.enabled_categories,  # Keep existing
            keep_history_days=self.history_days_spin.GetValue(),
        )
