from datetime import datetime, timezone
from app import db

class Claim(db.Model):
    """
    Claim request from a student verifying ownership of a matched item.
    """
    __tablename__ = 'claims'

    claim_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.match_id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    verification_score = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), default='Pending', nullable=False, index=True) # 'Pending', 'Approved', 'Rejected', 'Completed'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def id(self):
        """Alias for compatibility with existing code."""
        return self.claim_id

    def to_dict(self):
        """Serialize claim details."""
        return {
            'claim_id': self.claim_id,
            'id': self.claim_id,
            'match_id': self.match_id,
            'student_id': self.student_id,
            'verification_score': self.verification_score,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Claim {self.claim_id}: Match#{self.match_id} for Student#{self.student_id} ({self.status})>'
