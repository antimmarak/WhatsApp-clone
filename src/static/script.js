document.addEventListener("DOMContentLoaded", () => {
    const authView = document.getElementById("auth-view");
    const chatView = document.getElementById("chat-view");

    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const showRegisterLink = document.getElementById("show-register");
    const showLoginLink = document.getElementById("show-login");

    const loginUsernameInput = document.getElementById("login-username");
    const loginPasswordInput = document.getElementById("login-password");
    const loginButton = document.getElementById("login-button");

    const registerUsernameInput = document.getElementById("register-username");
    const registerPasswordInput = document.getElementById("register-password");
    const registerButton = document.getElementById("register-button");

    const currentUsernameDisplay = document.getElementById("current-username");
    const logoutButton = document.getElementById("logout-button");

    const addContactUsernameInput = document.getElementById("add-contact-username");
    const addContactButton = document.getElementById("add-contact-button");
    const contactsListUl = document.getElementById("contacts-list");
    const chatsListUl = document.getElementById("chats-list");

    const chatWithUsernameDisplay = document.getElementById("chat-with-username");
    const messagesContainer = document.getElementById("messages-container");
    const messageInput = document.getElementById("message-input");
    const sendMessageButton = document.getElementById("send-message-button");

    let socket = null;
    let currentChatId = null;
    let currentUserId = null;
    let currentOpenChatName = null;

    // --- API Helper ---
    async function apiRequest(endpoint, method = "GET", body = null) {
        const headers = {
            "Content-Type": "application/json",
        };
        const options = { method, headers };
        if (body) {
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: "Request failed with status: " + response.status }));
                console.error("API Error:", errorData);
                alert(`Error: ${errorData.error || "Unknown error"}`);
                return null;
            }
            if (response.status === 204) return true; // No content for successful DELETE etc.
            return await response.json();
        } catch (error) {
            console.error("Network or API request error:", error);
            alert("Network error. Please try again.");
            return null;
        }
    }

    // --- Authentication ---
    showRegisterLink.addEventListener("click", (e) => {
        e.preventDefault();
        loginForm.style.display = "none";
        registerForm.style.display = "block";
    });

    showLoginLink.addEventListener("click", (e) => {
        e.preventDefault();
        registerForm.style.display = "none";
        loginForm.style.display = "block";
    });

    registerButton.addEventListener("click", async () => {
        const username = registerUsernameInput.value.trim();
        const password = registerPasswordInput.value.trim();
        if (!username || !password) {
            alert("Username and password are required for registration.");
            return;
        }
        const result = await apiRequest("/auth/register", "POST", { username, password });
        if (result && result.message) {
            alert(result.message);
            // Automatically switch to login form or attempt login
            registerForm.style.display = "none";
            loginForm.style.display = "block";
            loginUsernameInput.value = username;
            loginPasswordInput.value = ""; // Clear password for security
        } 
    });

    loginButton.addEventListener("click", async () => {
        const username = loginUsernameInput.value.trim();
        const password = loginPasswordInput.value.trim();
        if (!username || !password) {
            alert("Username and password are required for login.");
            return;
        }
        const result = await apiRequest("/auth/login", "POST", { username, password });
        if (result && result.user_id) {
            currentUserId = result.user_id;
            switchToChatView(username);
        } 
    });

    logoutButton.addEventListener("click", async () => {
        const result = await apiRequest("/auth/logout", "GET");
        if (result) {
            switchToAuthView();
        }
    });

    async function checkAuthStatus() {
        const result = await apiRequest("/auth/status");
        if (result && result.is_authenticated) {
            currentUserId = result.user_id;
            switchToChatView(result.username);
            return true;
        }
        switchToAuthView();
        return false;
    }

    // --- UI Switching ---
    function switchToChatView(username) {
        authView.style.display = "none";
        chatView.style.display = "flex";
        currentUsernameDisplay.textContent = username;
        initializeSocket();
        loadContacts();
        loadChats();
    }

    function switchToAuthView() {
        if (socket) {
            socket.disconnect();
            socket = null;
        }
        authView.style.display = "flex";
        chatView.style.display = "none";
        currentChatId = null;
        currentUserId = null;
        currentOpenChatName = null;
        chatsListUl.innerHTML = "";
        contactsListUl.innerHTML = "";
        messagesContainer.innerHTML = "";
        chatWithUsernameDisplay.textContent = "Select a chat";
        loginUsernameInput.value = "";
        loginPasswordInput.value = "";
        registerUsernameInput.value = "";
        registerPasswordInput.value = "";
    }

    // --- Socket.IO ---
    function initializeSocket() {
        if (socket) socket.disconnect();
        socket = io({ autoConnect: false }); // Connect manually after login

        socket.on("connect", () => {
            console.log("Socket connected:", socket.id);
            // If a chat was open, try to rejoin its room
            if (currentChatId) {
                socket.emit("join_chat", { chat_id: currentChatId });
            }
        });

        socket.on("disconnect", () => {
            console.log("Socket disconnected");
        });

        socket.on("new_message", (message) => {
            console.log("New message received:", message);
            if (message.chat_id === currentChatId) {
                appendMessage(message);
            }
            // Update chat list preview (optional, can be complex)
            loadChats(); // Reload chats to update last message preview
        });

        socket.on("status", (status) => {
            console.log("Status update:", status);
            // Could display status messages in UI if needed
        });

        socket.on("error", (error) => {
            console.error("Socket Error:", error);
            alert(`Socket error: ${error.message}`);
        });
        socket.connect();
    }

    // --- Contact Management ---
    addContactButton.addEventListener("click", async () => {
        const contactUsername = addContactUsernameInput.value.trim();
        if (!contactUsername) {
            alert("Enter username to add contact.");
            return;
        }
        const result = await apiRequest("/chat/contacts/add", "POST", { username: contactUsername });
        if (result) {
            alert(result.message || "Contact added!");
            addContactUsernameInput.value = "";
            loadContacts();
        }
    });

    async function loadContacts() {
        const contacts = await apiRequest("/chat/contacts");
        contactsListUl.innerHTML = "";
        if (contacts && contacts.length > 0) {
            contacts.forEach(contact => {
                const li = document.createElement("li");
                li.textContent = contact.alias || contact.username;
                li.dataset.contactUserId = contact.user_id;
                li.dataset.contactUsername = contact.username;
                li.addEventListener("click", () => openChatWithContact(contact.user_id, contact.username));
                contactsListUl.appendChild(li);
            });
        }
    }

    async function openChatWithContact(contactUserId, contactUsername) {
        // Check if a one-on-one chat already exists or create one
        const result = await apiRequest("/chat/chats/create", "POST", { target_user_id: contactUserId });
        if (result && result.chat_id) {
            loadChats(); // Refresh chat list
            openChat(result.chat_id, contactUsername); 
        } else if (result && result.message === "Chat already exists") {
            // This case should ideally return the chat_id too, handled by server now
            // For now, we just reload chats and let user click from the list
            loadChats().then(() => {
                // Try to find and open the existing chat
                const existingChatLi = Array.from(chatsListUl.children).find(li => {
                    // This is a heuristic, depends on how chat names are formed for 1-on-1
                    return li.textContent.includes(contactUsername);
                });
                if (existingChatLi) {
                    existingChatLi.click();
                }
            });
        }
    }

    // --- Chat Functionality ---
    async function loadChats() {
        const chats = await apiRequest("/chat/chats");
        chatsListUl.innerHTML = "";
        if (chats && chats.length > 0) {
            chats.forEach(chat => {
                const li = document.createElement("li");
                li.textContent = chat.name; // Server now provides a good name
                li.dataset.chatId = chat.chat_id;
                li.dataset.chatName = chat.name;
                if (chat.chat_id === currentChatId) {
                    li.classList.add("active-chat");
                }
                li.addEventListener("click", () => openChat(chat.chat_id, chat.name));
                chatsListUl.appendChild(li);
            });
        }
    }

    function openChat(chatId, chatName) {
        if (currentChatId && socket) {
            socket.emit("leave_chat", { chat_id: currentChatId });
        }
        currentChatId = chatId;
        currentOpenChatName = chatName;
        chatWithUsernameDisplay.textContent = `Chat with ${chatName}`;
        messagesContainer.innerHTML = ""; // Clear previous messages
        
        // Highlight active chat
        Array.from(chatsListUl.children).forEach(li => {
            li.classList.remove("active-chat");
            if (parseInt(li.dataset.chatId) === chatId) {
                li.classList.add("active-chat");
            }
        });

        if (socket) {
            socket.emit("join_chat", { chat_id: chatId });
        }
        loadMessages(chatId);
    }

    async function loadMessages(chatId) {
        const messages = await apiRequest(`/chat/chats/${chatId}/messages`);
        messagesContainer.innerHTML = ""; // Clear again just in case
        if (messages && messages.length > 0) {
            messages.forEach(appendMessage);
        }
    }

    function appendMessage(message) {
        const messageBubble = document.createElement("div");
        messageBubble.classList.add("message-bubble");

        const senderNameSpan = document.createElement("div");
        senderNameSpan.classList.add("sender-name");
        
        if (message.sender_id === currentUserId) {
            messageBubble.classList.add("sent");
            // senderNameSpan.textContent = "You"; // Optional: or hide for self
        } else {
            messageBubble.classList.add("received");
            senderNameSpan.textContent = message.sender_username;
            messageBubble.appendChild(senderNameSpan);
        }

        const contentP = document.createElement("p");
        contentP.textContent = message.content;
        messageBubble.appendChild(contentP);

        const timestampSpan = document.createElement("div");
        timestampSpan.classList.add("timestamp");
        timestampSpan.textContent = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageBubble.appendChild(timestampSpan);

        messagesContainer.appendChild(messageBubble);
        messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to bottom
    }

    sendMessageButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        const content = messageInput.value.trim();
        if (!content || !currentChatId || !socket) {
            if(!socket) alert("Not connected to chat server.");
            return;
        }
        socket.emit("send_message", { chat_id: currentChatId, content: content });
        messageInput.value = "";
    }

    // --- Initial Load ---
    checkAuthStatus();
});

