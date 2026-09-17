from datetime import datetime, timezone
from app import db


class NotificationLog(db.Model):
    """
    Idempotency log for email/notification events.
    Prevents duplicate emails from being sent for the same event.

    The idempotency_key format is:
        <event_type>_match<match_id>_student<student_id>
    Examples:
        claim_approved_match5_student3
        owner_verified_match5_student7
        handover_arranged_match5_student3
        item_recovered_match5_student3
    """
    __tablename__ = 'notification_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idempotency_key = db.Column(db.String(300), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(100), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'idempotency_key': self.idempotency_key,
            'event_type': self.event_type,
            'recipient_email': self.recipient_email,
            'sent_at': self.sent_at.isoformat(),
        }

    def __repr__(self):
        return f'<NotificationLog {self.idempotency_key}>'
