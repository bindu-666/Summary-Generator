from transformers import pipeline
import torch
from typing import List
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize the text2text-generation pipeline
try:
    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        device=0 if torch.cuda.is_available() else -1
    )
    logger.info("Successfully loaded text2text-generation model")
except Exception as e:
    logger.error(f"Error loading text2text-generation model: {str(e)}")
    raise

def clean_and_deduplicate_text(text: str) -> str:
    """
    Clean text by removing repetitions and improving sentence structure.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text
    """
    try:
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return text

        # Remove duplicate sentences
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            # Normalize sentence for comparison
            normalized = ' '.join(sentence.lower().split())
            if normalized not in seen:
                seen.add(normalized)
                unique_sentences.append(sentence)

        # Remove redundant phrases within sentences
        cleaned_sentences = []
        for sentence in unique_sentences:
            # Split into words
            words = sentence.split()
            cleaned_words = []
            prev_phrase = None
            
            # Check for repeated phrases (3+ words)
            for i in range(len(words)):
                # Look for phrases of 3-5 words
                for phrase_len in range(3, 6):
                    if i + phrase_len <= len(words):
                        current_phrase = ' '.join(words[i:i + phrase_len])
                        if current_phrase == prev_phrase:
                            # Skip this phrase
                            continue
                        prev_phrase = current_phrase
                cleaned_words.append(words[i])
            
            cleaned_sentence = ' '.join(cleaned_words)
            cleaned_sentences.append(cleaned_sentence)

        # Join sentences with proper spacing
        cleaned_text = '. '.join(cleaned_sentences) + '.'
        
        # Fix common issues
        cleaned_text = cleaned_text.replace('..', '.')  # Fix double periods
        cleaned_text = cleaned_text.replace(' .', '.')  # Fix space before period
        cleaned_text = cleaned_text.replace('  ', ' ')  # Fix double spaces
        
        return cleaned_text

    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        return text

def format_summary_for_display(text: str) -> str:
    """
    Format the summary for better display in the UI.
    
    Args:
        text (str): Raw summary text
        
    Returns:
        str: Formatted summary text
    """
    try:
        if not text:
            return text

        # Fix capitalization
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        formatted_sentences = []
        
        for sentence in sentences:
            # Capitalize first letter
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
            
            # Fix common capitalization issues
            sentence = sentence.replace(' i ', ' I ')
            sentence = sentence.replace(' i\'', ' I\'')
            
            # Fix specific terms (like "Himalayas")
            sentence = sentence.replace('himalayas', 'Himalayas')
            sentence = sentence.replace('Himalayans', 'Himalayas')
            
            formatted_sentences.append(sentence)

        # Join sentences with proper spacing
        formatted_text = '. '.join(formatted_sentences) + '.'
        
        # Fix common formatting issues
        formatted_text = formatted_text.replace('..', '.')  # Fix double periods
        formatted_text = formatted_text.replace(' .', '.')  # Fix space before period
        formatted_text = formatted_text.replace('  ', ' ')  # Fix double spaces
        formatted_text = formatted_text.replace(' ,', ',')  # Fix space before comma
        formatted_text = formatted_text.replace(',,', ',')  # Fix double commas
        
        # Ensure proper spacing after punctuation
        for punct in ['.', ',', '!', '?']:
            formatted_text = formatted_text.replace(f'{punct}', f'{punct} ')
        
        # Remove extra spaces
        formatted_text = ' '.join(formatted_text.split())
        
        return formatted_text

    except Exception as e:
        logger.error(f"Error formatting summary: {str(e)}")
        return text

