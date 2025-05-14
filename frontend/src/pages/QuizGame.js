import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Typography,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  Paper,
  Container,
  CircularProgress,
  Alert,
} from '@mui/material';

const QuizGame = () => {
  const { filename } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [score, setScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    generateQuiz();
  }, [filename]);

  const generateQuiz = async () => {
    try {
      setLoading(true);
      const response = await axios.post(
        'http://localhost:5000/generate-quiz',
        { filename, num_questions: 5 },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      setQuestions(response.data.questions);
      setLoading(false);
    } catch (error) {
      console.error('Error generating quiz:', error);
      setError('Failed to generate quiz. Please try again.');
      setLoading(false);
    }
  };

  const handleAnswerChange = (event) => {
    setSelectedAnswer(event.target.value);
  };

  const handleSubmit = () => {
    if (selectedAnswer === questions[currentQuestion].correct_answer) {
      setScore(score + 1);
    }

    if (currentQuestion < 4) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer('');
    } else {
      setQuizCompleted(true);
    }
  };

  const handleRetry = () => {
    setQuestions([]);
    setCurrentQuestion(0);
    setSelectedAnswer('');
    setScore(0);
    setQuizCompleted(false);
    generateQuiz();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm">
        <Alert severity="error" sx={{ mt: 4 }}>{error}</Alert>
        <Button onClick={() => navigate('/quiz')} sx={{ mt: 2 }}>Back to Quiz List</Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        {!quizCompleted ? (
          <>
            <Typography variant="h5" gutterBottom>
              Question {currentQuestion + 1} of 5
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {questions[currentQuestion]?.question}
            </Typography>
            <FormControl component="fieldset">
              <RadioGroup value={selectedAnswer} onChange={handleAnswerChange}>
                {questions[currentQuestion]?.options.map((option, index) => (
                  <FormControlLabel
                    key={index}
                    value={option}
                    control={<Radio />}
                    label={option}
                  />
                ))}
              </RadioGroup>
            </FormControl>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={!selectedAnswer}
              sx={{ mt: 2 }}
            >
              {currentQuestion === 4 ? 'Finish' : 'Next'}
            </Button>
          </>
        ) : (
          <>
            <Typography variant="h5" gutterBottom>
              Quiz Completed!
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Your score: {score} out of 5
            </Typography>
            <Button variant="contained" onClick={handleRetry} sx={{ mr: 2 }}>
              Retry Quiz
            </Button>
            <Button variant="outlined" onClick={() => navigate('/quiz')}>
              Back to Quiz List
            </Button>
          </>
        )}
      </Paper>
    </Container>
  );
};

export default QuizGame;