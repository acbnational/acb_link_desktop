"""
Affiliate correction feedback module for ACB Link.

Provides a specialized feedback system for suggesting corrections to
state affiliate and special interest group (SIG) information.
Submissions are created as GitHub issues with structured data.
"""

import webbrowser
from dataclasses import dataclass
from typing import Optional, List, Dict
from urllib.parse import quote
import wx

from .accessibility import make_accessible


# GitHub repository for affiliate corrections
GITHUB_REPO_OWNER = "acbnational"
GITHUB_REPO_NAME = "acb_link_desktop"
GITHUB_ISSUES_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues/new"


@dataclass
class AffiliateInfo:
    """Data class for affiliate information."""
    name: str
    affiliate_type: str  # "State" or "SIG"
    state: str
    contact_name: str
    email: str
    phone: str
    website: str
    twitter: str  # Displayed as "X" in UI
    facebook: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AffiliateInfo":
        """Create AffiliateInfo from a dictionary."""
        return cls(
            name=data.get("name", ""),
            affiliate_type=data.get("type", ""),
            state=data.get("state", ""),
            contact_name=data.get("contact_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            website=data.get("website", ""),
            twitter=data.get("twitter", ""),
            facebook=data.get("facebook", ""),
        )
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.affiliate_type,
            "state": self.state,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "twitter": self.twitter,
            "facebook": self.facebook,
        }
    
    def format_for_display(self) -> str:
        """Format affiliate info for display/clipboard."""
        lines = [
            f"Organization: {self.name}",
            f"Type: {self.affiliate_type}",
        ]
        if self.state:
            lines.append(f"State: {self.state}")
        if self.contact_name:
            lines.append(f"Contact: {self.contact_name}")
        if self.email:
            lines.append(f"Email: {self.email}")
        if self.phone:
            lines.append(f"Phone: {self.phone}")
        if self.website:
            lines.append(f"Website: {self.website}")
        if self.twitter:
            lines.append(f"X (Twitter): {self.twitter}")
        if self.facebook:
            lines.append(f"Facebook: {self.facebook}")
        return "\n".join(lines)


# Field definitions for correction form
CORRECTION_FIELDS = [
    ("name", "Organization Name"),
    ("contact_name", "Contact Person"),
    ("email", "Email Address"),
    ("phone", "Phone Number"),
    ("website", "Website URL"),
    ("twitter", "X (Twitter)"),
    ("facebook", "Facebook"),
]


def build_affiliate_correction_url(
    affiliate: AffiliateInfo,
    corrections: Dict[str, str],
    notes: str = "",
    is_affiliated: bool = False
) -> str:
    """
    Build a GitHub issue URL for an affiliate correction request.
    
    Args:
        affiliate: The affiliate being corrected
        corrections: Dictionary of field_key -> new_value for corrections
        notes: Additional notes from the submitter
        is_affiliated: Whether the submitter is affiliated with the organization
        
    Returns:
        URL string for GitHub issue creation
    """
    # Build current info table
    current_rows = []
    for field_key, field_label in CORRECTION_FIELDS:
        value = getattr(affiliate, field_key, "") or "(not set)"
        current_rows.append(f"| {field_label} | {value} |")
    current_table = "\n".join(current_rows)
    
    # Build corrections table
    correction_rows = []
    for field_key, new_value in corrections.items():
        field_label = next(
            (label for key, label in CORRECTION_FIELDS if key == field_key),
            field_key
        )
        correction_rows.append(f"| {field_label} | {new_value} |")
    corrections_table = "\n".join(correction_rows) if correction_rows else "No corrections specified"
    
    # Get app version
    try:
        from . import __version__
        app_version = __version__
    except (ImportError, AttributeError):
        app_version = "Unknown"
    
    # Build issue body
    body = f"""## Affiliate Correction Request

**Affiliate Type:** {affiliate.affiliate_type}
**Affiliate Name:** {affiliate.name}
"""
    
    if affiliate.state:
        body += f"**State:** {affiliate.state}\n"
    
    body += f"""
### Current Information
| Field | Current Value |
|-------|---------------|
{current_table}

### Requested Corrections
| Field | New Value |
|-------|-----------|
{corrections_table}

### Additional Notes
{notes if notes else "None provided"}

### Submitter Information
- Affiliated with organization: {"Yes" if is_affiliated else "No"}
- Submitted via: ACB Link Desktop v{app_version}
"""
    
    # Build title
    title = f"[Affiliate Correction] {affiliate.name}"
    
    # Build URL parameters
    params = {
        "title": title,
        "body": body,
        "labels": "affiliate-data,correction-request",
    }
    
    query_string = "&".join(f"{k}={quote(v)}" for k, v in params.items())
    return f"{GITHUB_ISSUES_URL}?{query_string}"


