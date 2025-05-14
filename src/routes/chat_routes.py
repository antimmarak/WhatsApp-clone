from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models import db
from src.models.user import User
from src.models.contact import Contact
from src.models.chat import Chat
from src.models.chat_participant import ChatParticipant
from src.models.message import Message

chat_bp = Blueprint("chat", __name__)

# Contact Management Routes
@chat_bp.route("/contacts", methods=["GET"])
@login_required
def list_contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    contact_list = []
    for contact_entry in contacts:
        contact_user = User.query.get(contact_entry.contact_user_id)
        if contact_user:
            contact_list.append({
                "contact_id": contact_entry.id,
                "user_id": contact_user.id,
                "username": contact_user.username,
                "alias": contact_entry.alias or contact_user.username # Use alias if available, else username
            })
    return jsonify(contact_list), 200

@chat_bp.route("/contacts/add", methods=["POST"])
@login_required
def add_contact():
    data = request.get_json()
    contact_username = data.get("username")
    alias = data.get("alias")

    if not contact_username:
        return jsonify({"error": "Username of contact is required"}), 400

    contact_user = User.query.filter_by(username=contact_username).first()
    if not contact_user:
        return jsonify({"error": "User not found"}), 404

    if contact_user.id == current_user.id:
        return jsonify({"error": "You cannot add yourself as a contact"}), 400

    existing_contact = Contact.query.filter_by(user_id=current_user.id, contact_user_id=contact_user.id).first()
    if existing_contact:
        return jsonify({"error": "Contact already exists"}), 400

    new_contact = Contact(user_id=current_user.id, contact_user_id=contact_user.id, alias=alias)
    db.session.add(new_contact)
    db.session.commit()
    return jsonify({"message": "Contact added successfully", "contact_id": new_contact.id, "username": contact_user.username, "alias": new_contact.alias}), 201

@chat_bp.route("/contacts/remove/<int:contact_user_id>", methods=["DELETE"])
@login_required
def remove_contact(contact_user_id):
    contact_to_remove = Contact.query.filter_by(user_id=current_user.id, contact_user_id=contact_user_id).first()
    if not contact_to_remove:
        return jsonify({"error": "Contact not found"}), 404

    db.session.delete(contact_to_remove)
    db.session.commit()
    return jsonify({"message": "Contact removed successfully"}), 200

# Chat and Message Routes (can be expanded)
@chat_bp.route("/chats", methods=["GET"])
@login_required
def get_user_chats():
    # Get chats where the current user is a participant
    user_chat_associations = ChatParticipant.query.filter_by(user_id=current_user.id).all()
    chats_data = []
    for assoc in user_chat_associations:
        chat = Chat.query.get(assoc.chat_id)
        if chat:
            # Determine chat name (for one-on-one, it's the other user's name)
            chat_name = chat.name
            if chat.chat_type == 'one_on_one':
                other_participant = chat.participants.filter(ChatParticipant.user_id != current_user.id).first()
                if other_participant and other_participant.user:
                    chat_name = other_participant.user.username
                else:
                    chat_name = "Unknown User"
            
            last_message = chat.messages.order_by(Message.timestamp.desc()).first()
            chats_data.append({
                "chat_id": chat.id,
                "name": chat_name,
                "type": chat.chat_type,
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None,
                "last_message_preview": last_message.content if last_message else "No messages yet."
            })
    # Sort chats by last message time, most recent first
    chats_data.sort(key=lambda x: x["last_message_at"] or datetime.min.isoformat(), reverse=True)
    return jsonify(chats_data), 200

@chat_bp.route("/chats/create", methods=["POST"])
@login_required
def create_chat():
    data = request.get_json()
    target_user_id = data.get("target_user_id") # For one-on-one chat
    group_name = data.get("group_name") # For group chat
    participant_ids = data.get("participant_ids", []) # For group chat, list of user IDs

    if target_user_id: # Create a one-on-one chat
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({"error": "Target user not found"}), 404
        if target_user_id == current_user.id:
            return jsonify({"error": "Cannot create a chat with yourself"}), 400

        # Check if a one-on-one chat already exists between these two users
        # This query is a bit complex: find chats with exactly these two participants.
        existing_chat = db.session.query(Chat).join(ChatParticipant, Chat.id == ChatParticipant.chat_id)\
            .filter(Chat.chat_type == 'one_on_one')\
            .group_by(Chat.id)\
            .having(db.func.count(ChatParticipant.user_id) == 2)\
            .filter(db.or_(
                db.and_(ChatParticipant.user_id == current_user.id, ChatParticipant.user_id == target_user_id), # This condition is wrong
                db.and_(ChatParticipant.user_id == target_user_id, ChatParticipant.user_id == current_user.id) # This is also wrong
            )).first() # The filter for participants needs to be more robust
        
        # Simpler check: iterate through current user's one-on-one chats
        current_user_chats = Chat.query.join(ChatParticipant, Chat.id == ChatParticipant.chat_id)\
            .filter(Chat.chat_type == 'one_on_one', ChatParticipant.user_id == current_user.id).all()
        
        for chat in current_user_chats:
            participants = [p.user_id for p in chat.participants]
            if target_user_id in participants and len(participants) == 2:
                 return jsonify({"message": "Chat already exists", "chat_id": chat.id}), 200

        new_chat = Chat(chat_type='one_on_one')
        db.session.add(new_chat)
        db.session.flush() # Get the new_chat.id

        # Add participants
        p1 = ChatParticipant(chat_id=new_chat.id, user_id=current_user.id)
        p2 = ChatParticipant(chat_id=new_chat.id, user_id=target_user_id)
        db.session.add_all([p1, p2])
        db.session.commit()
        return jsonify({"message": "One-on-one chat created", "chat_id": new_chat.id}), 201

    elif group_name and participant_ids: # Create a group chat
        if not isinstance(participant_ids, list) or not participant_ids:
            return jsonify({"error": "Participant IDs must be a non-empty list for group chat"}), 400
        
        all_participant_ids = list(set([current_user.id] + [int(pid) for pid in participant_ids]))
        if len(all_participant_ids) < 2: # At least current user and one other
             return jsonify({"error": "Group chat must have at least two participants"}), 400

        new_chat = Chat(chat_type='group', name=group_name)
        db.session.add(new_chat)
        db.session.flush() # Get the new_chat.id

        participants_to_add = []
        for user_id in all_participant_ids:
            user = User.query.get(user_id)
            if not user:
                db.session.rollback() # Rollback if any user is not found
                return jsonify({"error": f"User with ID {user_id} not found"}), 404
            participants_to_add.append(ChatParticipant(chat_id=new_chat.id, user_id=user_id))
        
        db.session.add_all(participants_to_add)
        db.session.commit()
        return jsonify({"message": "Group chat created", "chat_id": new_chat.id, "name": new_chat.name}), 201
    else:
        return jsonify({"error": "Either target_user_id (for one-on-one) or group_name and participant_ids (for group) are required"}), 400

@chat_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
@login_required
def get_chat_messages(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # Check if current user is a participant of this chat
    is_participant = ChatParticipant.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not is_participant:
        return jsonify({"error": "You are not a participant of this chat"}), 403

    # Paginate messages later if needed
    messages = chat.messages.order_by(Message.timestamp.asc()).all()
    message_list = []
    for msg in messages:
        message_list.append({
            "message_id": msg.id,
            "sender_id": msg.sender_id,
            "sender_username": msg.sender.username,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "status": msg.status
        })
    return jsonify(message_list), 200

