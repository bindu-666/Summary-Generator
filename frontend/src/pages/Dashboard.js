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
  const [summary, setSummary] = useState('');
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

    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please log in to upload files');
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
          'Authorization': `Bearer ${token}`
        },
      });
      
      if (response.data.message) {
        setSuccess(response.data.message);
        setFile(null);
        // Dispatch event to notify sidebar of new file
        window.dispatchEvent(new Event('fileUploaded'));
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

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSummary(null);
    setSuccess(null);
    
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please log in to generate summaries');
      setLoading(false);
      return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ topic: topic }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate summary');
        }
        
        if (!data.study_guide) {
            throw new Error('No summary received from server');
        }
        
        setSummary(data.study_guide);
        setSuccess(data.message || 'Summary generated successfully');
        
    } catch (err) {
        console.error('Error generating summary:', err);
        setError(err.message);
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
          minHeight: '100vh',
          backgroundColor: '#f5f5f5'
        }}
      >
        <Container maxWidth="md">
          <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
            <Typography variant="h4" gutterBottom>
              Summary Generator
            </Typography>

            {/* File Upload Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" gutterBottom>
                Upload Document
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
                Generate Summary
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
                sx={{ mt: 2 }}
              >
                Generate Summary
              </Button>
            </Box>

            {/* Loading State */}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                <CircularProgress />
              </Box>
            )}

            {/* Error Message */}
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            {/* Success Message */}
            {success && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {success}
              </Alert>
            )}

            {/* Generated Summary */}
            {summary && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Generated Summary
                </Typography>
                <Paper elevation={1} sx={{ p: 3, backgroundColor: '#fff' }}>
                  <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                    {summary}
                  </Typography>
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