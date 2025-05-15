import React from 'react';
import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as SummaryIcon,
  Quiz as QuizIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

const Home = () => {
  const navigate = useNavigate();

  const cards = [
    {
      title: 'Upload',
      description: 'Upload your documents to generate summaries and quizzes',
      icon: <UploadIcon sx={{ fontSize: 40 }} />,
      path: '/upload',
      color: '#1976d2'
    },
    {
      title: 'Generate Summary',
      description: 'Create concise summaries from your uploaded documents',
      icon: <SummaryIcon sx={{ fontSize: 40 }} />,
      path: '/summary-generator',
      color: '#2e7d32'
    },
    {
      title: 'Quiz',
      description: 'Test your knowledge with quizzes based on your documents',
      icon: <QuizIcon sx={{ fontSize: 40 }} />,
      path: '/quiz',
      color: '#ed6c02'
    }
  ];

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
            Welcome to Study Guide
          </Typography>
          <Grid container spacing={4}>
            {cards.map((card) => (
              <Grid item xs={12} sm={6} md={4} key={card.title}>
                <Card 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'scale(1.02)',
                      boxShadow: 6
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                    <Box sx={{ color: card.color, mb: 2 }}>
                      {card.icon}
                    </Box>
                    <Typography gutterBottom variant="h5" component="h2">
                      {card.title}
                    </Typography>
                    <Typography>
                      {card.description}
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                    <Button 
                      variant="contained" 
                      onClick={() => navigate(card.path)}
                      sx={{ 
                        backgroundColor: card.color,
                        '&:hover': {
                          backgroundColor: card.color,
                          opacity: 0.9
                        }
                      }}
                    >
                      Get Started
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>
    </Box>
  );
};

export default Home; 