def copy_affiliate_correction_to_clipboard(
    affiliate: AffiliateInfo,
    corrections: Dict[str, str],
    notes: str = "",
    is_affiliated: bool = False
) -> str:
    """
    Format affiliate correction for clipboard (email alternative).
    
    Returns:
        Formatted correction text
    """
    # Get app version
    try:
        from . import __version__
        app_version = __version__
    except (ImportError, AttributeError):
        app_version = "Unknown"
    
    text = f"""ACB Link - Affiliate Correction Request
========================================

Affiliate: {affiliate.name}
Type: {affiliate.affiliate_type}
"""
    
    if affiliate.state:
        text += f"State: {affiliate.state}\n"
    
    text += """
Current Information:
-------------------
"""
    
    for field_key, field_label in CORRECTION_FIELDS:
        value = getattr(affiliate, field_key, "") or "(not set)"
        text += f"  {field_label}: {value}\n"
    
    text += """
Requested Corrections:
---------------------
"""
    
    if corrections:
        for field_key, new_value in corrections.items():
            field_label = next(
                (label for key, label in CORRECTION_FIELDS if key == field_key),
                field_key
            )
            text += f"  {field_label}: {new_value}\n"
    else:
        text += "  No corrections specified\n"
    
    text += f"""
Additional Notes:
----------------
{notes if notes else "None"}

Submitter Information:
---------------------
  Affiliated with organization: {"Yes" if is_affiliated else "No"}
  Submitted via: ACB Link Desktop v{app_version}
"""
    
    return text