def generate_study_guide(topic: str, input_text: str) -> str:
    """
    Generate a concise and informative study guide using a text2text-generation model.
    
    Args:
        topic (str): The topic for the study guide
        input_text (str): The context to use for generation
        
    Returns:
        str: The generated study guide
    """
    try:
        # Clean and deduplicate input text
        cleaned_text = clean_and_deduplicate_text(input_text)
        logger.info(f"Cleaned text length: {len(cleaned_text)}")

        # Pre-process the input text to ensure topic relevance
        relevant_text = select_relevant_content(cleaned_text, topic)
        logger.info(f"Selected relevant content length: {len(relevant_text)}")

        # Truncate input text if it's too long, preserving topic context
        max_tokens = 800  # Increased from 400 to allow more context
        truncated_text = truncate_text_with_context(relevant_text, topic, max_tokens)
        logger.info(f"Input text truncated from {len(relevant_text)} to {len(truncated_text)} characters")

        # Create a more focused prompt
        prompt = f"""Write a clear and concise summary about the topic '{topic}' using ONLY the information provided in the context below.
Follow these instructions strictly:
1. Use ONLY the information from the provided context - do not add external knowledge.
2. Focus on the main topic and its key aspects mentioned in the context.
3. Write a single, well-structured paragraph that flows naturally.
4. Maintain the original meaning and emphasis from the context.
5. If the context doesn't contain enough information about a specific aspect, do not make assumptions.

        Context:
{truncated_text}
        """
        
        logger.info(f"Generating summary for topic: {topic}")
        logger.info(f"Input text length: {len(truncated_text)}")
        
        # Use deterministic generation with appropriate parameters
        result = generator(
            prompt,
            max_length=512,  # Model's maximum sequence length
            min_length=100,
            num_beams=5,
            do_sample=False,  # Deterministic generation
            repetition_penalty=1.5,
            length_penalty=1.0,
            no_repeat_ngram_size=3
        )
        
        generated_text = result[0]['generated_text']
        logger.info(f"Generated summary length: {len(generated_text)}")
        logger.info(f"Generated content preview: {generated_text[:200]}...")
        
        # Clean the generated text
        generated_text = clean_and_deduplicate_text(generated_text)
        
        # Format the text for display
        generated_text = format_summary_for_display(generated_text)

        # Add a disclaimer if the generated text is too short
        if len(generated_text.split()) < 50:
            generated_text += "\n\nNote: The provided context may not contain enough information for a comprehensive summary."
        
        return generated_text
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return f"Error generating summary: {str(e)}"

def select_relevant_content(text: str, topic: str) -> str:
    """
    Select content most relevant to the given topic.
    
    Args:
        text (str): Input text to analyze
        topic (str): Topic to focus on
        
    Returns:
        str: Selected relevant content
    """
    try:
        # Split text into sentences
        sentences = text.split('. ')
        
        # Score sentences based on topic relevance
        scored_sentences = []
        topic_words = set(topic.lower().split())
        
        # Calculate topic relevance scores
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Calculate word overlap score
            sentence_words = set(sentence.lower().split())
            common_words = topic_words.intersection(sentence_words)
            word_score = len(common_words) / len(topic_words) if topic_words else 0
            
            # Calculate semantic similarity using token overlap
            topic_tokens = set(generator.tokenizer.encode(topic))
            sentence_tokens = set(generator.tokenizer.encode(sentence))
            token_overlap = len(topic_tokens.intersection(sentence_tokens)) / len(topic_tokens)
            
            # Calculate context score (how well it fits with other relevant sentences)
            context_score = 0
            if scored_sentences:
                prev_sentence = scored_sentences[-1][0]
                prev_tokens = set(generator.tokenizer.encode(prev_sentence))
                context_score = len(sentence_tokens.intersection(prev_tokens)) / len(sentence_tokens)
            
            # Combine scores with weights
            final_score = (word_score * 0.5) + (token_overlap * 0.3) + (context_score * 0.2)
            scored_sentences.append((sentence, final_score))
        
        # Sort by relevance score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select top relevant sentences while maintaining context
        selected_sentences = []
        min_score = 0.1  # Lower threshold to include more context
        
        # First, add sentences above threshold
        for sentence, score in scored_sentences:
            if score >= min_score:
                selected_sentences.append(sentence)
        
        # If we have too few sentences, add more context
        if len(selected_sentences) < 3:
            # Add sentences that provide context to the selected ones
            for sentence, _ in scored_sentences:
                if sentence not in selected_sentences:
                    selected_sentences.append(sentence)
                if len(selected_sentences) >= 5:  # Ensure we have enough context
                    break
        
        # Sort selected sentences by their original order
        original_sentences = [s.strip() for s in text.split('.') if s.strip()]
        selected_sentences = [s for s in original_sentences if s in selected_sentences]
        
        return '. '.join(selected_sentences) + '.'
        
    except Exception as e:
        logger.error(f"Error selecting relevant content: {str(e)}")
        return text

