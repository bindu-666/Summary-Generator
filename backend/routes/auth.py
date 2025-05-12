from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from models import db, User
from functools import wraps
import logging
import sqlite3

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
            return jsonify({'error': 'No data provided'}), 400
        
        # Check for required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # Validate input
        if not username.strip():
            return jsonify({'error': 'Username cannot be empty'}), 400
        if not email.strip():
            return jsonify({'error': 'Email cannot be empty'}), 400
        if not password:
            return jsonify({'error': 'Password cannot be empty'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Connect to database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        try:
            # Check if username or email already exists
            c.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
            existing_user = c.fetchone()
            if existing_user:
                return jsonify({'error': 'Username or email already exists'}), 400
            
            # Insert new user
            c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
            conn.commit()
            
            # Generate token
            token = jwt.encode({
                'username': username,
                'email': email,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, 'your-secret-key')  # Use the same secret key as in app.py
            
            return jsonify({
                'message': 'User created successfully',
                'token': token
            }), 201
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Username or email already exists'}), 400
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email']
        password = data['password']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            token = jwt.encode({
                'username': user[1],
                'email': user[2],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, 'your-secret-key')  # Use the same secret key as in app.py
            
            return jsonify({
                'message': 'Login successful',
                'token': token
            })
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'error': str(e)}), 500 