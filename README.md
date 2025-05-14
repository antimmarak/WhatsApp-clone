# WhatsApp Clone Web Application

## Overview

This project is a web-based communication application designed to mimic some of the core functionalities of WhatsApp. It allows users to register, log in, add contacts, create one-on-one and group chats, and exchange messages in real-time.

## Features Implemented

1.  **User Authentication**:
    *   User registration with username and password.
    *   Secure login and logout functionality.
    *   Session management using Flask-Login.

2.  **Contact Management**:
    *   Ability to add other registered users as contacts by their username.
    *   View a list of added contacts.
    *   (Removing contacts is also implemented via API).

3.  **Chat Functionality**:
    *   **One-on-One Chats**: Users can initiate private chats with their contacts.
    *   **Group Chats**: Users can create group chats by selecting participants (though the UI for group creation is basic, the backend supports it via API).
    *   **List Chats**: Users can see a list of their active chats, sorted by the most recent message.

4.  **Real-time Messaging**:
    *   Messages are sent and received in real-time using WebSockets (Flask-SocketIO).
    *   Users in a chat room receive new messages instantly.
    *   Message content, sender information, and timestamps are displayed.

5.  **Message Status**:
    *   Basic "sent" status is implemented for messages.
    *   (Further statuses like "delivered" and "read" can be future enhancements).

6.  **User Interface**:
    *   A responsive web interface built with HTML, CSS, and vanilla JavaScript.
    *   Separate views for authentication and the main chat application.
    *   Chat interface includes a sidebar for contacts and chats, and a main area for messages.
    *   Styled to be reminiscent of WhatsApp, with considerations for desktop and mobile layouts.

## Technology Stack

*   **Backend**: Flask (Python web framework)
*   **Real-time Communication**: Flask-SocketIO (WebSockets)
*   **Database**: SQLite (for ease of setup and development)
*   **ORM**: SQLAlchemy (with Flask-SQLAlchemy)
*   **Authentication**: Flask-Login
*   **Frontend**: HTML, CSS, JavaScript (no external frontend frameworks used for simplicity)

## Project Structure

The application is organized as follows:

```
/whatsapp_clone
├── src/
│   ├── models/             # SQLAlchemy database models (user.py, contact.py, chat.py, etc.)
│   │   ├── __init__.py
│   │   ├── db.py           # SQLAlchemy db instance
│   │   ├── user.py
│   │   ├── contact.py
│   │   ├── chat.py
│   │   ├── chat_participant.py
│   │   └── message.py
│   ├── routes/             # Flask blueprints for different parts of the app
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication routes (login, register, logout)
│   │   └── chat_routes.py  # Chat and contact management API routes
│   ├── static/             # Frontend static files
│   │   ├── index.html      # Main HTML file for the SPA
│   │   ├── style.css       # CSS styles
│   │   └── script.js       # JavaScript for frontend logic and SocketIO communication
│   └── main.py             # Main Flask application setup, SocketIO handlers, and server run
├── venv/                   # Python virtual environment (if created locally)
├── app.db                  # SQLite database file (created on first run)
└── requirements.txt        # Python dependencies
```

## How to Run Locally

1.  **Prerequisites**:
    *   Python 3.8+ installed.
    *   `pip` (Python package installer).

2.  **Setup**:
    *   Unzip the provided `whatsapp_clone.zip` file.
    *   Navigate to the `whatsapp_clone` directory in your terminal.
    *   Create a Python virtual environment (recommended):
        ```bash
        python3 -m venv venv
        ```
    *   Activate the virtual environment:
        *   On macOS and Linux: `source venv/bin/activate`
        *   On Windows: `venv\Scripts\activate`
    *   Install the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Running the Application**:
    *   Once the dependencies are installed and the virtual environment is active, run the Flask application:
        ```bash
        python src/main.py
        ```
    *   The application will start, and you should see output indicating it's running (usually on `http://127.0.0.1:5000/` or `http://0.0.0.0:5000/`).

4.  **Accessing the Application**:
    *   Open your web browser and navigate to `http://127.0.0.1:5000/` (or the URL shown in your terminal).

## Using the Application

1.  **Register**: Create a new user account.
2.  **Login**: Log in with your registered credentials.
3.  **Add Contacts**: In the chat view, use the "Add Contact" section by entering the username of another registered user.
4.  **Start Chats**: 
    *   Click on a contact from the "Contacts" list to initiate or open a one-on-one chat.
    *   (Group chat creation via UI is basic; the backend supports creating group chats via API calls if extended).
5.  **Send Messages**: Type your message in the input field and click "Send" or press Enter.

## Further Enhancements (Potential Future Work)

*   Full group chat management UI (creating groups, adding/removing members).
*   Advanced message statuses (delivered, read receipts).
*   Media sharing (images, videos, files).
*   User profiles with avatars.
*   Push notifications.
*   End-to-end encryption (significant complexity).
*   More robust error handling and user feedback on the frontend.
*   Formal unit and integration tests.
*   Deployment to a production environment with a proper WSGI server (e.g., Gunicorn) and database (e.g., PostgreSQL or MySQL).

This application serves as a functional prototype demonstrating core real-time chat features.

