from datetime import datetime, timezone
from app import db


class Message(db.Model):
    """
    In-app secure message between students in the context of a match.
    """
    __tablename__ = 'messages'

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.match_id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Serialize message."""
        from app.models.student import Student
        sender = Student.query.get(self.sender_id)
        return {
            'message_id': self.message_id,
            'match_id': self.match_id,
            'sender_id': self.sender_id,
            'sender_name': sender.student_name if sender else 'Unknown',
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Message {self.message_id} in Match#{self.match_id}>'


class PushSubscription(db.Model):
    """
    Browser push notification subscription for a student.
    """
    __tablename__ = 'push_subscriptions'

    sub_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    subscription_json = db.Column(db.JSON, nullable=False)  # Full PushSubscription object from browser
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'sub_id': self.sub_id,
            'student_id': self.student_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<PushSubscription Student#{self.student_id}>'
