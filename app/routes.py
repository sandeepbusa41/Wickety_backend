from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, pusher_client
from .models import User, Tournament
import re

main = Blueprint('main', __name__)

# Helper function to validate email
def validate_email(email):
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(email_regex, email))

# Helper function to validate phone
def validate_phone(phone):
    phone_regex = r'^\d{10}$'
    return bool(re.match(phone_regex, phone))

# Helper function to validate password
def validate_password(password):
    min_length = len(password) >= 8
    has_number = bool(re.search(r'\d', password))
    has_uppercase = bool(re.search(r'[A-Z]', password))
    return min_length and has_number and has_uppercase

# Check for duplicates
@main.route('/api/check-duplicate', methods=['POST'])
def check_duplicate():
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    if not field or not value:
        return jsonify({'error': 'Field and value are required'}), 400

    if field not in ['username', 'phone', 'email']:
        return jsonify({'error': 'Invalid field'}), 400

    # Query the database for the field
    user = None
    if field == 'username':
        user = User.query.filter_by(username=value).first()
    elif field == 'phone':
        user = User.query.filter_by(phone=value).first()
    elif field == 'email':
        user = User.query.filter_by(email=value).first()

    return jsonify({'exists': user is not None}), 200

# Signup Route
@main.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    email = data.get('email')

    # Validate required fields
    if not username or not password or not phone or not email:
        return jsonify({'error': 'Username, password, phone, and email are required'}), 400

    # Validate username (no special characters)
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return jsonify({'error': 'Username cannot contain special characters'}), 400

    # Validate phone
    if not validate_phone(phone):
        return jsonify({'error': 'Phone number must be 10 digits'}), 400

    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate password
    if not validate_password(password):
        return jsonify({'error': 'Password must be 8+ characters, with numbers and at least one uppercase letter'}), 400

    # Check for duplicates
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone already taken'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already taken'}), 400

    # Hash the password and create the user
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, phone=phone, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Login Route (unchanged)
@main.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"flag": False, "message": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"flag": True, "message": "Login Successful", "access_token": access_token}), 200

# Protected Route (unchanged)
@main.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify({'message': 'This is a protected endpoint'}), 200

# Tournament Routes (unchanged)
@main.route('/api/tournaments', methods=['POST'])
@jwt_required()
def create_tournament():
    data = request.get_json()
    name = data.get('name')
    start_date = data.get('start_date')
    organizer_id = get_jwt_identity()

    if not name or not start_date:
        return jsonify({'error': 'Missing required fields'}), 400

    tournament = Tournament(name=name, organizer_id=organizer_id, start_date=start_date)
    db.session.add(tournament)
    db.session.commit()

    pusher_client.trigger('tournaments', 'new-tournament', {
        'id': tournament.id,
        'name': tournament.name,
        'start_date': str(tournament.start_date)
    })

    return jsonify({'message': 'Tournament created', 'id': tournament.id}), 201

@main.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    tournaments = Tournament.query.all()
    return jsonify([{'id': t.id, 'name': t.name, 'start_date': str(t.start_date)} for t in tournaments]), 200