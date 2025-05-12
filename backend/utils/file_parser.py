import PyPDF2
import docx
import os

def parse_file(file_path, file_extension):
    """
    Parse different types of files and extract text content.
    
    Args:
        file_path (str): Path to the file
        file_extension (str): File extension (e.g., '.pdf', '.docx')
        
    Returns:
        str: Extracted text content
    """
    if file_extension == '.pdf':
        return parse_pdf(file_path)
    elif file_extension == '.docx':
        return parse_docx(file_path)
    else:
        raise ValueError(f'Unsupported file type: {file_extension}')

def parse_pdf(file_path):
    """Extract text from PDF files."""
    text = ''
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + '\n'
    return text

def parse_docx(file_path):
    """Extract text from DOCX files."""
    doc = docx.Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text 