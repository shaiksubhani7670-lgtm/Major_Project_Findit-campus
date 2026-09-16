from datetime import datetime, timezone
from app import db

class UploadedImage(db.Model):
    """
    Persistent storage for uploaded images in the database (Neon PostgreSQL/SQLite).
    Ensures image persistence on serverless hosts like Vercel.
    """
    __tablename__ = 'uploaded_images'

    filename = db.Column(db.String(255), primary_key=True)
    report_type = db.Column(db.String(50), nullable=True)
    content_type = db.Column(db.String(100), default='image/jpeg')
    image_data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UploadedImage {self.filename}>'
