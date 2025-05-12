from typing import List

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100, min_chunk_length: int = 100) -> List[str]:
    """
    Split text into smaller, focused chunks with overlap.
    
    Args:
        text (str): Text to split into chunks
        chunk_size (int): Target size of each chunk in characters (reduced for more focused chunks)
        overlap (int): Number of characters to overlap between chunks
        min_chunk_length (int): Minimum length for a chunk to be included
        
    Returns:
        List[str]: List of text chunks
    """
    chunks = []
    current_chunk = []
    current_size = 0
    sentences_per_chunk = 3  # Maximum number of sentences per chunk
    
    # Split text into sentences first to avoid cutting mid-sentence
    sentences = text.split('. ')
    
    for sentence in sentences:
        # Add period back to sentence
        sentence = sentence.strip() + '. '
        
        # If adding this sentence would exceed the chunk size or sentence limit
        if (current_size + len(sentence) > chunk_size) or (len(current_chunk) >= sentences_per_chunk):
            # If we have content in the current chunk, save it
            if current_chunk:
                chunk_text = ''.join(current_chunk)
                # Only add chunk if it meets minimum length requirement
                if len(chunk_text) >= min_chunk_length:
                    chunks.append(chunk_text)
                    
                    # Keep the last part for overlap
                    overlap_start = max(0, len(chunk_text) - overlap)
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
    
    # Log sample chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        logger.info(f"\nChunk {i+1} (length: {len(chunk)}):")
        logger.info(f"Start: {chunk[:100]}...")
        logger.info(f"End: ...{chunk[-100:]}")
    
    return chunks 