from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import logging
from ingestion import process_uploaded_file
from retrieval import get_index, upsert_documents, search_similar_documents, check_index_contents, rerank_chunks
from generator import generate_study_guide, generate_study_guide_from_text
import uuid
from routes.auth import auth_bp
from models import db, User, File, Summary, Quiz
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import sqlite3
import datetime
import json
from typing import Tuple, List
import nltk
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure CORS to allow all routes
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],  # Add more origins as needed
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploaded_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for document chunks
document_chunks = []

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Secret key for JWT
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key in production

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    
    # Create uploaded_files table
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/check-index')
def check_index():
    """Check the contents of the Pinecone index."""
    try:
        check_index_contents()
        return "Index check completed. Check the logs for details."
    except Exception as e:
        return f"Error checking index: {str(e)}"

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            'user_id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            # Generate token
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': 'Failed to login'}), 500

@app.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    try:
    if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            # Save file to database
            new_file = File(
                filename=file.filename,
                user_id=current_user.id
            )
            db.session.add(new_file)
            db.session.commit()

            # Save file to filesystem
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename
            }), 200

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return jsonify({'error': 'Failed to upload file'}), 500

@app.route('/api/files', methods=['GET'])
@token_required
def get_files(current_user):
    try:
        files = File.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'filename': file.filename,
            'upload_date': file.upload_date.isoformat()
        } for file in files]), 200

    except Exception as e:
        print(f"Error fetching files: {str(e)}")
        return jsonify({'error': 'Failed to fetch files'}), 500

@app.route('/generate', methods=['POST'])
@token_required
def generate_summary(current_user):
    try:
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Generate summary using your existing logic
        summary_content = generate_study_guide_from_text(topic)
        
        # Save summary to database
        new_summary = Summary(
            topic=topic,
            content=summary_content,
            user_id=current_user.id
        )
        db.session.add(new_summary)
        db.session.commit()

        return jsonify({
            'message': 'Summary generated successfully',
            'study_guide': summary_content
        }), 200

    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return jsonify({'error': 'Failed to generate summary'}), 500

@app.route('/generate-from-text', methods=['POST'])
@token_required
def generate_from_text(current_user):
    """Generate a study guide from provided text."""
    try:
        data = request.get_json()
        text_chunks = data.get('text_chunks', [])
        topic = data.get('topic', 'General Topic')
        preferences = data.get('preferences', '')
        
        if not text_chunks:
            return jsonify({'error': 'No text provided'}), 400
            
        # Generate study guide
        study_guide = generate_study_guide_from_text(text_chunks, topic, preferences)
        
        if study_guide.startswith('Error'):
            return jsonify({'error': study_guide}), 500
            
        return jsonify({
            'message': 'Summary generated successfully',
            'study_guide': study_guide
        })
        
    except Exception as e:
        logger.error(f"Error generating study guide: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['GET'])
@token_required
def get_file(current_user, filename):
    """Serve an uploaded file."""
    try:
        # Verify the file belongs to the user
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT filename FROM uploaded_files WHERE username = ? AND filename = ?',
                 (current_user['username'], filename))
        file_record = c.fetchone()
        conn.close()
        
        if not file_record:
            return jsonify({'error': 'File not found or access denied'}), 404
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>/content', methods=['GET'])
@token_required
def get_file_content(current_user, filename):
    """Get the content of an uploaded file."""
    try:
        # Verify the file belongs to the user
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT filename FROM uploaded_files WHERE username = ? AND filename = ?',
                 (current_user['username'], filename))
        file_record = c.fetchone()
        conn.close()
        
        if not file_record:
            return jsonify({'error': 'File not found or access denied'}), 404
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Read file content based on file type
        _, ext = os.path.splitext(filename)
        if ext.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif ext.lower() == '.pdf':
            # For PDF files, you might want to use a PDF parsing library
            # This is a simple example that might not work for all PDFs
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                content = ''
                for page in pdf.pages:
                    content += page.extract_text() + '\n'
        elif ext.lower() == '.docx':
            # For DOCX files, you might want to use python-docx
            # This is a simple example that might not work for all DOCX files
            import docx
            doc = docx.Document(file_path)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        return jsonify({
            'content': content,
            'filename': filename
        })
    
    except Exception as e:
        logger.error(f"Error reading file content: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_file_content(filename: str, username: str) -> Tuple[str, List[str]]:
    """
    Retrieve all chunks of a specific file from Pinecone.
    Returns:
        - Combined text
        - List of all noun phrases found in the document (for better distractor generation)
    """
    try:
        # Search for all chunks with the exact filename
        results = search_similar_documents(
            query="",  # Empty query returns all matching documents
            filter={
                'filename': {"$eq": filename},
                'username': {"$eq": username}
            },
            top_k=1000  # Get all chunks for this file
        )
        
        if not results:
            return None, None
            
        # Combine all chunks and extract noun phrases
        combined_text = ' '.join(results)
        noun_phrases = extract_noun_phrases(combined_text)
        
        return combined_text, noun_phrases
        
    except Exception as e:
        logger.error(f"Error retrieving file content: {str(e)}")
        return None, None

def extract_noun_phrases(text: str) -> List[str]:
    """
    Extract noun phrases from text using NLTK.
    """
    try:
        # Tokenize and tag
        tokens = nltk.word_tokenize(text)
        tagged = nltk.pos_tag(tokens)
        
        # Extract noun phrases
        grammar = r"""
            NP: {<DT>?<JJ>*<NN.*>+}  # Noun phrase
                {<NNP>+}              # Proper noun
                {<NNPS>+}             # Proper noun plural
        """
        chunk_parser = nltk.RegexpParser(grammar)
        tree = chunk_parser.parse(tagged)
        
        # Extract phrases
        noun_phrases = []
        for subtree in tree.subtrees(filter=lambda t: t.label() == 'NP'):
            phrase = ' '.join(word for word, tag in subtree.leaves())
            if len(phrase.split()) <= 4:  # Limit to reasonable length
                noun_phrases.append(phrase)
        
        return list(set(noun_phrases))  # Remove duplicates
        
    except Exception as e:
        logger.error(f"Error extracting noun phrases: {str(e)}")
        return []

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    try:
        # Get only summaries for the current user
        summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.created_at.desc()).all()

        # Format summaries for the frontend
        history = [{
            'type': 'summary',
            'topic': summary.topic,
            'content': summary.content,
            'date': summary.created_at.isoformat()
        } for summary in summaries]

        return jsonify(history), 200
    
    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        return jsonify({'error': 'Failed to fetch history'}), 500

@app.route('/api/check-users', methods=['GET'])
def check_users():
    try:
        users = User.query.all()
        user_list = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
        } for user in users]
        return jsonify({
            'count': len(user_list),
            'users': user_list
        }), 200
    except Exception as e:
        print(f"Error checking users: {str(e)}")
        return jsonify({'error': 'Failed to check users'}), 500

if __name__ == '__main__':
    app.run(debug=True) 