from flask import Blueprint, render_template, request, jsonify
from werkzeug.security import generate_password_hash
from route.database import db_session
from models.models import User


@create_user_bp.route('/create-user', methods=['GET'])
def create_user_page():
    """Serve the user creation page."""
    return render_template('create_user.html')

@create_user_bp.route('/api/create-user', methods=['POST'])
def create_user():
    """Handles user creation via API."""
    data = request.get_json()
    username = data.get('username').strip()
    email = data.get('email').strip()
    password = data.get('password')
    role = data.get('role', 'regular').lower()

    if role not in ['admin', 'regular']:
        return jsonify({"message": "Invalid role. Choose 'admin' or 'regular'."}), 400

    # Check if username or email already exists
    existing_user = db_session.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({"message": "Username or email already exists. Choose a different one."}), 409

    # Hash the password securely
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    # Create and save new user
    new_user = User(username=username, email=email, password=hashed_password, role=role)
    db_session.add(new_user)
    db_session.commit()

    return jsonify({"message": f"User '{username}' created successfully!"}), 201
