from datetime import datetime
from src.models.db import db # Updated import

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default="sent") # Enum-like: "sent", "delivered", "read"

    # Relationships
    sender = db.relationship("User", backref=db.backref("sent_messages", lazy="dynamic"))
    chat = db.relationship("Chat", back_populates="messages")

    def __init__(self, chat_id, sender_id, content):
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.content = content

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} in chat {self.chat_id}>"
