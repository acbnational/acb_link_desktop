"""
Affiliate Correction Administration Module for ACB Link.

Provides a safe, automated system for reviewing, approving, and applying
affiliate data corrections. This module eliminates the need for manual
XML editing while maintaining safety through a review/approval workflow.

Security:
- Requires AFFILIATE_ADMIN role or higher to review/approve corrections
- All actions are logged in the audit trail
- Changes are validated before application
- Automatic backup before any XML modifications

Key components:
- CorrectionQueue: Stores pending corrections in JSON
- CorrectionManager: Handles the review/approval workflow
- XMLUpdater: Safely applies approved changes to XML files
- AuditLog: Tracks all changes with history
- AdminReviewPanel: UI for administrators to review corrections
"""

import json
import os
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import wx

from .accessibility import make_accessible, make_button_accessible


class CorrectionStatus(Enum):
    """Status of a correction request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class AffiliateType(Enum):
    """Type of affiliate organization."""
    STATE = "State"
    SIG = "SIG"


@dataclass
class AffiliateCorrection:
    """
    Represents a single affiliate correction request.
    
    Stores all the information needed to track, review, and apply
    a correction to affiliate data.
    """
    id: str  # Unique identifier (timestamp-based)
    affiliate_name: str  # Name of the affiliate being corrected
    affiliate_type: str  # "State" or "SIG"
    state_code: str  # State code (for State affiliates)
    
    # Field corrections - maps field name to new value
    corrections: Dict[str, str]
    
    # Original values (for reference/rollback)
    original_values: Dict[str, str]
    
    # Submitter info
    submitter_notes: str = ""
    submitter_affiliated: bool = False
    submitted_at: str = ""  # ISO format timestamp
    submitted_via: str = "ACB Link Desktop"
    
    # Review info
    status: str = "pending"  # CorrectionStatus value
    reviewed_at: str = ""
    reviewed_by: str = ""
    review_notes: str = ""
    
    # Application info
    applied_at: str = ""
    apply_error: str = ""
    
    def __post_init__(self):
        """Generate ID and timestamp if not provided."""
        if not self.id:
            self.id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        if not self.submitted_at:
            self.submitted_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AffiliateCorrection":
        """Create from dictionary."""
        return cls(**data)
    
    def get_changes_summary(self) -> str:
        """Get a human-readable summary of changes."""
        lines = []
        for field_name, new_value in self.corrections.items():
            old_value = self.original_values.get(field_name, "(not set)")
            lines.append(f"  {field_name}: {old_value} → {new_value}")
        return "\n".join(lines) if lines else "No changes"
    
    def is_pending(self) -> bool:
        """Check if correction is pending review."""
        return self.status == CorrectionStatus.PENDING.value
    
    def is_approved(self) -> bool:
        """Check if correction has been approved."""
        return self.status == CorrectionStatus.APPROVED.value


class CorrectionQueue:
    """
    Manages the queue of pending affiliate corrections.
    
    Corrections are stored in a JSON file for persistence.
    """
    
    DEFAULT_QUEUE_FILE = "affiliate_corrections_queue.json"
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the correction queue.
        
        Args:
            data_dir: Directory to store queue file (default: app data dir)
        """
        if data_dir is None:
            # Use app data directory
            app_data = Path(os.environ.get("APPDATA", os.path.expanduser("~")))
            data_dir = app_data / "ACBLink"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.data_dir / self.DEFAULT_QUEUE_FILE
        self._corrections: List[AffiliateCorrection] = []
        self._load()
    
    def _load(self):
        """Load corrections from JSON file."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._corrections = [
                        AffiliateCorrection.from_dict(item) 
                        for item in data.get("corrections", [])
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                # Corrupted file - backup and start fresh
                backup_path = self.queue_file.with_suffix(".json.bak")
                shutil.copy2(self.queue_file, backup_path)
                self._corrections = []
    
    def _save(self):
        """Save corrections to JSON file."""
        data = {
            "version": "1.0",
            "last_modified": datetime.now().isoformat(),
            "corrections": [c.to_dict() for c in self._corrections]
        }
        
        # Write to temp file first, then rename (atomic write)
        temp_file = self.queue_file.with_suffix(".json.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_file.replace(self.queue_file)
    
    def add(self, correction: AffiliateCorrection) -> str:
        """
        Add a new correction to the queue.
        
        Returns:
            The correction ID
        """
        self._corrections.append(correction)
        self._save()
        return correction.id
    
    def get(self, correction_id: str) -> Optional[AffiliateCorrection]:
        """Get a correction by ID."""
        for c in self._corrections:
            if c.id == correction_id:
                return c
        return None
    
    def update(self, correction: AffiliateCorrection):
        """Update an existing correction."""
        for i, c in enumerate(self._corrections):
            if c.id == correction.id:
                self._corrections[i] = correction
                self._save()
                return
    
    def remove(self, correction_id: str) -> bool:
        """Remove a correction from the queue."""
        for i, c in enumerate(self._corrections):
            if c.id == correction_id:
                del self._corrections[i]
                self._save()
                return True
        return False
    
    def get_pending(self) -> List[AffiliateCorrection]:
        """Get all pending corrections."""
        return [c for c in self._corrections if c.is_pending()]
    
    def get_approved(self) -> List[AffiliateCorrection]:
        """Get all approved (but not yet applied) corrections."""
        return [c for c in self._corrections if c.is_approved()]
    
    def get_all(self) -> List[AffiliateCorrection]:
        """Get all corrections."""
        return list(self._corrections)
    
    def get_by_status(self, status: CorrectionStatus) -> List[AffiliateCorrection]:
        """Get corrections by status."""
        return [c for c in self._corrections if c.status == status.value]
    
    def get_by_affiliate(self, affiliate_name: str) -> List[AffiliateCorrection]:
        """Get corrections for a specific affiliate."""
        return [c for c in self._corrections if c.affiliate_name == affiliate_name]


class AuditLog:
    """
    Audit log for tracking all affiliate data changes.
    
    Maintains a complete history of who changed what and when.
    """
    
    DEFAULT_LOG_FILE = "affiliate_audit_log.json"
    
    @dataclass
    class Entry:
        """A single audit log entry."""
        timestamp: str
        action: str  # "approved", "rejected", "applied", "rollback"
        correction_id: str
        affiliate_name: str
        changes: Dict[str, str]
        performed_by: str
        notes: str = ""
        
        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)
        
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "AuditLog.Entry":
            return cls(**data)
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the audit log."""
        if data_dir is None:
            app_data = Path(os.environ.get("APPDATA", os.path.expanduser("~")))
            data_dir = app_data / "ACBLink"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / self.DEFAULT_LOG_FILE
        self._entries: List[AuditLog.Entry] = []
        self._load()
    
    def _load(self):
        """Load log from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._entries = [
                        self.Entry.from_dict(item)
                        for item in data.get("entries", [])
                    ]
            except (json.JSONDecodeError, KeyError):
                self._entries = []
    
    def _save(self):
        """Save log to file."""
        data = {
            "version": "1.0",
            "entries": [e.to_dict() for e in self._entries]
        }
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def log(
        self,
        action: str,
        correction: AffiliateCorrection,
        performed_by: str,
        notes: str = ""
    ):
        """Add an entry to the audit log."""
        entry = self.Entry(
            timestamp=datetime.now().isoformat(),
            action=action,
            correction_id=correction.id,
            affiliate_name=correction.affiliate_name,
            changes=correction.corrections,
            performed_by=performed_by,
            notes=notes
        )
        self._entries.append(entry)
        self._save()
    
    def get_history(
        self,
        affiliate_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Entry]:
        """Get audit history, optionally filtered by affiliate."""
        entries = self._entries
        if affiliate_name:
            entries = [e for e in entries if e.affiliate_name == affiliate_name]
        return list(reversed(entries[-limit:]))


class XMLUpdater:
    """
    Safely updates affiliate XML files.
    
    Features:
    - Automatic backup before changes
    - Validation before and after
    - Rollback capability
    - Atomic writes
    """
    
    # Field mapping: internal name -> XML element name
    FIELD_MAP = {
        "name": "AffiliateName",
        "contact_name": "Name",
        "email": "EmailAddress",
        "phone": "PhoneNumber",
        "website": "WebSiteAddress",
        "twitter": "TwitterAddress",
        "facebook": "FacebookAddress",
    }
    
    def __init__(self, data_dir: Path):
        """
        Initialize the XML updater.
        
        Args:
            data_dir: Path to the data/s3 directory containing XML files
        """
        self.data_dir = Path(data_dir)
        self.states_file = self.data_dir / "states.xml"
        self.sigs_file = self.data_dir / "sigs.xml"
        self.backup_dir = self.data_dir / "backups"
    
    def _get_xml_file(self, affiliate_type: str) -> Path:
        """Get the appropriate XML file for an affiliate type."""
        if affiliate_type == AffiliateType.STATE.value:
            return self.states_file
        elif affiliate_type == AffiliateType.SIG.value:
            return self.sigs_file
        else:
            raise ValueError(f"Unknown affiliate type: {affiliate_type}")
    
    def _create_backup(self, xml_file: Path) -> Path:
        """
        Create a backup of an XML file.
        
        Returns:
            Path to the backup file
        """
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{xml_file.stem}_{timestamp}.xml"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(xml_file, backup_path)
        return backup_path
    
    def _find_affiliate_element(
        self,
        root: ET.Element,
        affiliate_name: str
    ) -> Optional[ET.Element]:
        """Find an affiliate element by name."""
        for affiliate in root.findall("Affiliate"):
            name_elem = affiliate.find("AffiliateName")
            if name_elem is not None and name_elem.text == affiliate_name:
                return affiliate
        return None
    
    def _validate_xml(self, xml_file: Path) -> bool:
        """Validate that an XML file is well-formed."""
        try:
            ET.parse(xml_file)
            return True
        except ET.ParseError:
            return False
    
    def get_current_values(
        self,
        affiliate_name: str,
        affiliate_type: str
    ) -> Dict[str, str]:
        """
        Get current values for an affiliate.
        
        Returns:
            Dictionary of field_name -> value
        """
        xml_file = self._get_xml_file(affiliate_type)
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        affiliate_elem = self._find_affiliate_element(root, affiliate_name)
        if affiliate_elem is None:
            return {}
        
        values = {}
        for internal_name, xml_name in self.FIELD_MAP.items():
            elem = affiliate_elem.find(xml_name)
            values[internal_name] = elem.text if elem is not None and elem.text else ""
        
        return values
    
    def apply_correction(
        self,
        correction: AffiliateCorrection,
        create_backup: bool = True
    ) -> tuple[bool, str]:
        """
        Apply a correction to the XML file.
        
        Args:
            correction: The correction to apply
            create_backup: Whether to create a backup first
            
        Returns:
            Tuple of (success, message)
        """
        xml_file = self._get_xml_file(correction.affiliate_type)
        
        # Validate source file
        if not xml_file.exists():
            return False, f"XML file not found: {xml_file}"
        
        if not self._validate_xml(xml_file):
            return False, f"XML file is malformed: {xml_file}"
        
        # Create backup
        backup_path = None
        if create_backup:
            try:
                backup_path = self._create_backup(xml_file)
            except Exception as e:
                return False, f"Failed to create backup: {e}"
        
        # Parse and modify
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            affiliate_elem = self._find_affiliate_element(root, correction.affiliate_name)
            if affiliate_elem is None:
                return False, f"Affiliate not found: {correction.affiliate_name}"
            
            # Apply corrections
            for field_name, new_value in correction.corrections.items():
                xml_name = self.FIELD_MAP.get(field_name)
                if xml_name is None:
                    continue
                
                elem = affiliate_elem.find(xml_name)
                if elem is not None:
                    elem.text = new_value
            
            # Write to temp file first
            temp_file = xml_file.with_suffix(".xml.tmp")
            tree.write(temp_file, encoding="unicode", xml_declaration=True)
            
            # Validate the result
            if not self._validate_xml(temp_file):
                temp_file.unlink()
                return False, "Generated XML is malformed"
            
            # Atomic replace
            temp_file.replace(xml_file)
            
            return True, f"Successfully applied correction. Backup: {backup_path}"
            
        except Exception as e:
            # Try to restore from backup if available
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, xml_file)
            return False, f"Error applying correction: {e}"
    
    def rollback(self, backup_path: Path, affiliate_type: str) -> tuple[bool, str]:
        """
        Rollback to a previous backup.
        
        Args:
            backup_path: Path to the backup file
            affiliate_type: Type of affiliate (to determine which file)
            
        Returns:
            Tuple of (success, message)
        """
        xml_file = self._get_xml_file(affiliate_type)
        
        if not backup_path.exists():
            return False, f"Backup file not found: {backup_path}"
        
        if not self._validate_xml(backup_path):
            return False, f"Backup file is malformed: {backup_path}"
        
        try:
            # Backup current file before rollback
            self._create_backup(xml_file)
            
            # Restore from backup
            shutil.copy2(backup_path, xml_file)
            
            return True, f"Successfully rolled back to: {backup_path}"
        except Exception as e:
            return False, f"Rollback failed: {e}"
    
    def get_backups(self, affiliate_type: str) -> List[Path]:
        """Get list of available backups for an affiliate type."""
        if not self.backup_dir.exists():
            return []
        
        prefix = "states" if affiliate_type == AffiliateType.STATE.value else "sigs"
        backups = list(self.backup_dir.glob(f"{prefix}_*.xml"))
        return sorted(backups, reverse=True)


class CorrectionManager:
    """
    Central manager for the affiliate correction workflow.
    
    Coordinates between the queue, updater, and audit log.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        xml_dir: Optional[Path] = None
    ):
        """
        Initialize the correction manager.
        
        Args:
            data_dir: Directory for queue/audit files
            xml_dir: Directory containing XML data files
        """
        self.queue = CorrectionQueue(data_dir)
        self.audit = AuditLog(data_dir)
        
        if xml_dir is None:
            # Default to data/s3 relative to module
            module_dir = Path(__file__).parent.parent
            xml_dir = module_dir / "data" / "s3"
        
        self.updater = XMLUpdater(xml_dir)
    
    def submit_correction(
        self,
        affiliate_name: str,
        affiliate_type: str,
        state_code: str,
        corrections: Dict[str, str],
        notes: str = "",
        is_affiliated: bool = False
    ) -> AffiliateCorrection:
        """
        Submit a new correction for review.
        
        Args:
            affiliate_name: Name of the affiliate
            affiliate_type: "State" or "SIG"
            state_code: State code for state affiliates
            corrections: Dictionary of field -> new value
            notes: Additional notes from submitter
            is_affiliated: Whether submitter is affiliated
            
        Returns:
            The created correction object
        """
        # Get current values for reference
        original_values = self.updater.get_current_values(
            affiliate_name, affiliate_type
        )
        
        # Create correction
        correction = AffiliateCorrection(
            id="",  # Will be auto-generated
            affiliate_name=affiliate_name,
            affiliate_type=affiliate_type,
            state_code=state_code,
            corrections=corrections,
            original_values=original_values,
            submitter_notes=notes,
            submitter_affiliated=is_affiliated
        )
        
        # Add to queue
        self.queue.add(correction)
        
        return correction
    
    def approve_correction(
        self,
        correction_id: str,
        reviewer: str,
        notes: str = ""
    ) -> tuple[bool, str]:
        """
        Approve a pending correction.
        
        Does not apply the change yet - use apply_correction for that.
        """
        correction = self.queue.get(correction_id)
        if correction is None:
            return False, "Correction not found"
        
        if not correction.is_pending():
            return False, f"Correction is not pending (status: {correction.status})"
        
        correction.status = CorrectionStatus.APPROVED.value
        correction.reviewed_at = datetime.now().isoformat()
        correction.reviewed_by = reviewer
        correction.review_notes = notes
        
        self.queue.update(correction)
        self.audit.log("approved", correction, reviewer, notes)
        
        return True, "Correction approved"
    
    def reject_correction(
        self,
        correction_id: str,
        reviewer: str,
        reason: str
    ) -> tuple[bool, str]:
        """Reject a pending correction."""
        correction = self.queue.get(correction_id)
        if correction is None:
            return False, "Correction not found"
        
        if not correction.is_pending():
            return False, f"Correction is not pending (status: {correction.status})"
        
        correction.status = CorrectionStatus.REJECTED.value
        correction.reviewed_at = datetime.now().isoformat()
        correction.reviewed_by = reviewer
        correction.review_notes = reason
        
        self.queue.update(correction)
        self.audit.log("rejected", correction, reviewer, reason)
        
        return True, "Correction rejected"
    
    def apply_correction(
        self,
        correction_id: str,
        applier: str
    ) -> tuple[bool, str]:
        """
        Apply an approved correction to the XML file.
        
        Args:
            correction_id: ID of the correction to apply
            applier: Name/ID of person applying
            
        Returns:
            Tuple of (success, message)
        """
        correction = self.queue.get(correction_id)
        if correction is None:
            return False, "Correction not found"
        
        if not correction.is_approved():
            return False, f"Correction is not approved (status: {correction.status})"
        
        # Apply to XML
        success, message = self.updater.apply_correction(correction)
        
        if success:
            correction.status = CorrectionStatus.APPLIED.value
            correction.applied_at = datetime.now().isoformat()
            self.audit.log("applied", correction, applier, message)
        else:
            correction.status = CorrectionStatus.FAILED.value
            correction.apply_error = message
            self.audit.log("failed", correction, applier, message)
        
        self.queue.update(correction)
        return success, message
    
    def apply_all_approved(self, applier: str) -> List[tuple[str, bool, str]]:
        """
        Apply all approved corrections.
        
        Returns:
            List of (correction_id, success, message) tuples
        """
        results = []
        for correction in self.queue.get_approved():
            success, message = self.apply_correction(correction.id, applier)
            results.append((correction.id, success, message))
        return results
    
    def get_pending_count(self) -> int:
        """Get count of pending corrections."""
        return len(self.queue.get_pending())
    
    def get_approved_count(self) -> int:
        """Get count of approved but unapplied corrections."""
        return len(self.queue.get_approved())


