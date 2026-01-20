"""
User feedback collection module for ACB Link.

Provides a free, sustainable feedback system using GitHub Issues.
Users compose feedback in-app, then submit via browser to GitHub.
"""

import platform
import sys
import webbrowser
from typing import List, Optional
from urllib.parse import quote

import wx

# GitHub repository for issue submission
GITHUB_REPO_OWNER = "acbnational"
GITHUB_REPO_NAME = "acb_link_desktop"
GITHUB_ISSUES_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues/new"


class FeatureArea:
    """Application feature areas for categorizing feedback."""

    GENERAL_APP = "General / Application-wide"
    STREAMS = "Streams & Live Audio"
    PODCASTS = "Podcasts & Episodes"
    AFFILIATES = "State Affiliates & SIGs"
    PLAYBACK = "Playback & Media Controls"
    RECORDING = "Recording & Downloads"
    FAVORITES = "Favorites & Bookmarks"
    PLAYLISTS = "Playlists"
    SEARCH = "Search"
    CALENDAR = "Calendar & Events"
    VOICE_CONTROL = "Voice Control"
    SETTINGS = "Settings & Preferences"
    KEYBOARD = "Keyboard Shortcuts"
    ACCESSIBILITY = "Accessibility & Screen Readers"
    DATA_SYNC = "Data Synchronization"
    SYSTEM_TRAY = "System Tray"
    UPDATES = "Updates & Installation"

    @classmethod
    def all_areas(cls) -> List[str]:
        """Return all feature areas in logical order."""
        return [
            cls.GENERAL_APP,
            cls.STREAMS,
            cls.PODCASTS,
            cls.AFFILIATES,
            cls.PLAYBACK,
            cls.RECORDING,
            cls.FAVORITES,
            cls.PLAYLISTS,
            cls.SEARCH,
            cls.CALENDAR,
            cls.VOICE_CONTROL,
            cls.SETTINGS,
            cls.KEYBOARD,
            cls.ACCESSIBILITY,
            cls.DATA_SYNC,
            cls.SYSTEM_TRAY,
            cls.UPDATES,
        ]

    @classmethod
    def get_label(cls, area: str) -> str:
        """Get GitHub label for feature area."""
        labels = {
            cls.GENERAL_APP: "general",
            cls.STREAMS: "streams",
            cls.PODCASTS: "podcasts",
            cls.AFFILIATES: "affiliates",
            cls.PLAYBACK: "playback",
            cls.RECORDING: "recording",
            cls.FAVORITES: "favorites",
            cls.PLAYLISTS: "playlists",
            cls.SEARCH: "search",
            cls.CALENDAR: "calendar",
            cls.VOICE_CONTROL: "voice-control",
            cls.SETTINGS: "settings",
            cls.KEYBOARD: "keyboard",
            cls.ACCESSIBILITY: "accessibility",
            cls.DATA_SYNC: "data-sync",
            cls.SYSTEM_TRAY: "system-tray",
            cls.UPDATES: "updates",
        }
        return labels.get(area, "general")

    @classmethod
    def get_description(cls, area: str) -> str:
        """Get helpful description for feature area."""
        descriptions = {
            cls.GENERAL_APP: "Issues affecting the overall application experience",
            cls.STREAMS: "Live audio streams, stream selection, stream playback",
            cls.PODCASTS: "Podcast feeds, episodes, downloads, podcast playback",
            cls.AFFILIATES: "State affiliate and special interest group listings",
            cls.PLAYBACK: "Play, pause, stop, volume, speed, skip controls",
            cls.RECORDING: "Stream recording, scheduled recordings, downloads",
            cls.FAVORITES: "Adding/removing favorites, bookmarks, quick access",
            cls.PLAYLISTS: "Creating, editing, managing playlists",
            cls.SEARCH: "Searching for content across the application",
            cls.CALENDAR: "ACB calendar events, reminders, scheduling",
            cls.VOICE_CONTROL: "Voice commands, wake word, speech recognition",
            cls.SETTINGS: "Application settings, preferences, configuration",
            cls.KEYBOARD: "Keyboard shortcuts, hotkeys, accelerators",
            cls.ACCESSIBILITY: "Screen reader support, focus management, announcements",
            cls.DATA_SYNC: "Syncing data from ACB servers, offline mode",
            cls.SYSTEM_TRAY: "System tray icon, notifications, minimize behavior",
            cls.UPDATES: "Automatic updates, installation, version checks",
        }
        return descriptions.get(area, "")


