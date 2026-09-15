import bcrypt
from datetime import datetime, timezone
from app import db

class Account(db.Model):
    """
    Account model representing registered student login credentials and status.
    """
    __tablename__ = 'accounts'

    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password):
        """Hash and store password using bcrypt."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Verify password using bcrypt."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def to_dict(self):
        """Serialize account information."""
        return {
            'account_id': self.account_id,
            'student_id': self.student_id,
            'status': self.status,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Account ID {self.account_id} for Student ID {self.student_id}>'