# =============================================================================
# Admin Review UI
# =============================================================================

class CorrectionDetailsDialog(wx.Dialog):
    """Dialog showing full details of a correction."""
    
    def __init__(self, parent: wx.Window, correction: AffiliateCorrection):
        super().__init__(
            parent,
            title=f"Correction Details - {correction.affiliate_name}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.correction = correction
        self.SetMinSize((500, 400))
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header info
        header = wx.StaticText(
            panel,
            label=f"Affiliate: {self.correction.affiliate_name}\n"
                  f"Type: {self.correction.affiliate_type}\n"
                  f"Status: {self.correction.status.upper()}\n"
                  f"Submitted: {self.correction.submitted_at[:19]}"
        )
        make_accessible(header, "Correction header", "Basic correction information")
        sizer.Add(header, 0, wx.ALL | wx.EXPAND, 10)
        
        # Changes section
        changes_label = wx.StaticText(panel, label="Proposed Changes:")
        changes_label.SetFont(changes_label.GetFont().Bold())
        sizer.Add(changes_label, 0, wx.LEFT | wx.TOP, 10)
        
        changes_text = wx.TextCtrl(
            panel,
            value=self._format_changes(),
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 120)
        )
        make_accessible(changes_text, "Proposed changes", "List of field changes")
        sizer.Add(changes_text, 0, wx.ALL | wx.EXPAND, 10)
        
        # Submitter notes
        if self.correction.submitter_notes:
            notes_label = wx.StaticText(panel, label="Submitter Notes:")
            notes_label.SetFont(notes_label.GetFont().Bold())
            sizer.Add(notes_label, 0, wx.LEFT, 10)
            
            notes_text = wx.TextCtrl(
                panel,
                value=self.correction.submitter_notes,
                style=wx.TE_MULTILINE | wx.TE_READONLY,
                size=(-1, 60)
            )
            sizer.Add(notes_text, 0, wx.ALL | wx.EXPAND, 10)
        
        # Affiliated checkbox display
        affiliated_text = "Yes" if self.correction.submitter_affiliated else "No"
        affiliated_label = wx.StaticText(
            panel,
            label=f"Submitter affiliated with organization: {affiliated_text}"
        )
        sizer.Add(affiliated_label, 0, wx.LEFT | wx.BOTTOM, 10)
        
        # Close button
        close_btn = wx.Button(panel, wx.ID_CLOSE, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        sizer.Add(close_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        panel.SetSizer(sizer)
        self.Fit()
    
    def _format_changes(self) -> str:
        """Format the changes for display."""
        lines = []
        for field, new_value in self.correction.corrections.items():
            old_value = self.correction.original_values.get(field, "(not set)")
            lines.append(f"{field}:")
            lines.append(f"  Before: {old_value}")
            lines.append(f"  After:  {new_value}")
            lines.append("")
        return "\n".join(lines)


class AdminReviewPanel(wx.Panel):
    """
    Panel for administrators to review and approve affiliate corrections.
    
    Provides a list of pending corrections with approve/reject actions.
    Requires AFFILIATE_ADMIN role or higher for access.
    """
    
    def __init__(self, parent: wx.Window, manager: CorrectionManager, admin_name: Optional[str] = None):
        """
        Initialize the admin review panel.
        
        Args:
            parent: Parent window
            manager: CorrectionManager instance
            admin_name: Name of authenticated admin (required for approval actions)
        """
        super().__init__(parent)
        
        self.manager = manager
        self.admin_name = admin_name or "Unknown Admin"
        
        self._create_ui()
        self._bind_events()
        self._refresh_list()
    
    def _create_ui(self):
        """Create the panel UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(
            self,
            label="Review Affiliate Corrections"
        )
        header.SetFont(header.GetFont().Bold().Scaled(1.2))
        make_accessible(header, "Admin review panel", "Review pending affiliate corrections")
        main_sizer.Add(header, 0, wx.ALL, 10)
        
        # Filter controls
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        filter_label = wx.StaticText(self, label="&Show:")
        self.filter_choice = wx.Choice(
            self,
            choices=["Pending", "Approved", "Rejected", "Applied", "All"]
        )
        self.filter_choice.SetSelection(0)
        make_accessible(self.filter_choice, "Filter", "Filter corrections by status")
        
        self.refresh_btn = wx.Button(self, label="&Refresh")
        make_button_accessible(self.refresh_btn, "Refresh list")
        
        filter_sizer.Add(filter_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        filter_sizer.Add(self.filter_choice, 0, wx.RIGHT, 10)
        filter_sizer.Add(self.refresh_btn, 0)
        
        main_sizer.Add(filter_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Corrections list
        self.list_ctrl = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self.list_ctrl.SetName("Corrections list")
        
        # Set up columns
        self.list_ctrl.InsertColumn(0, "Affiliate", width=200)
        self.list_ctrl.InsertColumn(1, "Type", width=60)
        self.list_ctrl.InsertColumn(2, "Changes", width=150)
        self.list_ctrl.InsertColumn(3, "Submitted", width=100)
        self.list_ctrl.InsertColumn(4, "Status", width=80)
        
        main_sizer.Add(self.list_ctrl, 1, wx.ALL | wx.EXPAND, 10)
        
        # Action buttons
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.view_btn = wx.Button(self, label="&View Details")
        make_button_accessible(self.view_btn, "View full correction details")
        
        self.approve_btn = wx.Button(self, label="&Approve")
        make_button_accessible(self.approve_btn, "Approve selected correction")
        
        self.reject_btn = wx.Button(self, label="Re&ject")
        make_button_accessible(self.reject_btn, "Reject selected correction")
        
        self.apply_btn = wx.Button(self, label="A&pply to Data")
        make_button_accessible(self.apply_btn, "Apply approved correction to XML data")
        
        self.apply_all_btn = wx.Button(self, label="Apply &All Approved")
        make_button_accessible(self.apply_all_btn, "Apply all approved corrections")
        
        action_sizer.Add(self.view_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.approve_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.reject_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.apply_btn, 0, wx.RIGHT, 5)
        action_sizer.Add(self.apply_all_btn, 0)
        
        main_sizer.Add(action_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Status bar
        self.status_text = wx.StaticText(self, label="")
        main_sizer.Add(self.status_text, 0, wx.ALL | wx.EXPAND, 10)
        
        self.SetSizer(main_sizer)
        self._update_button_states()
    
    def _bind_events(self):
        """Bind event handlers."""
        self.filter_choice.Bind(wx.EVT_CHOICE, self._on_filter_changed)
        self.refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_selection_changed)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_view_details)
        self.view_btn.Bind(wx.EVT_BUTTON, self._on_view_details)
        self.approve_btn.Bind(wx.EVT_BUTTON, self._on_approve)
        self.reject_btn.Bind(wx.EVT_BUTTON, self._on_reject)
        self.apply_btn.Bind(wx.EVT_BUTTON, self._on_apply)
        self.apply_all_btn.Bind(wx.EVT_BUTTON, self._on_apply_all)
    
    def _refresh_list(self):
        """Refresh the corrections list."""
        self.list_ctrl.DeleteAllItems()
        
        # Get filtered corrections
        filter_text = self.filter_choice.GetStringSelection()
        if filter_text == "All":
            corrections = self.manager.queue.get_all()
        else:
            status_map = {
                "Pending": CorrectionStatus.PENDING,
                "Approved": CorrectionStatus.APPROVED,
                "Rejected": CorrectionStatus.REJECTED,
                "Applied": CorrectionStatus.APPLIED,
            }
            status = status_map.get(filter_text, CorrectionStatus.PENDING)
            corrections = self.manager.queue.get_by_status(status)
        
        # Populate list
        self._corrections = corrections
        for i, correction in enumerate(corrections):
            self.list_ctrl.InsertItem(i, correction.affiliate_name)
            self.list_ctrl.SetItem(i, 1, correction.affiliate_type)
            self.list_ctrl.SetItem(i, 2, ", ".join(correction.corrections.keys()))
            self.list_ctrl.SetItem(i, 3, correction.submitted_at[:10])
            self.list_ctrl.SetItem(i, 4, correction.status.upper())
        
        # Update status
        pending = self.manager.get_pending_count()
        approved = self.manager.get_approved_count()
        self.status_text.SetLabel(
            f"Pending: {pending} | Approved (ready to apply): {approved}"
        )
        
        self._update_button_states()
    
    def _get_selected_correction(self) -> Optional[AffiliateCorrection]:
        """Get the currently selected correction."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx == -1 or idx >= len(self._corrections):
            return None
        return self._corrections[idx]
    
    def _update_button_states(self):
        """Update button enabled states based on selection."""
        correction = self._get_selected_correction()
        has_selection = correction is not None
        
        self.view_btn.Enable(has_selection)
        self.approve_btn.Enable(has_selection and correction.is_pending())
        self.reject_btn.Enable(has_selection and correction.is_pending())
        self.apply_btn.Enable(has_selection and correction.is_approved())
        self.apply_all_btn.Enable(self.manager.get_approved_count() > 0)
    
    def _on_filter_changed(self, event):
        """Handle filter change."""
        self._refresh_list()
    
    def _on_refresh(self, event):
        """Handle refresh button."""
        self._refresh_list()
    
    def _on_selection_changed(self, event):
        """Handle list selection change."""
        self._update_button_states()
        event.Skip()
    
    def _on_view_details(self, event):
        """Show correction details dialog."""
        correction = self._get_selected_correction()
        if correction is None:
            return
        
        dialog = CorrectionDetailsDialog(self, correction)
        dialog.ShowModal()
        dialog.Destroy()
    
    def _on_approve(self, event):
        """Approve the selected correction."""
        correction = self._get_selected_correction()
        if correction is None:
            return
        
        # Confirm
        result = wx.MessageBox(
            f"Approve correction for {correction.affiliate_name}?\n\n"
            f"Changes:\n{correction.get_changes_summary()}",
            "Confirm Approval",
            wx.YES_NO | wx.ICON_QUESTION,
            self
        )
        
        if result == wx.YES:
            success, message = self.manager.approve_correction(
                correction.id, self.admin_name
            )
            if success:
                wx.MessageBox(
                    "Correction approved. Use 'Apply to Data' to update the XML file.",
                    "Approved",
                    wx.OK | wx.ICON_INFORMATION,
                    self
                )
            else:
                wx.MessageBox(f"Error: {message}", "Error", wx.OK | wx.ICON_ERROR, self)
            self._refresh_list()
    
    def _on_reject(self, event):
        """Reject the selected correction."""
        correction = self._get_selected_correction()
        if correction is None:
            return
        
        # Get rejection reason
        dialog = wx.TextEntryDialog(
            self,
            "Enter reason for rejection:",
            "Reject Correction",
            ""
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            reason = dialog.GetValue().strip() or "No reason provided"
            success, message = self.manager.reject_correction(
                correction.id, self.admin_name, reason
            )
            if success:
                wx.MessageBox("Correction rejected.", "Rejected", wx.OK | wx.ICON_INFORMATION, self)
            else:
                wx.MessageBox(f"Error: {message}", "Error", wx.OK | wx.ICON_ERROR, self)
            self._refresh_list()
        
        dialog.Destroy()
    
    def _on_apply(self, event):
        """Apply the selected approved correction."""
        correction = self._get_selected_correction()
        if correction is None:
            return
        
        # Confirm with warning
        result = wx.MessageBox(
            f"Apply correction to XML data for {correction.affiliate_name}?\n\n"
            f"This will modify the affiliate data file.\n"
            f"A backup will be created automatically.\n\n"
            f"Changes:\n{correction.get_changes_summary()}",
            "Confirm Apply",
            wx.YES_NO | wx.ICON_WARNING,
            self
        )
        
        if result == wx.YES:
            success, message = self.manager.apply_correction(
                correction.id, self.admin_name
            )
            if success:
                wx.MessageBox(
                    f"Correction applied successfully!\n\n{message}",
                    "Applied",
                    wx.OK | wx.ICON_INFORMATION,
                    self
                )
            else:
                wx.MessageBox(
                    f"Failed to apply correction:\n\n{message}",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                    self
                )
            self._refresh_list()
    
    def _on_apply_all(self, event):
        """Apply all approved corrections."""
        approved_count = self.manager.get_approved_count()
        
        result = wx.MessageBox(
            f"Apply all {approved_count} approved correction(s)?\n\n"
            f"This will modify the affiliate data files.\n"
            f"Backups will be created automatically.",
            "Confirm Apply All",
            wx.YES_NO | wx.ICON_WARNING,
            self
        )
        
        if result == wx.YES:
            results = self.manager.apply_all_approved(self.admin_name)
            
            successes = sum(1 for _, success, _ in results if success)
            failures = len(results) - successes
            
            if failures == 0:
                wx.MessageBox(
                    f"Successfully applied {successes} correction(s).",
                    "All Applied",
                    wx.OK | wx.ICON_INFORMATION,
                    self
                )
            else:
                wx.MessageBox(
                    f"Applied {successes}, failed {failures}.\n\n"
                    f"Check the list for details.",
                    "Partial Success",
                    wx.OK | wx.ICON_WARNING,
                    self
                )
            
            self._refresh_list()


class AdminReviewDialog(wx.Dialog):
    """
    Standalone dialog for admin review.
    
    This dialog requires admin authentication before allowing access.
    """
    
    def __init__(
        self,
        parent: Optional[wx.Window],
        manager: CorrectionManager,
        admin_name: Optional[str] = None
    ):
        """
        Initialize the admin review dialog.
        
        Args:
            parent: Parent window
            manager: CorrectionManager instance
            admin_name: Authenticated admin username
        """
        super().__init__(
            parent,
            title="Affiliate Correction Admin - ACB Link",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        )
        
        self.SetSize(800, 600)
        self.SetMinSize((600, 400))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = AdminReviewPanel(self, manager, admin_name=admin_name)
        sizer.Add(self.panel, 1, wx.EXPAND)
        
        # Close button
        close_btn = wx.Button(self, wx.ID_CLOSE, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        sizer.Add(close_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        self.SetSizer(sizer)
        self.Centre()


# =============================================================================
# Public API
# =============================================================================

def show_admin_review_dialog(
    parent: Optional[wx.Window] = None,
    data_dir: Optional[Path] = None,
    xml_dir: Optional[Path] = None,
    admin_name: Optional[str] = None
) -> int:
    """
    Show the admin review dialog with authentication.
    
    This function requires AFFILIATE_ADMIN role or higher.
    If admin_name is not provided, the caller should ensure
    authentication was performed via admin_auth_ui.require_admin_login().
    
    Args:
        parent: Parent window
        data_dir: Directory for queue/audit files
        xml_dir: Directory containing XML data files
        admin_name: Authenticated admin username
        
    Returns:
        Dialog result (wx.ID_CLOSE)
    """
    # Import here to avoid circular imports
    from .admin_auth_ui import require_admin_login
    from .github_admin import AdminRole
    
    # Require authentication if admin_name not provided
    if admin_name is None:
        success, session = require_admin_login(
            parent,
            required_role=AdminRole.AFFILIATE_ADMIN,
            context="Affiliate Correction Administration"
        )
        if not success or session is None:
            return wx.ID_CANCEL
        admin_name = session.display_name
    
    manager = CorrectionManager(data_dir, xml_dir)
    dialog = AdminReviewDialog(parent, manager, admin_name=admin_name)
    result = dialog.ShowModal()
    dialog.Destroy()
    return result


def get_correction_manager(
    data_dir: Optional[Path] = None,
    xml_dir: Optional[Path] = None
) -> CorrectionManager:
    """
    Get a CorrectionManager instance.
    
    This is the main entry point for programmatic access.
    """
    return CorrectionManager(data_dir, xml_dir)


def submit_affiliate_correction(
    affiliate_name: str,
    affiliate_type: str,
    state_code: str,
    corrections: Dict[str, str],
    notes: str = "",
    is_affiliated: bool = False,
    data_dir: Optional[Path] = None,
    xml_dir: Optional[Path] = None
) -> str:
    """
    Submit an affiliate correction for review.
    
    This is a convenience function for submitting corrections
    programmatically, e.g., from the existing AffiliateCorrectionDialog.
    
    Returns:
        The correction ID
    """
    manager = CorrectionManager(data_dir, xml_dir)
    correction = manager.submit_correction(
        affiliate_name=affiliate_name,
        affiliate_type=affiliate_type,
        state_code=state_code,
        corrections=corrections,
        notes=notes,
        is_affiliated=is_affiliated
    )
    return correction.id