class FeedbackType:
    """Feedback categories."""

    BUG_REPORT = "Bug Report"
    FEATURE_REQUEST = "Feature Request"
    ACCESSIBILITY = "Accessibility Issue"
    USABILITY = "Usability / Confusing Behavior"
    PERFORMANCE = "Performance Issue"
    GENERAL = "General Feedback"

    @classmethod
    def all_types(cls) -> List[str]:
        return [
            cls.BUG_REPORT,
            cls.FEATURE_REQUEST,
            cls.ACCESSIBILITY,
            cls.USABILITY,
            cls.PERFORMANCE,
            cls.GENERAL,
        ]

    @classmethod
    def get_label(cls, feedback_type: str) -> str:
        """Get GitHub label for feedback type."""
        labels = {
            cls.BUG_REPORT: "bug",
            cls.FEATURE_REQUEST: "enhancement",
            cls.ACCESSIBILITY: "accessibility",
            cls.USABILITY: "usability",
            cls.PERFORMANCE: "performance",
            cls.GENERAL: "feedback",
        }
        return labels.get(feedback_type, "feedback")

    @classmethod
    def get_hint(cls, feedback_type: str) -> str:
        """Get helpful hint text for the description field."""
        hints = {
            cls.BUG_REPORT: "Describe what went wrong. Include steps to reproduce if possible.",
            cls.FEATURE_REQUEST: "Describe the feature you'd like and why it would be helpful.",
            cls.ACCESSIBILITY: "Describe the accessibility barrier and your assistive technology.",
            cls.USABILITY: "Describe what was confusing and how it could be clearer.",
            cls.PERFORMANCE: "Describe the slowness or lag you experienced.",
            cls.GENERAL: "Share your thoughts, suggestions, or questions.",
        }
        return hints.get(feedback_type, "Describe your feedback in detail...")

    @classmethod
    def get_template(cls, feedback_type: str, feature_area: str = "") -> str:
        """Get issue body template for feedback type."""
        area_section = f"\n**Feature Area:** {feature_area}\n" if feature_area else ""

        templates = {
            cls.BUG_REPORT: f"""## Bug Description
{{description}}
{area_section}
## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior


## Actual Behavior


## System Information
{{system_info}}
""",
            cls.FEATURE_REQUEST: f"""## Feature Description
{{description}}
{area_section}
## Use Case
Why would this feature be helpful?

## Proposed Solution
How might this work?

## Alternatives Considered
Any other approaches?
""",
            cls.ACCESSIBILITY: f"""## Accessibility Issue
{{description}}
{area_section}
## Assistive Technology Used
(Screen reader name/version, magnification, etc.)

## Expected Accessible Behavior


## Current Behavior


## System Information
{{system_info}}
""",
            cls.USABILITY: f"""## Usability Issue
{{description}}
{area_section}
## What Was Confusing


## What Would Be Clearer


## Additional Context

""",
            cls.PERFORMANCE: f"""## Performance Issue
{{description}}
{area_section}
## When Does It Occur
(Always, sometimes, specific conditions)

## Severity
(Minor lag, significant delay, application freeze)

## System Information
{{system_info}}
""",
            cls.GENERAL: f"""## Feedback
{{description}}
{area_section}
## Additional Context

""",
        }
        return templates.get(feedback_type, templates[cls.GENERAL])


def get_system_info() -> str:
    """Collect anonymous system information for bug reports."""
    try:
        from . import __version__

        app_version = __version__
    except (ImportError, AttributeError):
        app_version = "Unknown"

    info_lines = [
        f"- ACB Link Version: {app_version}",
        f"- Python Version: {sys.version.split()[0]}",
        f"- Platform: {platform.system()} {platform.release()}",
        f"- Architecture: {platform.machine()}",
    ]

    # Add wxPython version if available
    try:
        info_lines.append(f"- wxPython Version: {wx.version()}")
    except Exception:
        pass

    # Add screen reader detection (Windows)
    if platform.system() == "Windows":
        try:
            from .utils import is_screen_reader_active

            sr_active = is_screen_reader_active()
            info_lines.append(f"- Screen Reader Active: {sr_active}")
        except Exception:
            pass

    return "\n".join(info_lines)


