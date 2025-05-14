from datetime import datetime
from src.models.db import db # Updated import

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # For group chats, null for one-on-one
    chat_type = db.Column(db.String(20), nullable=False, default='one_on_one') # Enum-like: 'one_on_one', 'group'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    participants = db.relationship('ChatParticipant', back_populates='chat', lazy='dynamic', cascade="all, delete-orphan")
    messages = db.relationship('Message', back_populates='chat', lazy='dynamic', order_by='Message.timestamp.desc()', cascade="all, delete-orphan")

    def __init__(self, chat_type, name=None):
        self.chat_type = chat_type
        if chat_type == 'group' and not name:
            raise ValueError("Group chats must have a name.")
        self.name = name

    def __repr__(self):
        return f'<Chat {self.id} - {self.name if self.name else self.chat_type}>'
