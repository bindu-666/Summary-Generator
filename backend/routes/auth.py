from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from models import db, User
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        logger.debug(f"Received signup data: {data}")
        
        if not data:
            logger.error("No data received in request")
            return jsonify({'message': 'No data provided'}), 400
        
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            logger.error(f"Email already exists: {data['email']}")
            return jsonify({'message': 'Email already exists'}), 400
        
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            name=data['name'],
            email=data['email'],
            password=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User created successfully: {data['email']}")
        
        token = jwt.encode({
            'user_id': new_user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, 'your-secret-key')
        
        return jsonify({
            'message': 'User created successfully',
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'message': 'An error occurred during signup',
            'error': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.debug(f"Received login data: {data}")
        
        if not data:
            logger.error("No data received in request")
            return jsonify({'message': 'No data provided'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password, data['password']):
            logger.error(f"Invalid login attempt for email: {data['email']}")
            return jsonify({'message': 'Invalid email or password'}), 401
        
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, 'your-secret-key')
        
        logger.info(f"User logged in successfully: {data['email']}")
        return jsonify({
            'message': 'Login successful',
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        return jsonify({
            'message': 'An error occurred during login',
            'error': str(e)
        }), 500 