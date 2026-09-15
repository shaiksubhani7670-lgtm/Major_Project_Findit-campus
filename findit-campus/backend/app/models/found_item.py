from datetime import datetime, timezone
from app import db

class FoundItem(db.Model):
    """
    Found item report submitted by a student.
    """
    __tablename__ = 'found_items'

    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=True)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(500), nullable=True)  # Primary image (backward compat)
    image_paths = db.Column(db.JSON, nullable=True)  # Up to 5 image URLs
    additional_details = db.Column(db.JSON, nullable=True)  # Store category-specific fields as JSON
    status = db.Column(db.String(50), default='Searching', nullable=False, index=True) # 'Searching', 'Matched', 'Claim Pending', 'Completed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    matches = db.relationship('Match', backref='found_item', lazy='dynamic', foreign_keys='Match.found_report_id', cascade='all, delete-orphan')

    @property
    def id(self):
        """Alias for compatibility with existing code."""
        return self.report_id

    def to_dict(self):
        """Serialize found item to dictionary."""
        return {
            'report_id': self.report_id,
            'id': self.report_id,
            'student_id': self.student_id,
            'category': self.category,
            'item_name': self.item_name,
            'color': self.color,
            'location': self.location,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.isoformat() if self.time else None,
            'description': self.description,
            'image_path': self.image_path,
            'image_paths': self.image_paths or ([self.image_path] if self.image_path else []),
            'additional_details': self.additional_details,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<FoundItem {self.report_id}: {self.item_name}>'
