import re
from typing import List

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks of specified size.
    
    Args:
        text (str): Input text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            # Add current chunk to chunks
            chunks.append(' '.join(current_chunk))
            
            # Start new chunk with overlap
            overlap_size = 0
            overlap_chunk = []
            for s in reversed(current_chunk):
                if overlap_size + len(s) <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_size += len(s)
                else:
                    break
            
            current_chunk = overlap_chunk
            current_size = overlap_size
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks 