import pinecone
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict
import numpy as np
from dotenv import load_dotenv
import logging
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'studyguide-index')

# Initialize the sentence transformer model
model = SentenceTransformer('intfloat/multilingual-e5-large')

# Initialize Pinecone with the provided API key
api_key = 'pcsk_3QD2yg_ErC9WPvf686c64wNkqf7hMg8TWjFxS3vXnN2oYEdKtJF3YDFcgrZ2jw88Lbqpuw'
pc = pinecone.Pinecone(
    api_key=api_key,
    environment=PINECONE_ENVIRONMENT
)

# Initialize the cross-encoder reranker
reranker_tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker_model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")

def get_index(index_name: str = PINECONE_INDEX_NAME):
    """
    Get the Pinecone index.
    
    Args:
        index_name (str): Name of the index to use (defaults to study-guide-index)
        
    Returns:
        pinecone.Index: The index object
    """
    try:
        # Get the index
        return pc.Index(index_name)
    except Exception as e:
        logger.error(f"Error getting index: {str(e)}")
        raise

def upsert_documents(documents: List[Dict[str, str]], index_name: str = PINECONE_INDEX_NAME):
    """
    Add documents to the Pinecone index.
    
    Args:
        documents (List[Dict]): List of documents to add
        index_name (str): Name of the index to add documents to (defaults to study-guide-index)
    """
    try:
        # Get the index
        index = get_index(index_name)
        
        # Convert documents to vectors
        vectors = []
        for doc in documents:
            # Generate embedding
            embedding = model.encode(doc['text'])
            
            
            # Create vector object
            vector = {
                'id': doc['id'],
                'values': embedding.tolist(),
                'metadata': {'text': doc['text']}
            }
            vectors.append(vector)
        print("vector is ",vectors[0])
        # Upsert vectors in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch)
        
        logger.info(f"Successfully added {len(vectors)} documents to index")
        
    except Exception as e:
        logger.error(f"Error upserting documents: {str(e)}")
        raise

