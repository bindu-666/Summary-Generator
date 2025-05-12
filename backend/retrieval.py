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
PINECONE_API_KEY = 'pcsk_3QD2yg_ErC9WPvf686c64wNkqf7hMg8TWjFxS3vXnN2oYEdKtJF3YDFcgrZ2jw88Lbqpuw'  # Your API key
PINECONE_ENVIRONMENT = 'us-east-1'
PINECONE_INDEX_NAME = 'study-guide'  # Consistent index name

# Initialize Pinecone with new API
pc = pinecone.Pinecone(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize the cross-encoder reranker
reranker_tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker_model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")

def get_index():
    """Get or create the Pinecone index."""
    try:
        logger.info("Checking if index exists...")
        existing_indexes = pc.list_indexes().names()
        logger.info(f"Existing indexes: {existing_indexes}")
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            logger.info(f"Creating new index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,  # dimension of the all-MiniLM-L6-v2 model
                metric="cosine",
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info("Index created successfully")
        else:
            logger.info(f"Using existing index: {PINECONE_INDEX_NAME}")
        
        index = pc.Index(PINECONE_INDEX_NAME)
        logger.info("Index retrieved successfully")
        return index
    except Exception as e:
        logger.error(f"Error in get_index: {str(e)}", exc_info=True)
        raise

def upsert_documents(documents):
    """Upsert documents to Pinecone index."""
    try:
        logger.info(f"Starting upsert of {len(documents)} documents")
        index = get_index()
        
        # Prepare vectors for upserting
        vectors = []
        for doc in documents:
            # Generate embedding for the text
            logger.info(f"Generating embedding for document: {doc['id']}")
            embedding = model.encode(doc['text']).tolist()
            
            # Create vector with metadata
            vector = {
                'id': doc['id'],
                'values': embedding,
                'metadata': {
                    **doc.get('metadata', {}),
                    'text': doc['text']  # Store the text in metadata for retrieval
                }
            }
            vectors.append(vector)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            logger.info(f"Upserting batch {i//batch_size + 1} of {(len(vectors) + batch_size - 1)//batch_size}")
            index.upsert(vectors=batch)
        
        logger.info("All documents upserted successfully")
    except Exception as e:
        logger.error(f"Error in upsert_documents: {str(e)}", exc_info=True)
        raise

def search_similar_documents(query, top_k=5, filter=None):
    """Search for similar documents in Pinecone index."""
    try:
        index = get_index()
        
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search with filter if provided
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter  # Add filter parameter
        )
        
        # Extract text from results
        similar_docs = []
        for match in results.matches:
            if 'text' in match.metadata:
                similar_docs.append(match.metadata['text'])
        
        logger.info(f"Found {len(similar_docs)} similar documents")
        return similar_docs
    except Exception as e:
        logger.error(f"Error in search_similar_documents: {str(e)}", exc_info=True)
        raise

def check_index_contents():
    """Check the contents of the Pinecone index."""
    index = get_index()
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")

def rerank_chunks(query, chunks, top_k=5):
    """Rerank chunks based on relevance to the query."""
    # For now, just return the top k chunks
    # In a more sophisticated implementation, you could use a cross-encoder
    return chunks[:top_k] 