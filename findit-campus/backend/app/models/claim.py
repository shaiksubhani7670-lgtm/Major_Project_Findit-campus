from datetime import datetime, timezone
from app import db

class Claim(db.Model):
    """
    Claim request from a student verifying ownership of a matched item.

    Status flow:
        Pending → Approved → (handover_status tracks physical handover)

    handover_status values:
        None              → Contact shared, awaiting physical handover
        finder_handed_over → Finder has marked item as handed over
        owner_confirmed    → Owner confirmed receipt → triggers Recovered
        issue_reported     → Handover issue was reported

    Full end-to-end status lifecycle (visible to users):
        Possible Match → Verification Pending → Claim Approved →
        Contact Details Shared → Handover Arranged →
        Recovered | Handover Issue Reported
    """
    __tablename__ = 'claims'

    claim_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.match_id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    verification_score = db.Column(db.Float, nullable=False, default=0.0)

    # Core claim status: 'Pending', 'Approved', 'Rejected', 'Completed'
    status = db.Column(db.String(50), default='Pending', nullable=False, index=True)

    # Handover tracking (nullable — only populated after claim is Approved)
    # Values: None | 'finder_handed_over' | 'owner_confirmed' | 'issue_reported'
    handover_status = db.Column(db.String(50), nullable=True, default=None)
    handover_issue_description = db.Column(db.Text, nullable=True)
    contact_shared_at = db.Column(db.DateTime, nullable=True)
    finder_handover_at = db.Column(db.DateTime, nullable=True)
    owner_confirmed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def id(self):
        """Alias for compatibility with existing code."""
        return self.claim_id

    @property
    def display_status(self):
        """
        Human-readable end-to-end status for display in UI.
        Maps internal status + handover_status to user-facing labels.
        """
        if self.status == 'Rejected':
            return 'Verification Failed'
        if self.status == 'Pending':
            return 'Verification Pending'
        if self.status == 'Approved':
            hs = self.handover_status
            if hs == 'issue_reported':
                return 'Handover Issue Reported'
            if hs == 'owner_confirmed':
                return 'Recovered'
            if hs == 'finder_handed_over':
                return 'Handover Arranged'
            if self.contact_shared_at:
                return 'Contact Details Shared'
            return 'Claim Approved'
        if self.status == 'Completed':
            return 'Recovered'
        return self.status

    def to_dict(self):
        """Serialize claim details."""
        return {
            'claim_id': self.claim_id,
            'id': self.claim_id,
            'match_id': self.match_id,
            'student_id': self.student_id,
            'verification_score': self.verification_score,
            'status': self.status,
            'display_status': self.display_status,
            'handover_status': self.handover_status,
            'handover_issue_description': self.handover_issue_description,
            'contact_shared_at': self.contact_shared_at.isoformat() if self.contact_shared_at else None,
            'finder_handover_at': self.finder_handover_at.isoformat() if self.finder_handover_at else None,
            'owner_confirmed_at': self.owner_confirmed_at.isoformat() if self.owner_confirmed_at else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Claim {self.claim_id}: Match#{self.match_id} for Student#{self.student_id} ({self.status}/{self.handover_status})>'
