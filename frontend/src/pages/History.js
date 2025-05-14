import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ArticleIcon from '@mui/icons-material/Article';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('http://localhost:5000/api/history', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Filter only summaries from the history
        const summaries = response.data.filter(item => item.type === 'summary');
        setHistory(summaries);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch history');
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography color="error" align="center">
          {error}
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Generated Summaries
      </Typography>
      
      {history.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No summaries generated yet
          </Typography>
        </Paper>
      ) : (
        <List>
          {history.map((item, index) => (
            <React.Fragment key={index}>
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    backgroundColor: '#f5f5f5',
                    '&:hover': {
                      backgroundColor: '#eeeeee',
                    },
                  }}
                >
                  <ListItemIcon>
                    <ArticleIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.topic}
                    secondary={new Date(item.date).toLocaleString()}
                  />
                </AccordionSummary>
                <AccordionDetails>
                  <Typography
                    component="div"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      p: 2,
                      backgroundColor: '#ffffff',
                      borderRadius: 1,
                    }}
                  >
                    {item.content}
                  </Typography>
                </AccordionDetails>
              </Accordion>
              {index < history.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      )}
    </Container>
  );
};

export default History; 