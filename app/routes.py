# app/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, pusher_client
from .models import User, Tournament

main = Blueprint('main', __name__)

# Authentication Routes
@main.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'flag': False, 'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

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

@main.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify({'message': 'This is a protected endpoint'}), 200

# Tournament Routes
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