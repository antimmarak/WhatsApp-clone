import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request # Added request for socketio
# from flask_sqlalchemy import SQLAlchemy # Removed, as db is now in models.db
from flask_login import LoginManager, current_user # Added current_user for socketio
from flask_socketio import SocketIO, emit, join_room, leave_room # Added socketio imports

# Import db instance from models.db
from src.models.db import db

# Import models here to ensure they are known to SQLAlchemy before db.create_all()
from src.models.user import User
from src.models.contact import Contact
from src.models.chat import Chat
from src.models.chat_participant import ChatParticipant
from src.models.message import Message

# Initialize extensions that are not db
login_manager = LoginManager()
socketio = SocketIO()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed_in_production')

# Configure SQLite database (using an absolute path is safer)
app_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(app_dir)
db_path = os.path.join(project_root, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # Initialize db with the app
login_manager.init_app(app)
login_manager.login_view = 'auth.login' 
socketio.init_app(app, cors_allowed_origins="*") # Allow all origins for SocketIO during development

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import and register blueprints
from src.routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from src.routes.chat_routes import chat_bp # Import chat blueprint
app.register_blueprint(chat_bp, url_prefix='/chat') # Register chat blueprint

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "Welcome to the WhatsApp Clone API. No frontend UI is available at the root yet.", 200

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f'Client connected: {current_user.username} ({request.sid})')
        join_room(str(current_user.id)) 
    else:
        print(f'Anonymous client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        print(f'Client disconnected: {current_user.username} ({request.sid})')
        leave_room(str(current_user.id))
    else:
        print(f'Anonymous client disconnected: {request.sid}')

@socketio.on('join_chat')
def handle_join_chat(data):
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required to join chat.'})
        return

    chat_id = data.get('chat_id')
    if not chat_id:
        emit('error', {'message': 'chat_id is required.'})
        return

    chat = Chat.query.get(chat_id)
    if not chat:
        emit('error', {'message': 'Chat not found.'})
        return

    is_participant = ChatParticipant.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not is_participant:
        emit('error', {'message': 'You are not a participant of this chat.'})
        return

    room_name = f'chat_{chat_id}'
    join_room(room_name)
    print(f'{current_user.username} joined room {room_name}')
    emit('status', {'message': f'User {current_user.username} joined chat {chat_id}.'}, room=room_name)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required to leave chat.'})
        return
        
    chat_id = data.get('chat_id')
    if not chat_id:
        emit('error', {'message': 'chat_id is required.'})
        return

    room_name = f'chat_{chat_id}'
    leave_room(room_name)
    print(f'{current_user.username} left room {room_name}')
    emit('status', {'message': f'User {current_user.username} left chat {chat_id}.'}, room=room_name)

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required to send messages.'})
        return

    chat_id = data.get('chat_id')
    content = data.get('content')

    if not chat_id or not content:
        emit('error', {'message': 'chat_id and content are required.'})
        return

    chat = Chat.query.get(chat_id)
    if not chat:
        emit('error', {'message': 'Chat not found.'})
        return

    is_participant = ChatParticipant.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not is_participant:
        emit('error', {'message': 'You are not a participant of this chat.'})
        return

    new_message = Message(chat_id=chat_id, sender_id=current_user.id, content=content)
    db.session.add(new_message)
    chat.last_message_at = new_message.timestamp # Update chat's last message time
    db.session.commit()

    message_data = {
        'message_id': new_message.id,
        'chat_id': new_message.chat_id,
        'sender_id': new_message.sender_id,
        'sender_username': current_user.username,
        'content': new_message.content,
        'timestamp': new_message.timestamp.isoformat(),
        'status': new_message.status
    }
    room_name = f'chat_{chat_id}'
    socketio.emit('new_message', message_data, room=room_name)
    print(f'Message from {current_user.username} to room {room_name}: {content}')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