def build_github_issue_url(
    feedback_type: str,
    title: str,
    description: str,
    include_system_info: bool = True,
    feature_area: str = "",
) -> str:
    """
    Build a GitHub issue URL with pre-filled content.

    Args:
        feedback_type: Type of feedback from FeedbackType
        title: Issue title
        description: User's feedback description
        include_system_info: Whether to include system info
        feature_area: Feature area from FeatureArea (optional)

    Returns:
        URL string that opens GitHub new issue page with pre-filled data
    """
    template = FeedbackType.get_template(feedback_type, feature_area)
    type_label = FeedbackType.get_label(feedback_type)

    system_info = get_system_info() if include_system_info else "Not provided"

    body = template.format(description=description, system_info=system_info)

    # Build labels list
    labels = [type_label]
    if feature_area:
        area_label = FeatureArea.get_label(feature_area)
        if area_label and area_label != "general":
            labels.append(area_label)

    # Build URL with query parameters
    params = {
        "title": f"[{feedback_type}] {title}",
        "body": body,
        "labels": ",".join(labels),
    }

    query_string = "&".join(f"{k}={quote(v)}" for k, v in params.items())
    return f"{GITHUB_ISSUES_URL}?{query_string}"


def copy_feedback_to_clipboard(
    feedback_type: str,
    title: str,
    description: str,
    include_system_info: bool = True,
    feature_area: str = "",
) -> str:
    """
    Format feedback for clipboard (email alternative).

    Returns:
        Formatted feedback text
    """
    template = FeedbackType.get_template(feedback_type, feature_area)
    system_info = get_system_info() if include_system_info else "Not provided"

    body = template.format(description=description, system_info=system_info)

    area_line = f"\nFeature Area: {feature_area}" if feature_area else ""

    text = f"""ACB Link Feedback
Type: {feedback_type}{area_line}
Subject: {title}

{body}
"""
    return text