def search_similar_documents(query: str, top_k: int = 5, index_name: str = PINECONE_INDEX_NAME) -> List[str]:
    """
    Search for similar documents in the index.
    
    Args:
        query (str): Query text to search for
        top_k (int): Number of results to return
        index_name (str): Name of the index to search in (defaults to study-guide-index)
        
    Returns:
        List[str]: List of similar document texts
    """
    try:
        # Get the index
        index = get_index(index_name)
        
        # Clean and normalize the query
        query = query.strip().lower()
        
        # Check if query is a question
        is_question = query.endswith('?')
        
        # Remove question mark if present
        if is_question:
            query = query[:-1].strip()
        
        # Create enhanced queries with different contexts and phrasings
        enhanced_queries = []
        
        # 1. Definition and Basic Concepts
        enhanced_queries.extend([
            f"What is {query}?",
            f"Define {query}",
            f"Basic concepts of {query}",
            f"Core principles of {query}"
        ])
        
        # 2. Practical Applications
        enhanced_queries.extend([
            f"Examples of {query}",
            f"Use cases of {query}",
            f"Applications of {query}",
            f"Practical implementation of {query}"
        ])
        
        # 3. Advanced Topics
        enhanced_queries.extend([
            f"Advanced concepts in {query}",
            f"Complex aspects of {query}",
            f"Technical details of {query}",
            f"In-depth analysis of {query}"
        ])
        
        # 4. Learning and Understanding
        enhanced_queries.extend([
            f"How to understand {query}",
            f"Key points about {query}",
            f"Important aspects of {query}",
            f"Critical concepts in {query}"
        ])
        
        # 5. Question-based variations (if original was a question)
        if is_question:
            enhanced_queries.extend([
                f"Answer to: {query}",
                f"Explanation of {query}",
                f"Detailed response about {query}",
                f"Comprehensive answer regarding {query}"
            ])
        
        # 6. Original query (if it's not already included)
        if query not in enhanced_queries:
            enhanced_queries.append(query)
        
        logger.info(f"Original query: {query}")
        logger.info(f"Enhanced queries: {enhanced_queries}")
        
        all_matches = []
        for enhanced_query in enhanced_queries:
            # Generate query embedding
            query_embedding = model.encode(enhanced_query)
            
            # Search in Pinecone
            results = index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            # Add matches to our collection
            all_matches.extend(results.matches)
        
        # Sort all matches by score
        all_matches.sort(key=lambda x: x.score, reverse=True)
        
        # Log detailed search results
        logger.info(f"Found {len(all_matches)} total matches")
        logger.info("Detailed match information:")
        for i, match in enumerate(all_matches):
            logger.info(f"\nMatch {i+1}:")
            logger.info(f"Score: {match.score:.4f}")
            logger.info(f"ID: {match.id}")
            logger.info(f"Text preview: {match.metadata['text'][:300]}...")
            logger.info("-" * 50)
        
        # Define confidence levels and thresholds
        confidence_levels = {
            'Very High': (0.5, float('inf')),
            'High': (0.4, 0.5),
            'Medium': (0.3, 0.4),
            'Low': (0.2, 0.3),
            'Very Low': (0.0, 0.2)
        }
        
        # Set minimum similarity score
        min_similarity_score = 0.3  # Minimum score to consider a match
        
        # Log threshold information
        logger.info("\nApplying similarity thresholds:")
        logger.info(f"Minimum similarity score: {min_similarity_score}")
        for level, (min_score, max_score) in confidence_levels.items():
            count = sum(1 for m in all_matches if min_score <= m.score < max_score)
            logger.info(f"{level} confidence ({min_score:.1f}-{max_score:.1f}): {count} matches")
        
        # Filter matches based on minimum similarity score
        filtered_texts = []
        seen_texts = set()  # To avoid duplicates
        
        for match in all_matches:
            text = match.metadata['text']
            if text not in seen_texts and match.score >= min_similarity_score:
                # Determine confidence level
                confidence = next(
                    (level for level, (min_score, max_score) in confidence_levels.items()
                     if min_score <= match.score < max_score),
                    'Unknown'
                )
                
                logger.info(f"\nIncluding match with {confidence} confidence:")
                logger.info(f"Score: {match.score:.4f}")
                logger.info(f"Text preview: {text[:200]}...")
                filtered_texts.append(text)
                seen_texts.add(text)
            else:
                if text not in seen_texts:
                    logger.info(f"\nExcluding low confidence match:")
                    logger.info(f"Score: {match.score:.4f}")
                    logger.info(f"Text preview: {text[:200]}...")
        
        if not filtered_texts:
            logger.warning(f"No matches found above minimum similarity score of {min_similarity_score}")
            return []
            
        logger.info(f"\nFinal results: {len(filtered_texts)} unique matches after filtering")
        return filtered_texts
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise

def check_index_contents(index_name: str = PINECONE_INDEX_NAME):
    """
    Check the contents of the Pinecone index.
    
    Args:
        index_name (str): Name of the index to check
    """
    try:
        # Get the index
        index = get_index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
        
        # Get a sample of vectors
        results = index.query(
            vector=[0.0] * 384,  # Dummy vector
            top_k=5,
            include_metadata=True
        )
        
        logger.info("Sample documents in index:")
        for i, match in enumerate(results.matches):
            logger.info(f"Document {i+1}:")
            logger.info(f"ID: {match.id}")
            logger.info(f"Score: {match.score}")
            logger.info(f"Text: {match.metadata['text'][:200]}...")
            logger.info("="*50)
            
    except Exception as e:
        logger.error(f"Error checking index contents: {str(e)}")
        raise

def rerank_chunks(query: str, chunks: list, top_k: int = 5) -> list:
    """
    Rerank retrieved chunks using a cross-encoder for query relevance.
    Returns the top_k most relevant chunks.
    """
    if not chunks:
        return []
    pairs = [(query, chunk) for chunk in chunks]
    inputs = reranker_tokenizer.batch_encode_plus(
        pairs, padding=True, truncation=True, return_tensors="pt", max_length=256
    )
    with torch.no_grad():
        scores = reranker_model(**inputs).logits.squeeze(-1).cpu().numpy()
    # Sort by score descending
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in ranked[:top_k]] 