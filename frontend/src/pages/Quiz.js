import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const Quiz = () => {
  const { filename } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [score, setScore] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    generateQuiz();
  }, [filename]);

  const generateQuiz = async () => {
    try {
      setLoading(true);
      const response = await axios.post(
        'http://localhost:5000/generate-quiz',
        { filename },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      console.log('Quiz response:', response.data);
      if (!response.data.questions || !Array.isArray(response.data.questions)) {
        throw new Error('Invalid quiz response format');
      }
      setQuestions(response.data.questions);
      setAnswers({});
      setScore(null);
    } catch (error) {
      console.error('Error generating quiz:', error);
      setError(error.response?.data?.error || 'Failed to generate quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSubmit = () => {
    const correctAnswers = questions.filter(
      q => answers[q.id] === q.correct_answer
    ).length;
    setScore({
      correct: correctAnswers,
      total: questions.length,
      percentage: (correctAnswers / questions.length) * 100
    });
  };

  const handleNewQuiz = () => {
    generateQuiz();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(!sidebarOpen)} />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          minHeight: '100vh',
          backgroundColor: '#f5f5f5'
        }}
      >
        <Container maxWidth="md">
          <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
            <Typography variant="h4" gutterBottom>
              Quiz: {filename}
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {score ? (
              <Box sx={{ textAlign: 'center', my: 4 }}>
                <Typography variant="h5" gutterBottom>
                  Quiz Results
                </Typography>
                <Typography variant="h6">
                  Score: {score.correct} out of {score.total} ({score.percentage.toFixed(1)}%)
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleNewQuiz}
                  sx={{ mt: 2 }}
                >
                  Generate New Quiz
                </Button>
              </Box>
            ) : (
              <Box>
                {questions.map((question, index) => (
                  <FormControl
                    key={question.id}
                    component="fieldset"
                    sx={{ mb: 3, width: '100%' }}
                  >
                    <FormLabel component="legend">
                      Question {index + 1}: {question.question}
                    </FormLabel>
                    <RadioGroup
                      value={answers[question.id] || ''}
                      onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                    >
                      {question.options.map((option, optIndex) => (
                        <FormControlLabel
                          key={optIndex}
                          value={option}
                          control={<Radio />}
                          label={option}
                        />
                      ))}
                    </RadioGroup>
                  </FormControl>
                ))}

                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={Object.keys(answers).length !== questions.length}
                  sx={{ mt: 2 }}
                >
                  Submit Quiz
                </Button>
              </Box>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default Quiz; 