class FeedbackDialog(wx.Dialog):
    """
    Accessible feedback dialog for collecting user feedback.

    Allows users to compose feedback and submit via GitHub Issues
    or copy to clipboard for email submission. Includes feature area
    categorization for better routing and organization.
    """

    def __init__(
        self,
        parent: Optional[wx.Window] = None,
        initial_feature_area: str = "",
        initial_feedback_type: str = "",
    ):
        super().__init__(
            parent,
            title="Send Feedback - ACB Link",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._initial_feature_area = initial_feature_area
        self._initial_feedback_type = initial_feedback_type

        self.SetMinSize((550, 550))  # type: ignore[arg-type]
        self._create_ui()
        self._bind_events()
        self.Centre()

        # Set initial selections if provided
        if initial_feedback_type:
            try:
                idx = FeedbackType.all_types().index(initial_feedback_type)
                self.feedback_type_choice.SetSelection(idx)
            except ValueError:
                pass

        if initial_feature_area:
            try:
                idx = FeatureArea.all_areas().index(initial_feature_area)
                self.feature_area_choice.SetSelection(idx)
            except ValueError:
                pass

        # Update description hint based on initial selection
        self._update_description_hint()

        # Set initial focus for screen readers
        self.feedback_type_choice.SetFocus()

    def _create_ui(self):
        """Create the dialog UI with accessibility in mind."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Share your feedback to help improve ACB Link. "
            "Select the type of feedback and which feature area it relates to. "
            "Your feedback will be submitted as a GitHub issue.",
        )
        instructions.Wrap(500)
        main_sizer.Add(instructions, 0, wx.ALL | wx.EXPAND, 10)

        # Create a grid sizer for the dropdowns
        grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)
        grid_sizer.AddGrowableCol(1, 1)

        # Feedback type selection
        type_label = wx.StaticText(panel, label="&Feedback Type:")
        self.feedback_type_choice = wx.Choice(panel, choices=FeedbackType.all_types())
        self.feedback_type_choice.SetSelection(0)
        self.feedback_type_choice.SetName("Feedback Type")
        self.feedback_type_choice.SetToolTip(
            "Select the type of feedback: Bug Report for problems, "
            "Feature Request for suggestions, etc."
        )

        grid_sizer.Add(type_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.feedback_type_choice, 1, wx.EXPAND)

        # Feature area selection (NEW)
        area_label = wx.StaticText(panel, label="Feature &Area:")
        self.feature_area_choice = wx.Choice(panel, choices=FeatureArea.all_areas())
        self.feature_area_choice.SetSelection(0)
        self.feature_area_choice.SetName("Feature Area")
        self.feature_area_choice.SetToolTip(
            "Select which part of the application your feedback is about."
        )

        grid_sizer.Add(area_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.feature_area_choice, 1, wx.EXPAND)

        main_sizer.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Feature area description (dynamic)
        self.area_description = wx.StaticText(panel, label="")
        self.area_description.SetForegroundColour(wx.Colour(80, 80, 80))
        self._update_area_description()
        main_sizer.Add(self.area_description, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Title/subject
        title_label = wx.StaticText(panel, label="&Subject:")
        self.title_text = wx.TextCtrl(panel)
        self.title_text.SetName("Subject")
        self.title_text.SetHint("Brief summary of your feedback")
        self.title_text.SetToolTip("Enter a brief, descriptive subject line for your feedback")

        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_sizer.Add(title_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        title_sizer.Add(self.title_text, 1, wx.EXPAND)
        main_sizer.Add(title_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Description with dynamic hint
        desc_label = wx.StaticText(panel, label="&Description:")
        main_sizer.Add(desc_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)

        self.description_text = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_WORDWRAP, size=(-1, 180)  # type: ignore[arg-type]
        )
        self.description_text.SetName("Description")
        self._update_description_hint()
        main_sizer.Add(self.description_text, 1, wx.ALL | wx.EXPAND, 10)

        # Hint text below description
        self.hint_label = wx.StaticText(panel, label="")
        self.hint_label.SetForegroundColour(wx.Colour(80, 80, 80))
        font = self.hint_label.GetFont()
        font.SetPointSize(font.GetPointSize() - 1)
        self.hint_label.SetFont(font)
        self._update_hint_label()
        main_sizer.Add(self.hint_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # Include system info checkbox
        self.include_system_info = wx.CheckBox(
            panel, label="&Include anonymous system information (helps with bug reports)"
        )
        self.include_system_info.SetValue(True)
        self.include_system_info.SetName("Include system information")
        self.include_system_info.SetToolTip(
            "When checked, includes your operating system, app version, "
            "and screen reader status to help diagnose issues."
        )
        main_sizer.Add(self.include_system_info, 0, wx.ALL, 10)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.submit_btn = wx.Button(panel, label="&Submit via GitHub")
        self.submit_btn.SetDefault()
        self.submit_btn.SetName("Submit feedback via GitHub")
        self.submit_btn.SetToolTip("Opens your browser to submit this feedback as a GitHub issue")

        self.copy_btn = wx.Button(panel, label="&Copy to Clipboard")
        self.copy_btn.SetName("Copy feedback to clipboard")
        self.copy_btn.SetToolTip("Copies the feedback to your clipboard for email submission")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, label="Cancel")

        button_sizer.Add(self.submit_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(self.copy_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(self.cancel_btn, 0)

        main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

        # Dialog sizer
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(dialog_sizer)
        self.Fit()

    def _bind_events(self):
        """Bind event handlers."""
        self.submit_btn.Bind(wx.EVT_BUTTON, self._on_submit)
        self.copy_btn.Bind(wx.EVT_BUTTON, self._on_copy)
        self.feedback_type_choice.Bind(wx.EVT_CHOICE, self._on_type_changed)
        self.feature_area_choice.Bind(wx.EVT_CHOICE, self._on_area_changed)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)

    def _on_type_changed(self, event):
        """Update UI when feedback type changes."""
        self._update_description_hint()
        self._update_hint_label()
        event.Skip()

    def _on_area_changed(self, event):
        """Update UI when feature area changes."""
        self._update_area_description()
        event.Skip()

    def _update_area_description(self):
        """Update the feature area description text."""
        selected_area = FeatureArea.all_areas()[self.feature_area_choice.GetSelection()]
        description = FeatureArea.get_description(selected_area)
        self.area_description.SetLabel(description)
        self.area_description.Wrap(480)

    def _update_description_hint(self):
        """Update the description field hint based on feedback type."""
        selected_type = FeedbackType.all_types()[self.feedback_type_choice.GetSelection()]
        hint = FeedbackType.get_hint(selected_type)
        self.description_text.SetHint(hint)
        self.description_text.SetToolTip(hint)

    def _update_hint_label(self):
        """Update the hint label below the description field."""
        selected_type = FeedbackType.all_types()[self.feedback_type_choice.GetSelection()]
        hint = FeedbackType.get_hint(selected_type)
        self.hint_label.SetLabel(f"Tip: {hint}")
        self.hint_label.Wrap(480)

    def _on_key(self, event):
        """Handle keyboard shortcuts."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def _validate_input(self) -> bool:
        """Validate user input before submission."""
        title = self.title_text.GetValue().strip()
        description = self.description_text.GetValue().strip()

        if not title:
            wx.MessageBox(
                "Please enter a subject for your feedback.",
                "Subject Required",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            self.title_text.SetFocus()
            return False

        if not description:
            wx.MessageBox(
                "Please enter a description of your feedback.",
                "Description Required",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            self.description_text.SetFocus()
            return False

        return True

    def _get_feedback_data(self) -> dict:
        """Get feedback data from form."""
        return {
            "feedback_type": FeedbackType.all_types()[self.feedback_type_choice.GetSelection()],
            "feature_area": FeatureArea.all_areas()[self.feature_area_choice.GetSelection()],
            "title": self.title_text.GetValue().strip(),
            "description": self.description_text.GetValue().strip(),
            "include_system_info": self.include_system_info.GetValue(),
        }

    def _on_submit(self, event):
        """Handle submit button - open GitHub issue URL."""
        if not self._validate_input():
            return

        data = self._get_feedback_data()
        url = build_github_issue_url(
            data["feedback_type"],
            data["title"],
            data["description"],
            data["include_system_info"],
            data["feature_area"],
        )

        # Open in browser
        try:
            webbrowser.open(url)
            wx.MessageBox(
                "Your browser has been opened to submit the feedback. "
                "Please review and click 'Submit new issue' on GitHub.\n\n"
                "Note: You'll need a free GitHub account to submit.",
                "Feedback Submitted",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            self.EndModal(wx.ID_OK)
        except Exception as e:
            wx.MessageBox(
                f"Could not open browser: {e}\n\n"
                "Try using 'Copy to Clipboard' instead and email your feedback.",
                "Browser Error",
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def _on_copy(self, event):
        """Handle copy button - copy feedback to clipboard."""
        if not self._validate_input():
            return

        data = self._get_feedback_data()
        text = copy_feedback_to_clipboard(
            data["feedback_type"],
            data["title"],
            data["description"],
            data["include_system_info"],
            data["feature_area"],
        )

        # Copy to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox(
                "Feedback copied to clipboard!\n\n"
                "You can paste it into an email to: feedback@acblink.org\n"
                "Or submit at: https://github.com/acbnational/acb_link_desktop/issues",
                "Copied to Clipboard",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                "Could not access clipboard. Please try again.",
                "Clipboard Error",
                wx.OK | wx.ICON_ERROR,
                self,
            )


def show_feedback_dialog(
    parent: Optional[wx.Window] = None,
    initial_feature_area: str = "",
    initial_feedback_type: str = "",
) -> int:
    """
    Show the feedback dialog.

    Args:
        parent: Parent window
        initial_feature_area: Pre-select a feature area (from FeatureArea)
        initial_feedback_type: Pre-select a feedback type (from FeedbackType)

    Returns:
        wx.ID_OK if submitted, wx.ID_CANCEL if cancelled
    """
    dialog = FeedbackDialog(
        parent,
        initial_feature_area=initial_feature_area,
        initial_feedback_type=initial_feedback_type,
    )
    result = dialog.ShowModal()
    dialog.Destroy()
    return result


# Convenience function for menu integration
def on_send_feedback(event=None, parent: Optional[wx.Window] = None):
    """Menu handler for Help > Send Feedback."""
    show_feedback_dialog(parent)


# Convenience functions for context-aware feedback
def report_bug(parent: Optional[wx.Window] = None, feature_area: str = "") -> int:
    """Open feedback dialog pre-configured for bug reporting."""
    return show_feedback_dialog(
        parent, initial_feature_area=feature_area, initial_feedback_type=FeedbackType.BUG_REPORT
    )


def request_feature(parent: Optional[wx.Window] = None, feature_area: str = "") -> int:
    """Open feedback dialog pre-configured for feature requests."""
    return show_feedback_dialog(
        parent,
        initial_feature_area=feature_area,
        initial_feedback_type=FeedbackType.FEATURE_REQUEST,
    )


def report_accessibility_issue(parent: Optional[wx.Window] = None, feature_area: str = "") -> int:
    """Open feedback dialog pre-configured for accessibility issues."""
    return show_feedback_dialog(
        parent,
        initial_feature_area=feature_area or FeatureArea.ACCESSIBILITY,
        initial_feedback_type=FeedbackType.ACCESSIBILITY,
    )
