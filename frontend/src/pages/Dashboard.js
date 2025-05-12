import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const Dashboard = () => {
  const [file, setFile] = useState(null);
  const [topic, setTopic] = useState('');
  const [studyGuide, setStudyGuide] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
    setSuccess('');
  };

  const handleTopicChange = (e) => {
    setTopic(e.target.value);
    setError('');
    setSuccess('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      setError('');
      setSuccess('');
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.message) {
        setSuccess(response.data.message);
        setFile(null);
      } else {
        setError('No response message from server');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.error || 'Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!topic) {
      setError('Please enter a topic');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess('');
      const response = await axios.post('http://localhost:5000/generate', {
        topic: topic,
      });
      
      if (response.data.study_guide) {
        setStudyGuide(response.data.study_guide);
        setSuccess('Study guide generated successfully');
      } else {
        setError('No study guide received from server');
      }
    } catch (err) {
      console.error('Generate error:', err);
      setError(err.response?.data?.error || 'Error generating study guide');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(!sidebarOpen)} />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          marginTop: '64px', // Add margin to account for the hamburger menu
        }}
      >
        <Container maxWidth="md">
          <Paper elevation={3} sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
              Study Guide Generator
            </Typography>

            {/* File Upload Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Upload Study Material
              </Typography>
              <input
                accept=".pdf,.docx,.txt"
                style={{ display: 'none' }}
                id="file-upload"
                type="file"
                onChange={handleFileChange}
              />
              <label htmlFor="file-upload">
                <Button variant="contained" component="span" sx={{ mr: 2 }}>
                  Choose File
                </Button>
              </label>
              {file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected file: {file.name}
                </Typography>
              )}
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!file || loading}
                sx={{ mt: 2 }}
              >
                Upload
              </Button>
            </Box>

            {/* Topic Input Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Generate Study Guide
              </Typography>
              <TextField
                fullWidth
                label="Enter Topic"
                value={topic}
                onChange={handleTopicChange}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleGenerate}
                disabled={!topic || loading}
              >
                Generate Study Guide
              </Button>
            </Box>

            {/* Status Messages */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}

            {/* Loading Indicator */}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <CircularProgress />
              </Box>
            )}

            {/* Study Guide Display */}
            {studyGuide && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Generated Study Guide
                </Typography>
                <Paper elevation={1} sx={{ p: 2, whiteSpace: 'pre-wrap' }}>
                  {studyGuide}
                </Paper>
              </Box>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default Dashboard; 