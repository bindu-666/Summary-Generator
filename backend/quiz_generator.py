import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from nltk.tokenize import sent_tokenize
import random

class QuizGenerator:
    def __init__(self):
        self.model_name = "allenai/t5-small-squad2-qg"
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def generate_qa_pairs(self, text, num_questions=5):
        sentences = sent_tokenize(text)
        qa_pairs = []

        while len(qa_pairs) < num_questions and sentences:
            sentence = random.choice(sentences)
            sentences.remove(sentence)

            input_text = f"generate question: {sentence}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)

            outputs = self.model.generate(input_ids, max_length=64, num_return_sequences=1)
            question = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            input_text = f"generate answer: {question} context: {sentence}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)

            outputs = self.model.generate(input_ids, max_length=64, num_return_sequences=1)
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            qa_pairs.append({"question": question, "answer": answer})

        return qa_pairs

    def generate_quiz(self, text, num_questions=5):
        qa_pairs = self.generate_qa_pairs(text, num_questions)
        quiz = []

        for pair in qa_pairs:
            question = pair["question"]
            correct_answer = pair["answer"]
            
            # Generate incorrect options
            incorrect_options = self.generate_incorrect_options(text, correct_answer, 3)
            
            options = incorrect_options + [correct_answer]
            random.shuffle(options)

            quiz_item = {
                "question": question,
                "options": options,
                "correct_answer": correct_answer
            }
            quiz.append(quiz_item)

        return quiz

    def generate_incorrect_options(self, text, correct_answer, num_options=3):
        sentences = sent_tokenize(text)
        incorrect_options = []

        while len(incorrect_options) < num_options and sentences:
            sentence = random.choice(sentences)
            sentences.remove(sentence)

            input_text = f"generate wrong answer: {correct_answer} context: {sentence}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)

            outputs = self.model.generate(input_ids, max_length=32, num_return_sequences=1)
            wrong_answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            if wrong_answer != correct_answer and wrong_answer not in incorrect_options:
                incorrect_options.append(wrong_answer)

        return incorrect_options

# Usage example
if __name__ == "__main__":
    quiz_gen = QuizGenerator()
    sample_text = """
    Python is a high-level, interpreted programming language. It was created by Guido van Rossum 
    and first released in 1991. Python's design philosophy emphasizes code readability with its 
    notable use of significant whitespace. Its language constructs and object-oriented approach 
    aim to help programmers write clear, logical code for small and large-scale projects.
    """
    quiz = quiz_gen.generate_quiz(sample_text)
    for i, item in enumerate(quiz, 1):
        print(f"Question {i}: {item['question']}")
        for j, option in enumerate(item['options'], 1):
            print(f"  {j}. {option}")
        print(f"Correct answer: {item['correct_answer']}\n")