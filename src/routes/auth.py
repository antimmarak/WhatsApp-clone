from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from src.models.user import User
from src.models import db # Assuming db is initialized in models/__init__.py or main.py

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("serve")) # Or a dashboard route

    if request.method == "POST":
        data = request.get_json() or request.form
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        # For API-based registration, return success
        if request.is_json:
            return jsonify({"message": "User registered successfully", "user_id": new_user.id}), 201
        # For form-based, redirect to login or home
        return redirect(url_for("auth.login")) 
    
    # For GET request, render a registration form (if you have one)
    # return render_template("register.html") # Assuming you have a register.html
    return jsonify({"message": "GET request to register endpoint. POST to register."}), 200

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("serve")) # Or a dashboard route

    if request.method == "POST":
        data = request.get_json() or request.form
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True) # Add remember=True if you want "remember me" functionality
            # For API-based login, return success
            if request.is_json:
                return jsonify({"message": "Login successful", "user_id": user.id}), 200
            # For form-based, redirect to a protected page or home
            return redirect(url_for("serve")) # Or a dashboard route
        
        return jsonify({"error": "Invalid username or password"}), 401

    # For GET request, render a login form (if you have one)
    # return render_template("login.html") # Assuming you have a login.html
    return jsonify({"message": "GET request to login endpoint. POST to login."}), 200

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    # For API-based logout
    if request.is_json:
        return jsonify({"message": "Logout successful"}), 200
    # For form-based, redirect to home or login page
    return redirect(url_for("auth.login"))

@auth_bp.route("/status")
@login_required
def status():
    return jsonify({"user_id": current_user.id, "username": current_user.username, "is_authenticated": current_user.is_authenticated}), 200

