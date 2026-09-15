from datetime import datetime, timezone
from app import db

class Student(db.Model):
    """
    Student model representing a preloaded student directory record.
    Students cannot register unless their record is preloaded here.
    """
    __tablename__ = 'students'

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(10), nullable=False)
    college_email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    points = db.Column(db.Integer, default=0, nullable=False)  # Reward points for leaderboard
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    account = db.relationship('Account', backref='student', uselist=False, cascade='all, delete-orphan')
    lost_items = db.relationship('LostItem', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    found_items = db.relationship('FoundItem', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    claims = db.relationship('Claim', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Serialize student information."""
        return {
            'student_id': self.student_id,
            'roll_number': self.roll_number,
            'student_name': self.student_name,
            'full_name': self.student_name,
            'name': self.student_name,
            'department': self.department,
            'year': self.year,
            'section': self.section,
            'college_email': self.college_email,
            'email': self.college_email,
            'points': self.points,
            'is_email_verified': self.is_email_verified,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Student {self.roll_number}: {self.student_name}>'
