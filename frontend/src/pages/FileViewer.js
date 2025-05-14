import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const FileViewer = () => {
  const { filename } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    fetchFileContent();
  }, [filename]);

  const fetchFileContent = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/api/files/${filename}/content`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setContent(response.data.content);
    } catch (error) {
      console.error('Error fetching file content:', error);
      setError('Failed to load file content. Please try again.');
    } finally {
      setLoading(false);
    }
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
              {filename}
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Paper 
              elevation={1} 
              sx={{ 
                p: 3, 
                backgroundColor: '#fff',
                maxHeight: '70vh',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace'
              }}
            >
              <Typography variant="body1">
                {content}
              </Typography>
            </Paper>
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default FileViewer; 