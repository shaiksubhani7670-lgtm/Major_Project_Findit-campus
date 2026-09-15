from datetime import datetime, timezone
from app import db

class QuestionAnswer(db.Model):
    """
    Stores answers to category-specific questions for reports.
    """
    __tablename__ = 'question_answers'

    answer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_type = db.Column(db.String(50), nullable=False)  # 'lost' or 'found'
    report_id = db.Column(db.Integer, nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Serialize question-answer mapping."""
        return {
            'answer_id': self.answer_id,
            'report_type': self.report_type,
            'report_id': self.report_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<QuestionAnswer {self.answer_id}: {self.report_type}#{self.report_id}>'
