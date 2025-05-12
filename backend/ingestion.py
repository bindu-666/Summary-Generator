import PyPDF2
import docx
import os

def process_uploaded_file(file_path: str) -> str:
    """
    Process an uploaded file and extract its text content.
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        str: Extracted text content
    """
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == '.pdf':
        return process_pdf(file_path)
    elif ext.lower() == '.docx':
        return process_docx(file_path)
    elif ext.lower() == '.txt':
        return process_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

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