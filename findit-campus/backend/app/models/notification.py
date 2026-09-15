from datetime import datetime, timezone
from app import db

class Notification(db.Model):
    """
    In-app notifications sent to students.
    """
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def id(self):
        """Alias for compatibility with existing code."""
        return self.notification_id

    def to_dict(self):
        """Serialize notification data."""
        return {
            'notification_id': self.notification_id,
            'id': self.notification_id,
            'student_id': self.student_id,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Notification {self.notification_id} for Student#{self.student_id}>'
