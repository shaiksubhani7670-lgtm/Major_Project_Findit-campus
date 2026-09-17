from datetime import datetime, timezone
from app import db


class CampusLocation(db.Model):
    """
    Campus QR Location — each record represents a physical campus location
    that has a corresponding QR code for quick Found Item reporting.
    """
    __tablename__ = 'campus_locations'

    location_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    # e.g. 'library', 'canteen', 'lab_a1'
    location_name = db.Column(db.String(200), nullable=False)
    # e.g. 'Library', 'Canteen', 'Lab A1'
    description = db.Column(db.Text, nullable=True)
    building = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'location_id': self.location_id,
            'location_key': self.location_key,
            'location_name': self.location_name,
            'description': self.description,
            'building': self.building,
            'is_active': self.is_active,
            'qr_url': f'/api/qr/{self.location_key}',
            'report_url': f'/report-found?location={self.location_key}',
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<CampusLocation {self.location_key}: {self.location_name}>'
