from datetime import datetime
from src.models.db import db # Updated import

class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alias = db.Column(db.String(80), nullable=True) # Optional alias for the contact
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships to User model for user_id and contact_user_id
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('contact_entries', lazy=True))
    contact_user = db.relationship('User', foreign_keys=[contact_user_id])

    # Ensure a user cannot add themselves as a contact and a contact pair is unique
    __table_args__ = (db.UniqueConstraint('user_id', 'contact_user_id', name='unique_contact_pair'),
                      db.CheckConstraint('user_id != contact_user_id', name='check_user_not_contact_self'))

    def __init__(self, user_id, contact_user_id, alias=None):
        self.user_id = user_id
        self.contact_user_id = contact_user_id
        self.alias = alias

    def __repr__(self):
        return f'<Contact {self.user_id} - {self.contact_user_id}>'
