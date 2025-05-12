import PyPDF2
import docx
import os
import re
import nltk
from nltk.tokenize import sent_tokenize

# Set NLTK data path
nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

def chunk_text(text: str, max_chunk_size: int = 1000) -> list:
    """
    Split text into chunks of complete sentences.
    
    Args:
        text (str): Input text to chunk
        max_chunk_size (int): Maximum size of each chunk
        
    Returns:
        list: List of text chunks
    """
    # Clean the text
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    # Split into sentences using NLTK's sent_tokenize
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        # If punkt_tab is not found, download it
        print("Downloading NLTK punkt_tab data...")
        nltk.download('punkt_tab', download_dir=os.path.join(os.path.dirname(__file__), 'nltk_data'))
        sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:  # Skip empty sentences
            continue
            
        sentence_size = len(sentence)
        
        # If adding this sentence would exceed the max size, save current chunk and start new one
        if current_size + sentence_size > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def process_uploaded_file(file_path: str) -> list:
    """
    Process an uploaded file and extract its text content in chunks.
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        list: List of text chunks
    """
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == '.pdf':
        text = process_pdf(file_path)
    elif ext.lower() == '.docx':
        text = process_docx(file_path)
    elif ext.lower() == '.txt':
        text = process_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    return chunk_text(text)

def process_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def process_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file.
    
    Args:
        file_path (str): Path to the DOCX file
        
    Returns:
        str: Extracted text
    """
    doc = docx.Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def process_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    
    Args:
        file_path (str): Path to the TXT file
        
    Returns:
        str: Extracted text
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read() 