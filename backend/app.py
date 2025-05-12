from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import logging
from ingestion import process_uploaded_file
from retrieval import get_index, upsert_documents, search_similar_documents, check_index_contents, rerank_chunks
from generator import generate_study_guide
import uuid
from routes.auth import auth_bp
from models import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import sqlite3
import datetime

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

# Configure CORS to allow all routes
CORS(app, resources={
    r"/*": {  # This will match all routes
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploaded_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for document chunks
document_chunks = []

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_guide.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key

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
def generate_guide(current_user):
    """
    Generate a study guide based on the provided topic.
    """
    logger.info("Received generate guide request")
    
    # Get topic from JSON data
    data = request.get_json()
    topic = data.get('topic') if data else None
    
    if not topic:
        logger.error("No topic provided")
        return jsonify({'error': 'No topic provided'}), 400
    
    logger.info(f"Generating guide for topic: {topic}")
    
    try:
        # Search for relevant documents with user filter
        relevant_chunks = search_similar_documents(
            topic, 
            top_k=10,
            filter={'username': current_user['username']}  # Changed from user_id to username to match metadata
        )
        logger.info(f"Found {len(relevant_chunks)} relevant chunks before reranking")
        
        if not relevant_chunks:
            logger.warning("No relevant documents found")
            return jsonify({
                'error': 'No relevant content found for this topic. Please try a different topic or upload more study materials.'
            }), 404
        
        # Rerank the chunks for query-specific relevance
        reranked_chunks = rerank_chunks(topic, relevant_chunks, top_k=5)
        logger.info(f"Top {len(reranked_chunks)} chunks after reranking")
        
        # Log each reranked chunk
        for i, chunk in enumerate(reranked_chunks):
            logger.info(f"Reranked chunk {i+1}:\n{chunk}\n{'='*50}")
        
        # Combine reranked chunks into a single text
        input_text = "\n".join(reranked_chunks)
        logger.info(f"Input text length for generator: {len(input_text)}")
        logger.info(f"Input text content:\n{input_text}\n{'='*50}")
        
        # Generate study guide using the new text2text-generation approach
        study_guide = generate_study_guide(topic, input_text)
        logger.info(f"Generated study guide length: {len(study_guide)}")
        
        if not study_guide:
            logger.error("Generated study guide is empty")
            return jsonify({'error': 'Failed to generate study guide. Please try again.'}), 500
        
        return jsonify({'study_guide': study_guide})
    
    except Exception as e:
        logger.error(f"Error generating guide: {str(e)}", exc_info=True)
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

if __name__ == '__main__':
    app.run(debug=True) 