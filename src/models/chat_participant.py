from datetime import datetime
from src.models.db import db # Updated import

class ChatParticipant(db.Model):
    __tablename__ = 'chat_participants'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('chat_associations', lazy='dynamic'))
    chat = db.relationship('Chat', back_populates='participants')

    # Ensure a user is unique per chat
    __table_args__ = (db.UniqueConstraint('chat_id', 'user_id', name='unique_user_in_chat'),)

    def __init__(self, chat_id, user_id):
        self.chat_id = chat_id
        self.user_id = user_id

    def __repr__(self):
        return f'<ChatParticipant chat_id={self.chat_id} user_id={self.user_id}>'
