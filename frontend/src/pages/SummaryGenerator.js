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

const SummaryGenerator = () => {
  const [topic, setTopic] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleTopicChange = (e) => {
    setTopic(e.target.value);
    setError('');
    setSuccess('');
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

            {/* Summary Display */}
            {summary && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Generated Summary
                </Typography>
                <Paper elevation={1} sx={{ p: 2, backgroundColor: '#fff' }}>
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

export default SummaryGenerator; 