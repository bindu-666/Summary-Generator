import React, { useState, ChangeEvent } from 'react';
import {
  Container,
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import axios from 'axios';

interface StudyGuideResponse {
  studyGuide: string;
}

function App() {
  const [topic, setTopic] = useState('');
  const [studyGuide, setStudyGuide] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError('');
    try {
      const response = await axios.post<StudyGuideResponse>('http://localhost:5000/generate', { topic });
      setStudyGuide(response.data.studyGuide);
    } catch (err) {
      setError('Failed to generate study guide. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploadError('');
    setUploadSuccess('');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', files[0]);

    try {
      await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadSuccess(`Successfully uploaded ${files[0].name}`);
      setUploadedFiles(prev => [...prev, files[0].name]);
    } catch (err) {
      setUploadError('Failed to upload file. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
      // Reset the file input
      e.target.value = '';
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Study Guide Generator
        </Typography>

        {/* File Upload Section */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Study Materials
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload PDF, DOCX, or TXT files to index for study guide generation.
          </Typography>
          <Button
            variant="contained"
            component="label"
            disabled={loading}
            sx={{ mb: 2 }}
          >
            Upload File
            <input
              type="file"
              hidden
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
            />
          </Button>

          {uploadError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {uploadError}
            </Alert>
          )}

          {uploadSuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {uploadSuccess}
            </Alert>
          )}

          {uploadedFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Uploaded Files:
              </Typography>
              <List dense>
                {uploadedFiles.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={file} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Paper>

        <Divider sx={{ my: 3 }} />

        {/* Study Guide Generation Section */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generate Study Guide
          </Typography>
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Enter a topic"
              variant="outlined"
              value={topic}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setTopic(e.target.value)}
              margin="normal"
              disabled={loading}
              helperText="Enter a topic to generate a study guide from uploaded materials"
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              size="large"
              disabled={loading || !topic.trim()}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Study Guide'}
            </Button>
          </form>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {studyGuide && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Study Guide for: {topic}
            </Typography>
            <Typography
              component="pre"
              sx={{
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                fontFamily: 'inherit',
              }}
            >
              {studyGuide}
            </Typography>
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App;
