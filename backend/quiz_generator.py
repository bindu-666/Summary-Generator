import random
import nltk
from nltk.tokenize import sent_tokenize

class QuizGenerator:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def generate_quiz(self, text, num_questions=5):
        """Generate a quiz from the given text."""
        # Split text into sentences
        sentences = sent_tokenize(text)
        if not sentences:
            return []

        # Generate questions
        quiz = []
        used_sentences = set()

        # Pre-process all sentences to find important words
        sentence_important_words = {}
        for sentence in sentences:
            important_words = self._find_important_words(sentence)
            if important_words:
                sentence_important_words[sentence] = important_words

        while len(quiz) < num_questions and len(used_sentences) < len(sentences):
            # Get a random sentence that hasn't been used
            available_sentences = [s for s in sentences if s not in used_sentences]
            if not available_sentences:
                break

            sentence = random.choice(available_sentences)
            used_sentences.add(sentence)

            # Get important words for this sentence
            important_words = sentence_important_words.get(sentence, [])
            if not important_words:
                continue

            # Choose a word to be the answer
            answer = random.choice(important_words)
            
            # Create the question by replacing the answer with a blank
            words = sentence.split()
            answer_words = answer.split()
            
            # Find the starting index of the answer in the sentence
            start_index = -1
            for i in range(len(words) - len(answer_words) + 1):
                if ' '.join(words[i:i + len(answer_words)]).lower() == answer.lower():
                    start_index = i
                    break
            
            if start_index == -1:
                continue
                
            # Replace the answer with blank(s)
            for i in range(len(answer_words)):
                words[start_index + i] = "__________"
            
            # Remove extra blanks if they're adjacent
            question = ' '.join(words).replace("__________ __________", "__________")
            
            # Generate incorrect options
            incorrect_options = self._generate_incorrect_options(sentence_important_words, answer)
            if len(incorrect_options) < 3:  # Skip if we can't generate enough options
                continue

            # Combine and shuffle options
            options = incorrect_options + [answer]
            random.shuffle(options)

            quiz.append({
                "question": question,
                "options": options,
                "correct_answer": answer
            })

        return quiz

    def _find_important_words(self, sentence):
        """Find important words in a sentence that would make good quiz answers."""
        words = sentence.split()
        important_words = []
        
        # Look for capitalized words and numbers
        for word in words:
            # Skip very short words
            if len(word) <= 3:
                continue
                
            # Include capitalized words (likely proper nouns)
            if word[0].isupper():
                important_words.append(word)
                
            # Include numbers
            if any(c.isdigit() for c in word):
                important_words.append(word)
                
            # Include longer words (likely important terms)
            if len(word) > 6:
                important_words.append(word)
        
        return important_words

    def _generate_incorrect_options(self, sentence_important_words, correct_answer, num_options=3):
        """Generate incorrect options that are contextually relevant."""
        # Get all important words from all sentences
        all_important_words = []
        for words in sentence_important_words.values():
            all_important_words.extend(words)

        # Remove duplicates and the correct answer (case-insensitive)
        unique_words = [w for w in all_important_words 
                       if w.lower() != correct_answer.lower()]

        # If we don't have enough unique words, return what we have
        if len(unique_words) < num_options:
            return unique_words

        # Return random incorrect options
        return random.sample(unique_words, num_options)

# Usage example
if __name__ == "__main__":
    quiz_gen = QuizGenerator()
    sample_text = """
    The Himalayas were formed about 50 million years ago when the Indian tectonic plate collided with the Eurasian plate.
    This massive collision created the world's highest mountain range, with Mount Everest standing at 29,029 feet above sea level.
    The range spans five countries: India, Nepal, Bhutan, China, and Pakistan.
    The Himalayas are home to diverse ecosystems, from tropical forests at the base to permanent snow and ice at the highest elevations.
    """
    quiz = quiz_gen.generate_quiz(sample_text)
    for i, item in enumerate(quiz, 1):
        print(f"Question {i}: {item['question']}")
        for j, option in enumerate(item['options'], 1):
            print(f"  {j}. {option}")
        print(f"Correct answer: {item['correct_answer']}\n")