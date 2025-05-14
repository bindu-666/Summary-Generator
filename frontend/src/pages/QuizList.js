import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Description as FileIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const QuizList = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/api/files', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setFiles(response.data.files);
    } catch (error) {
      setError('Failed to load files. Please try again.');
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuizClick = (filename) => {
    navigate(`/quiz/${encodeURIComponent(filename)}`);
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
              Available Quizzes
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {files.length === 0 ? (
              <Typography variant="body1" sx={{ mt: 2 }}>
                No files available for quiz generation. Please upload some study materials first.
              </Typography>
            ) : (
              <List>
                {files.map((file) => (
                  <ListItem
                    key={file.filename}
                    button
                    onClick={() => handleQuizClick(file.filename)}
                    sx={{
                      mb: 1,
                      backgroundColor: 'white',
                      borderRadius: 1,
                      '&:hover': {
                        backgroundColor: '#f0f0f0'
                      }
                    }}
                  >
                    <ListItemIcon>
                      <FileIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={file.filename}
                      secondary={`Uploaded: ${new Date(file.upload_date).toLocaleDateString()}`}
                    />
                    <Button variant="contained" color="primary">
                      Start Quiz
                    </Button>
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default QuizList; 