class AffiliateCorrectionDialog(wx.Dialog):
    """
    Dialog for submitting affiliate information corrections.
    
    Allows users to select which fields to correct and provide
    new values. Submissions can go to GitHub Issues or be saved
    locally for admin review using the affiliate_admin module.
    """
    
    def __init__(
        self,
        parent: Optional[wx.Window],
        affiliates: List[AffiliateInfo],
        selected_affiliate: Optional[AffiliateInfo] = None
    ):
        """
        Initialize the correction dialog.
        
        Args:
            parent: Parent window
            affiliates: List of all affiliates for selection
            selected_affiliate: Pre-selected affiliate (optional)
        """
        super().__init__(
            parent,
            title="Suggest Affiliate Correction - ACB Link",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.affiliates = affiliates
        self.selected_affiliate = selected_affiliate
        self.correction_checkboxes: Dict[str, wx.CheckBox] = {}
        self.correction_fields: Dict[str, wx.TextCtrl] = {}
        self.correction_labels: Dict[str, wx.StaticText] = {}  # Store labels separately
        
        self.SetMinSize((550, 600))  # type: ignore[arg-type]
        self._create_ui()
        self._bind_events()
        self.Centre()
        
        # Pre-select affiliate if provided
        if selected_affiliate:
            for i, aff in enumerate(affiliates):
                if aff.name == selected_affiliate.name:
                    self.affiliate_choice.SetSelection(i)
                    self._update_current_info()
                    break
        
        # Set initial focus
        self.affiliate_choice.SetFocus()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Help keep affiliate information accurate by suggesting corrections. "
                  "Select the affiliate and check the fields you'd like to correct."
        )
        instructions.Wrap(500)
        main_sizer.Add(instructions, 0, wx.ALL | wx.EXPAND, 10)
        
        # Affiliate selection
        affiliate_label = wx.StaticText(panel, label="&Affiliate:")
        self.affiliate_choice = wx.Choice(
            panel,
            choices=[aff.name for aff in self.affiliates]
        )
        self.affiliate_choice.SetName("Select affiliate to correct")
        make_accessible(
            self.affiliate_choice,
            "Affiliate selection",
            "Choose the affiliate organization to suggest corrections for"
        )
        
        affiliate_sizer = wx.BoxSizer(wx.HORIZONTAL)
        affiliate_sizer.Add(affiliate_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        affiliate_sizer.Add(self.affiliate_choice, 1, wx.EXPAND)
        main_sizer.Add(affiliate_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # Current information display
        info_box = wx.StaticBox(panel, label="Current Information")
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        
        self.current_info_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL,
            size=(-1, 120)  # type: ignore[arg-type]
        )
        self.current_info_text.SetName("Current affiliate information")
        info_sizer.Add(self.current_info_text, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(info_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        # Scrolled panel for correction fields
        scroll = wx.ScrolledWindow(panel, style=wx.VSCROLL)
        scroll.SetScrollRate(0, 20)
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Correction checkboxes and fields
        corrections_label = wx.StaticText(
            scroll,
            label="What would you like to correct? (check all that apply)"
        )
        corrections_label.SetFont(
            corrections_label.GetFont().Bold()
        )
        scroll_sizer.Add(corrections_label, 0, wx.ALL, 5)
        
        for field_key, field_label in CORRECTION_FIELDS:
            # Container for checkbox and text field
            field_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Checkbox
            checkbox = wx.CheckBox(scroll, label=f"&{field_label}")
            checkbox.SetName(f"Correct {field_label}")
            self.correction_checkboxes[field_key] = checkbox
            field_sizer.Add(checkbox, 0, wx.LEFT | wx.TOP, 5)
            
            # Text field (initially hidden)
            text_label = wx.StaticText(scroll, label=f"New {field_label}:")
            text_ctrl = wx.TextCtrl(scroll, size=(400, -1))  # type: ignore[arg-type]
            text_ctrl.SetName(f"New {field_label}")
            text_ctrl.SetHint(f"Enter the correct {field_label.lower()}")
            
            self.correction_fields[field_key] = text_ctrl
            self.correction_labels[field_key] = text_label  # Store label in dict
            
            # Initially hide the text controls
            text_label.Hide()
            text_ctrl.Hide()
            
            field_sizer.Add(text_label, 0, wx.LEFT | wx.TOP, 20)
            field_sizer.Add(text_ctrl, 0, wx.LEFT | wx.BOTTOM | wx.EXPAND, 20)
            
            scroll_sizer.Add(field_sizer, 0, wx.EXPAND)
        
        scroll.SetSizer(scroll_sizer)
        main_sizer.Add(scroll, 1, wx.ALL | wx.EXPAND, 10)
        
        # Additional notes
        notes_label = wx.StaticText(panel, label="Additional &Notes (optional):")
        main_sizer.Add(notes_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.notes_text = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE,
            size=(-1, 60)  # type: ignore[arg-type]
        )
        self.notes_text.SetName("Additional notes")
        self.notes_text.SetHint("Any additional context about the correction...")
        main_sizer.Add(self.notes_text, 0, wx.ALL | wx.EXPAND, 10)
        
        # Affiliation checkbox
        self.affiliated_checkbox = wx.CheckBox(
            panel,
            label="&I am affiliated with this organization"
        )
        self.affiliated_checkbox.SetName("I am affiliated with this organization")
        main_sizer.Add(self.affiliated_checkbox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.submit_local_btn = wx.Button(panel, label="&Submit for Review")
        self.submit_local_btn.SetDefault()
        make_accessible(
            self.submit_local_btn,
            "Submit correction for local review",
            "Saves the correction for administrator review and approval"
        )
        
        self.submit_btn = wx.Button(panel, label="Submit via &GitHub")
        make_accessible(
            self.submit_btn,
            "Submit correction via GitHub",
            "Opens your browser to submit the correction as a GitHub issue"
        )
        
        self.copy_btn = wx.Button(panel, label="&Copy to Clipboard")
        make_accessible(
            self.copy_btn,
            "Copy correction to clipboard",
            "Copy the correction details for emailing"
        )
        
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, label="Cancel")
        
        button_sizer.Add(self.submit_local_btn, 0, wx.RIGHT, 5)
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
        
        # Store scroll reference for layout updates
        self._scroll = scroll
        self._scroll_sizer = scroll_sizer
    
    def _bind_events(self):
        """Bind event handlers."""
        self.affiliate_choice.Bind(wx.EVT_CHOICE, self._on_affiliate_changed)
        self.submit_local_btn.Bind(wx.EVT_BUTTON, self._on_submit_local)
        self.submit_btn.Bind(wx.EVT_BUTTON, self._on_submit)
        self.copy_btn.Bind(wx.EVT_BUTTON, self._on_copy)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        
        # Bind checkbox events
        for field_key, checkbox in self.correction_checkboxes.items():
            checkbox.Bind(
                wx.EVT_CHECKBOX,
                lambda evt, key=field_key: self._on_checkbox_changed(key)
            )
    
    def _on_key(self, event):
        """Handle keyboard shortcuts."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()
    
    def _on_affiliate_changed(self, event):
        """Handle affiliate selection change."""
        self._update_current_info()
    
    def _update_current_info(self):
        """Update the current information display."""
        idx = self.affiliate_choice.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self.affiliates):
            self.current_info_text.SetValue("")
            return
        
        affiliate = self.affiliates[idx]
        self.current_info_text.SetValue(affiliate.format_for_display())
    
    def _on_checkbox_changed(self, field_key: str):
        """Handle correction checkbox toggle."""
        checkbox = self.correction_checkboxes[field_key]
        text_ctrl = self.correction_fields[field_key]
        text_label = self.correction_labels[field_key]
        
        if checkbox.GetValue():
            text_label.Show()
            text_ctrl.Show()
        else:
            text_label.Hide()
            text_ctrl.Hide()
            text_ctrl.SetValue("")
        
        # Update layout
        self._scroll_sizer.Layout()
        self._scroll.FitInside()
        self.Layout()
    
    def _get_selected_affiliate(self) -> Optional[AffiliateInfo]:
        """Get the currently selected affiliate."""
        idx = self.affiliate_choice.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self.affiliates):
            return None
        return self.affiliates[idx]
    
    def _get_corrections(self) -> Dict[str, str]:
        """Get the corrections from checked fields."""
        corrections = {}
        for field_key, checkbox in self.correction_checkboxes.items():
            if checkbox.GetValue():
                value = self.correction_fields[field_key].GetValue().strip()
                if value:
                    corrections[field_key] = value
        return corrections
    
    def _validate_input(self) -> bool:
        """Validate user input before submission."""
        # Check affiliate selected
        if self._get_selected_affiliate() is None:
            wx.MessageBox(
                "Please select an affiliate to correct.",
                "Affiliate Required",
                wx.OK | wx.ICON_WARNING,
                self
            )
            self.affiliate_choice.SetFocus()
            return False
        
        # Check at least one correction
        corrections = self._get_corrections()
        checked_count = sum(1 for cb in self.correction_checkboxes.values() if cb.GetValue())
        
        if checked_count == 0:
            wx.MessageBox(
                "Please check at least one field to correct.",
                "Correction Required",
                wx.OK | wx.ICON_WARNING,
                self
            )
            return False
        
        if not corrections:
            wx.MessageBox(
                "Please enter the new value(s) for the checked field(s).",
                "Values Required",
                wx.OK | wx.ICON_WARNING,
                self
            )
            return False
        
        return True
    
    def _on_submit_local(self, event):
        """Handle local submit button - save for admin review."""
        if not self._validate_input():
            return
        
        affiliate = self._get_selected_affiliate()
        if affiliate is None:
            return
        
        corrections = self._get_corrections()
        notes = self.notes_text.GetValue().strip()
        is_affiliated = self.affiliated_checkbox.GetValue()
        
        try:
            from .affiliate_admin import submit_affiliate_correction
            
            correction_id = submit_affiliate_correction(
                affiliate_name=affiliate.name,
                affiliate_type=affiliate.affiliate_type,
                state_code=affiliate.state,
                corrections=corrections,
                notes=notes,
                is_affiliated=is_affiliated
            )
            
            wx.MessageBox(
                "Your correction has been submitted for review!\n\n"
                f"Correction ID: {correction_id}\n\n"
                "An administrator will review your suggestion and update "
                "the affiliate information if approved.\n\n"
                "Thank you for helping keep our data accurate!",
                "Correction Submitted",
                wx.OK | wx.ICON_INFORMATION,
                self
            )
            self.EndModal(wx.ID_OK)
            
        except ImportError:
            wx.MessageBox(
                "Local submission is not available.\n"
                "Please use 'Submit via GitHub' instead.",
                "Feature Unavailable",
                wx.OK | wx.ICON_WARNING,
                self
            )
        except Exception as e:
            wx.MessageBox(
                f"Error submitting correction: {e}\n\n"
                "Please try 'Submit via GitHub' instead.",
                "Submission Error",
                wx.OK | wx.ICON_ERROR,
                self
            )
    
    def _on_submit(self, event):
        """Handle submit button - open GitHub issue URL."""
        if not self._validate_input():
            return
        
        affiliate = self._get_selected_affiliate()
        if affiliate is None:  # Should not happen after validation, but satisfy type checker
            return
            
        corrections = self._get_corrections()
        notes = self.notes_text.GetValue().strip()
        is_affiliated = self.affiliated_checkbox.GetValue()
        
        url = build_affiliate_correction_url(
            affiliate, corrections, notes, is_affiliated
        )
        
        try:
            webbrowser.open(url)
            wx.MessageBox(
                "Your browser has been opened to submit the correction. "
                "Please review and click 'Submit new issue' on GitHub.\n\n"
                "Note: You'll need a free GitHub account to submit.",
                "Correction Submitted",
                wx.OK | wx.ICON_INFORMATION,
                self
            )
            self.EndModal(wx.ID_OK)
        except Exception as e:
            wx.MessageBox(
                f"Could not open browser: {e}\n\n"
                "Try using 'Copy to Clipboard' instead and email your correction.",
                "Browser Error",
                wx.OK | wx.ICON_ERROR,
                self
            )
    
    def _on_copy(self, event):
        """Handle copy button - copy correction to clipboard."""
        if not self._validate_input():
            return
        
        affiliate = self._get_selected_affiliate()
        if affiliate is None:  # Should not happen after validation, but satisfy type checker
            return
            
        corrections = self._get_corrections()
        notes = self.notes_text.GetValue().strip()
        is_affiliated = self.affiliated_checkbox.GetValue()
        
        text = copy_affiliate_correction_to_clipboard(
            affiliate, corrections, notes, is_affiliated
        )
        
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox(
                "Correction details copied to clipboard!\n\n"
                "You can paste it into an email to: affiliates@acb.org\n"
                f"Or submit at: {GITHUB_ISSUES_URL}",
                "Copied to Clipboard",
                wx.OK | wx.ICON_INFORMATION,
                self
            )
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                "Could not access clipboard. Please try again.",
                "Clipboard Error",
                wx.OK | wx.ICON_ERROR,
                self
            )


def show_affiliate_correction_dialog(
    parent: Optional[wx.Window],
    affiliates: List[AffiliateInfo],
    selected_affiliate: Optional[AffiliateInfo] = None
) -> int:
    """
    Show the affiliate correction dialog.
    
    Args:
        parent: Parent window
        affiliates: List of all affiliates
        selected_affiliate: Pre-selected affiliate (optional)
        
    Returns:
        wx.ID_OK if submitted, wx.ID_CANCEL if cancelled
    """
    dialog = AffiliateCorrectionDialog(parent, affiliates, selected_affiliate)
    result = dialog.ShowModal()
    dialog.Destroy()
    return result
