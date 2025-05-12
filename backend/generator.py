from transformers import pipeline
import torch
from typing import List, Dict
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

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

def generate_study_guide(topic: str, input_text: str) -> str:
    """
    Generate a focused study guide using a text2text-generation model.
    
    Args:
        topic (str): The topic for the study guide
        input_text (str): The context to use for generation
        
    Returns:
        str: The generated study guide
    """
    try:
        # Create a focused prompt
        prompt = f"""Write a comprehensive study guide about {topic} using only this context.
        Focus on key concepts, definitions, and practical applications.
        Context:
        {input_text}
        """
        
        # Generate the study guide
        logger.info(f"Generating study guide for topic: {topic}")
        logger.info(f"Input text length: {len(input_text)}")
        
        result = generator(
            prompt,
            max_length=1024,
            min_length=200,
            num_beams=5,
            temperature=0.8,
            top_p=0.95,
            do_sample=True,
            truncation=True,
            repetition_penalty=1.5,
            length_penalty=1.0,
            no_repeat_ngram_size=3
        )
        
        generated_text = result[0]['generated_text']
        logger.info(f"Generated study guide length: {len(generated_text)}")
        logger.info(f"Generated content preview: {generated_text[:200]}...")
        
        return generated_text
        
    except Exception as e:
        logger.error(f"Error generating study guide: {str(e)}")
        raise

def generate_study_guide_from_text(text_chunks, preferences=''):
    """
    Generate a study guide from the provided text chunks.
    
    Args:
        text_chunks (list): List of text chunks to process
        preferences (str): User preferences for the study guide
        
    Returns:
        str: Generated study guide
    """
    logger.info(f"Generating study guide from {len(text_chunks)} chunks")
    
    try:
        # Combine chunks into a single text
        combined_text = ' '.join(text_chunks)
        logger.debug(f"Combined text length: {len(combined_text)}")
        
        # Add preferences to the input text
        if preferences:
            combined_text = f"Preferences: {preferences}\n\n{combined_text}"
        
        # Tokenize the input
        inputs = tokenizer(combined_text, max_length=1024, truncation=True, return_tensors='pt')
        logger.debug("Text tokenized successfully")
        
        # Generate summary
        summary_ids = model.generate(
            inputs['input_ids'],
            max_length=500,
            min_length=100,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        logger.debug("Summary generated successfully")
        
        # Decode and return the generated text
        study_guide = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        logger.info(f"Generated study guide length: {len(study_guide)}")
        
        if not study_guide:
            logger.error("Generated study guide is empty")
            return "Failed to generate study guide. Please try again."
            
        return study_guide
        
    except Exception as e:
        logger.error(f"Error generating study guide: {str(e)}", exc_info=True)
        return f"Error generating study guide: {str(e)}" 