def truncate_text_with_context(text: str, topic: str, max_tokens: int) -> str:
    """
    Truncate text while preserving topic context and sentence boundaries.
    
    Args:
        text (str): Input text to truncate
        topic (str): Topic to preserve context for
        max_tokens (int): Maximum number of tokens allowed
        
    Returns:
        str: Truncated text with preserved context
    """
    try:
        # Split text into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return text

        # Find topic-relevant sentences
        topic_sentences = []
        other_sentences = []
        
        for sentence in sentences:
            # Check if sentence contains topic
            if topic.lower() in sentence.lower():
                topic_sentences.append(sentence)
            else:
                other_sentences.append(sentence)

        # If no topic sentences found, use first few sentences
        if not topic_sentences:
            selected_sentences = sentences[:5]  # Increased from 3 to 5 sentences
        else:
            # Start with topic sentences
            selected_sentences = topic_sentences.copy()
            
            # Add context sentences before and after topic sentences
            for topic_sentence in topic_sentences:
                topic_idx = sentences.index(topic_sentence)
                
                # Add 2-3 sentences before (increased from 1-2)
                for i in range(max(0, topic_idx - 3), topic_idx):
                    if sentences[i] not in selected_sentences:
                        selected_sentences.insert(0, sentences[i])
                
                # Add 2-3 sentences after (increased from 1-2)
                for i in range(topic_idx + 1, min(len(sentences), topic_idx + 4)):
                    if sentences[i] not in selected_sentences:
                        selected_sentences.append(sentences[i])

        # Join sentences and check token length
        truncated_text = '. '.join(selected_sentences) + '.'
        tokens = generator.tokenizer.encode(truncated_text)
        
        # If still too long, remove sentences from the end while preserving topic sentences
        while len(tokens) > max_tokens and len(selected_sentences) > len(topic_sentences):
            # Remove the last non-topic sentence
            for i in range(len(selected_sentences) - 1, -1, -1):
                if selected_sentences[i] not in topic_sentences:
                    selected_sentences.pop(i)
                    break
            truncated_text = '. '.join(selected_sentences) + '.'
            tokens = generator.tokenizer.encode(truncated_text)
        
        # If still too long, remove sentences from the beginning while preserving topic sentences
        while len(tokens) > max_tokens and len(selected_sentences) > len(topic_sentences):
            # Remove the first non-topic sentence
            for i in range(len(selected_sentences)):
                if selected_sentences[i] not in topic_sentences:
                    selected_sentences.pop(i)
                    break
            truncated_text = '. '.join(selected_sentences) + '.'
            tokens = generator.tokenizer.encode(truncated_text)
        
        # If still too long, truncate at token level but try to end at a sentence boundary
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            truncated_text = generator.tokenizer.decode(truncated_tokens)
            # Find last complete sentence
            last_period = truncated_text.rfind('.')
            if last_period > 0:
                truncated_text = truncated_text[:last_period + 1]
            else:
                # Find last complete word
                last_space = truncated_text.rfind(' ')
                if last_space > 0:
                    truncated_text = truncated_text[:last_space] + '...'
                else:
                    truncated_text += '...'
        
        return truncated_text
        
    except Exception as e:
        logger.error(f"Error truncating text with context: {str(e)}")
        # Fallback: simple character-based truncation
        return text[:max_tokens * 4] + "..."  # Rough estimate: 4 chars per token

def generate_study_guide_from_text(text_chunks: List[str], topic: str = "", preferences: str = "") -> str:
    """
    Generate a study guide from provided text chunks.
    
    Args:
        text_chunks (list): List of text chunks to process
        topic (str): Topic to guide the generation
        preferences (str): User preferences for the guide
        
    Returns:
        str: Generated study guide
    """
    logger.info(f"Generating study guide from {len(text_chunks)} chunks")
    
    try:
        # Validate input
        if not text_chunks:
            return "Error: No text chunks provided for study guide generation."
        if not topic:
            return "Error: No topic provided for study guide generation."

        # First stage: Initial ranking of chunks
        initial_ranked_chunks = rank_chunks(text_chunks, topic)
        logger.info(f"Initial ranking completed for {len(initial_ranked_chunks)} chunks")

        # Second stage: Rerank top chunks with more detailed analysis
        top_chunks = [chunk for chunk, _ in initial_ranked_chunks[:10]]  # Take top 10 for reranking
        reranked_chunks = rerank_chunks(top_chunks, topic)
        logger.info(f"Reranking completed for {len(reranked_chunks)} chunks")

        # Extract and modify relevant sentences from reranked chunks
        relevant_sentences = []
        for chunk, _ in reranked_chunks:
            sentences = [s.strip() for s in chunk.split('.') if s.strip()]
            for sentence in sentences:
                if is_relevant_to_topic(sentence, topic):
                    modified_sentence = modify_sentence_for_clarity(sentence, topic)
                    if modified_sentence:
                        relevant_sentences.append(modified_sentence)

        if not relevant_sentences:
            return "Error: No relevant content found for the given topic."

        # Combine sentences into a coherent text
        combined_text = ' '.join(relevant_sentences)
        logger.debug(f"Combined text length: {len(combined_text)}")
        
        # Add preferences if provided
        if preferences:
            combined_text = f"Additional Requirements:\n{preferences}\n\nContext:\n{combined_text}"
        
        # Generate the study guide
        return generate_study_guide(topic, combined_text)

    except Exception as e:
        logger.error(f"Error generating study guide from text: {str(e)}", exc_info=True)
        return f"Error generating study guide from text: {str(e)}"

