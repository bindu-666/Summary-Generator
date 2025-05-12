from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
from ingestion import process_uploaded_file
from retrieval import get_index, upsert_documents, search_similar_documents, check_index_contents, rerank_chunks
from generator import generate_study_guide
import uuid
from routes.auth import auth_bp
from models import db

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

@app.route('/upload', methods=['POST'])
def upload_file():
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
    
    # Check file extension
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ['.pdf', '.docx', '.txt']:
        logger.error(f"Unsupported file type: {ext}")
        return jsonify({'error': 'Unsupported file type. Please upload PDF, DOCX, or TXT files.'}), 400
    
    try:
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        logger.info(f"File saved at: {file_path}")
        
        # Process the file
        text = process_uploaded_file(file_path)
        logger.info(f"Processed file content length: {len(text)}")
        
        # Create document chunks using fixed-size chunks with overlap
        chunks = []
        chunk_size = 500  # Target chunk size in characters
        overlap_size = 100  # Overlap size in characters
        min_chunk_length = 100  # Minimum chunk length to avoid junk
        
        # Split text into sentences first to avoid cutting mid-sentence
        sentences = text.split('. ')
        current_chunk = []
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            # Add period back to sentence
            sentence = sentence.strip() + '. '
            
            # If adding this sentence would exceed the chunk size
            if current_size + len(sentence) > chunk_size:
                # If we have content in the current chunk, save it
                if current_chunk:
                    chunk_text = ''.join(current_chunk)
                    # Only add chunk if it meets minimum length requirement
                    if len(chunk_text) >= min_chunk_length:
                        chunks.append(chunk_text)
                        
                        # Keep the last part for overlap
                        overlap_start = max(0, len(chunk_text) - overlap_size)
                        current_chunk = [chunk_text[overlap_start:]]
                        current_size = len(current_chunk[0])
                    else:
                        logger.info(f"Skipping short chunk (length: {len(chunk_text)})")
                        current_chunk = []
                        current_size = 0
                else:
                    # If the sentence itself is too long, split it
                    if len(sentence) > chunk_size:
                        # Split into smaller parts
                        parts = [sentence[i:i+chunk_size] for i in range(0, len(sentence), chunk_size)]
                        for part in parts:
                            if len(part) >= min_chunk_length:
                                chunks.append(part)
                            else:
                                logger.info(f"Skipping short part (length: {len(part)})")
                        current_chunk = []
                        current_size = 0
                    else:
                        current_chunk = [sentence]
                        current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)
        
        # Add the last chunk if it exists and meets minimum length
        if current_chunk:
            chunk_text = ''.join(current_chunk)
            if len(chunk_text) >= min_chunk_length:
                chunks.append(chunk_text)
            else:
                logger.info(f"Skipping final short chunk (length: {len(chunk_text)})")
        
        # Log chunk statistics
        logger.info(f"Created {len(chunks)} chunks")
        total_chars = sum(len(chunk) for chunk in chunks)
        avg_chunk_size = total_chars / len(chunks) if chunks else 0
        logger.info(f"Average chunk size: {avg_chunk_size:.2f} characters")
        logger.info(f"Total characters in chunks: {total_chars}")
        
        # Prepare documents for indexing
        documents = [{'id': str(uuid.uuid4()), 'text': chunk} for chunk in chunks]
        
        # Get the index
        get_index()
        
        # Upsert documents to Pinecone
        upsert_documents(documents)
        logger.info("Documents upserted to Pinecone")
        
        return jsonify({'message': 'File uploaded and processed successfully'})
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_guide():
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
        # Search for relevant documents
        relevant_chunks = search_similar_documents(topic, top_k=10)  # Retrieve more for reranking
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

if __name__ == '__main__':
    app.run(debug=True) 