import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Description as FileIcon,
  Quiz as QuizIcon,
} from '@mui/icons-material';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setHistory(response.data.history);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch history');
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <Sidebar open={false} onClose={() => {}} />
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
        <Container maxWidth="lg">
          <Typography variant="h4" gutterBottom sx={{ mt: 4, mb: 4 }}>
            Activity History
          </Typography>
          <Paper elevation={3} sx={{ p: 2 }}>
            {loading ? (
              <Typography>Loading...</Typography>
            ) : error ? (
              <Typography color="error">{error}</Typography>
            ) : history.length === 0 ? (
              <Typography>No activity history found</Typography>
            ) : (
              <List>
                {history.map((item, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemIcon>
                        {item.type === 'file' ? <FileIcon /> : <QuizIcon />}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.title}
                        secondary={`${item.type === 'file' ? 'File uploaded' : 'Quiz taken'} on ${new Date(item.date).toLocaleString()}`}
                      />
                    </ListItem>
                    {index < history.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default History; 