def rank_chunks(chunks: List[str], topic: str) -> List[tuple]:
    """
    First stage ranking of chunks based on basic relevance metrics.
    
    Args:
        chunks (List[str]): List of text chunks to rank
        topic (str): Topic to rank against
        
    Returns:
        List[tuple]: List of (chunk, score) tuples sorted by score
    """
    try:
        ranked_chunks = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # Basic relevance score
            relevance_score = calculate_chunk_relevance(chunk, topic)
            
            # Topic mention bonus
            topic_mention_bonus = 0.2 if topic.lower() in chunk.lower() else 0
            
            # Length penalty (prefer chunks of moderate length)
            words = chunk.split()
            length_penalty = 0
            if len(words) < 10:
                length_penalty = 0.1  # Penalize very short chunks
            elif len(words) > 100:
                length_penalty = 0.1  # Penalize very long chunks
                
            # Calculate final score
            final_score = relevance_score + topic_mention_bonus - length_penalty
            ranked_chunks.append((chunk, final_score))
            
        # Sort by score
        ranked_chunks.sort(key=lambda x: x[1], reverse=True)
        return ranked_chunks
        
    except Exception as e:
        logger.error(f"Error in initial chunk ranking: {str(e)}")
        return [(chunk, 0.0) for chunk in chunks]

def rerank_chunks(chunks: List[str], topic: str) -> List[tuple]:
    """
    Second stage ranking with more detailed analysis of chunks.
    
    Args:
        chunks (List[str]): List of text chunks to rerank
        topic (str): Topic to rank against
        
    Returns:
        List[tuple]: List of (chunk, score) tuples sorted by score
    """
    try:
        reranked_chunks = []
        topic_words = set(topic.lower().split())
        
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # Calculate detailed metrics
            sentences = [s.strip() for s in chunk.split('.') if s.strip()]
            
            # Topic coverage (how many sentences mention the topic)
            topic_sentences = sum(1 for s in sentences if topic.lower() in s.lower())
            topic_coverage = topic_sentences / len(sentences) if sentences else 0
            
            # Semantic coherence
            coherence_score = calculate_semantic_coherence(sentences)
            
            # Information density
            info_density = calculate_information_density(chunk, topic_words)
            
            # Combine scores with weights
            final_score = (
                topic_coverage * 0.4 +     # Topic coverage
                coherence_score * 0.3 +    # Semantic coherence
                info_density * 0.3         # Information density
            )
            
            reranked_chunks.append((chunk, final_score))
            
        # Sort by score
        reranked_chunks.sort(key=lambda x: x[1], reverse=True)
        return reranked_chunks
        
    except Exception as e:
        logger.error(f"Error in chunk reranking: {str(e)}")
        return [(chunk, 0.0) for chunk in chunks]

def calculate_semantic_coherence(sentences: List[str]) -> float:
    """
    Calculate semantic coherence between sentences in a chunk.
    
    Args:
        sentences (List[str]): List of sentences to analyze
        
    Returns:
        float: Coherence score between 0 and 1
    """
    try:
        if len(sentences) < 2:
            return 1.0  # Single sentence is considered coherent
            
        total_overlap = 0
        comparisons = 0
        
        for i in range(len(sentences) - 1):
            current_tokens = set(generator.tokenizer.encode(sentences[i]))
            next_tokens = set(generator.tokenizer.encode(sentences[i + 1]))
            
            # Calculate token overlap
            overlap = len(current_tokens.intersection(next_tokens)) / len(current_tokens)
            total_overlap += overlap
            comparisons += 1
            
        return total_overlap / comparisons if comparisons > 0 else 0
        
    except Exception as e:
        logger.error(f"Error calculating semantic coherence: {str(e)}")
        return 0.0

