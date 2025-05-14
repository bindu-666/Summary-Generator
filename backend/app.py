from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import logging
from ingestion import process_uploaded_file
from retrieval import get_index, upsert_documents, search_similar_documents, check_index_contents, rerank_chunks
from generator import generate_study_guide, generate_study_guide_from_text
import uuid
from routes.auth import auth_bp
from models import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import sqlite3
import datetime
import json
from typing import Tuple, List
import nltk

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_guide.db'
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
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except:
            return jsonify({'error': 'Token is invalid'}), 401
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

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                 (username, email, hashed_password))
        conn.commit()
        conn.close()
        
        # Generate token
        token = jwt.encode({
            'username': username,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'message': 'User created successfully',
            'token': token
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not all(k in data for k in ('email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    email = data['email']
    password = data['password']
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            token = jwt.encode({
                'username': user[1],
                'email': user[2],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'message': 'Login successful',
                'token': token
            })
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """
    Handle file upload and process the content.
    """
    logger.info("Received file upload request")
    
    if 'file' not in request.files:
        logger.error("No file provided in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save the file
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        logger.info(f"File saved to {file_path}")
        
        # Process the file and get chunks
        chunks = process_uploaded_file(file_path)
        logger.info(f"File processed into {len(chunks)} chunks")
        
        # Prepare documents for Pinecone
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{filename}_{i}"
            documents.append({
                'id': doc_id,
                'text': chunk,
                'metadata': {
                    'filename': filename,
                    'chunk_index': i,
                    'username': current_user['username']
                }
            })
        
        # Upsert to Pinecone
        upsert_documents(documents)
        logger.info(f"Successfully upserted {len(documents)} chunks to Pinecone")
        
        # Save file info to database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO uploaded_files (username, filename) VALUES (?, ?)',
                 (current_user['username'], filename))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'chunks': len(chunks)
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
@token_required
def get_user_files(current_user):
    """Get list of files uploaded by the user."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT filename, upload_date FROM uploaded_files WHERE username = ? ORDER BY upload_date DESC',
                 (current_user['username'],))
        files = c.fetchall()
        conn.close()
        
        return jsonify({
            'files': [{'filename': f[0], 'upload_date': f[1]} for f in files]
        })
    except Exception as e:
        logger.error(f"Error getting user files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
@token_required
def generate(current_user):
    """Generate a study guide from uploaded documents."""
    try:
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'No topic provided'}), 400
            
        # Get user's uploaded files
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT filename FROM uploaded_files WHERE username = ?', (current_user['username'],))
        files = c.fetchall()
        conn.close()
        
        if not files:
            return jsonify({'error': 'No files uploaded yet'}), 400
            
        # Get content from all files
        all_chunks = []
        for file in files:
            filename = file[0]
            content, _ = get_file_content(filename, current_user['username'])
            if content:
                all_chunks.append(content)
            
        if not all_chunks:
            return jsonify({'error': 'No content found in files'}), 400
            
        # Generate study guide
        study_guide = generate_study_guide(topic, ' '.join(all_chunks))
        
        if study_guide.startswith('Error'):
            return jsonify({'error': study_guide}), 500
            
        return jsonify({
            'message': 'Summary generated successfully',
            'study_guide': study_guide
        })
        
    except Exception as e:
        logger.error(f"Error generating study guide: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(debug=True) 