def calculate_information_density(chunk: str, topic_words: set) -> float:
    """
    Calculate information density of a chunk relative to the topic.
    
    Args:
        chunk (str): Text chunk to analyze
        topic_words (set): Set of topic-related words
        
    Returns:
        float: Information density score between 0 and 1
    """
    try:
        words = chunk.lower().split()
        if not words:
            return 0.0
            
        # Count topic-related words
        topic_word_count = sum(1 for word in words if word in topic_words)
        
        # Count unique words
        unique_words = len(set(words))
        
        # Calculate density scores
        topic_density = topic_word_count / len(words)
        uniqueness = unique_words / len(words)
        
        # Combine scores
        return (topic_density * 0.7) + (uniqueness * 0.3)
        
    except Exception as e:
        logger.error(f"Error calculating information density: {str(e)}")
        return 0.0

def is_relevant_to_topic(sentence: str, topic: str) -> bool:
    """
    Check if a sentence is relevant to the topic.
    
    Args:
        sentence (str): Sentence to check
        topic (str): Topic to check against
        
    Returns:
        bool: True if sentence is relevant to topic
    """
    try:
        if not sentence.strip() or not topic.strip():
            return False
            
        # Check for direct topic mention
        if topic.lower() in sentence.lower():
            return True
            
        # Check for semantic relevance
        topic_tokens = set(generator.tokenizer.encode(topic))
        sentence_tokens = set(generator.tokenizer.encode(sentence))
        token_overlap = len(topic_tokens.intersection(sentence_tokens)) / len(topic_tokens)
        
        # Check for related terms
        topic_words = set(topic.lower().split())
        sentence_words = set(sentence.lower().split())
        common_words = topic_words.intersection(sentence_words)
        
        # Consider relevant if either condition is met
        return token_overlap > 0.3 or len(common_words) > 0
        
    except Exception as e:
        logger.error(f"Error checking sentence relevance: {str(e)}")
        return False

def modify_sentence_for_clarity(sentence: str, topic: str) -> str:
    """
    Modify a sentence to make it clearer and more focused on the topic.
    
    Args:
        sentence (str): Original sentence
        topic (str): Topic to focus on
        
    Returns:
        str: Modified sentence
    """
    try:
        if not sentence.strip():
            return ""
            
        # Create a prompt for sentence modification
        prompt = f"""Modify the following sentence to be clearer and more focused on the topic '{topic}'.
Keep the original meaning but make it more concise and direct.
Only use information present in the original sentence.

Original sentence: {sentence}

Modified sentence:"""

        # Generate modified sentence
        result = generator(
            prompt,
            max_length=100,
            min_length=10,
            num_beams=4,
            do_sample=False,
            repetition_penalty=1.2
        )
        
        modified = result[0]['generated_text'].strip()
        
        # Ensure the modified sentence is not too different from original
        if len(modified.split()) < len(sentence.split()) * 0.5:
            return sentence  # Return original if too much was removed
            
        return modified
        
    except Exception as e:
        logger.error(f"Error modifying sentence: {str(e)}")
        return sentence  # Return original sentence on error

def calculate_chunk_relevance(chunk: str, topic: str) -> float:
    """
    Calculate how relevant a chunk is to the given topic.
    
    Args:
        chunk (str): Text chunk to evaluate
        topic (str): Topic to check relevance against
        
    Returns:
        float: Relevance score between 0 and 1
    """
    try:
        if not chunk.strip() or not topic.strip():
            return 0.0
            
        # Calculate word overlap score
        topic_words = set(topic.lower().split())
        chunk_words = set(chunk.lower().split())
        common_words = topic_words.intersection(chunk_words)
        word_score = len(common_words) / len(topic_words) if topic_words else 0
        
        # Calculate semantic similarity using token overlap
        topic_tokens = set(generator.tokenizer.encode(topic))
        chunk_tokens = set(generator.tokenizer.encode(chunk))
        token_overlap = len(topic_tokens.intersection(chunk_tokens)) / len(topic_tokens)
        
        # Calculate topic density (how much of the chunk is about the topic)
        chunk_length = len(chunk.split())
        topic_density = len(common_words) / chunk_length if chunk_length > 0 else 0
        
        # Combine scores with weights
        final_score = (
            word_score * 0.4 +      # Word overlap
            token_overlap * 0.3 +   # Semantic similarity
            topic_density * 0.3     # Topic density
        )
        
        return min(1.0, final_score)  # Ensure score is between 0 and 1
        
    except Exception as e:
        logger.error(f"Error calculating chunk relevance: {str(e)}")
        return 0.0
