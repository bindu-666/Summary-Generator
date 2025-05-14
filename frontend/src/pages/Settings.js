import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
} from '@mui/material';
import axios from 'axios';
import Sidebar from '../components/Sidebar';

const Settings = () => {
  const [settings, setSettings] = useState({
    email: '',
    notifications: true,
    darkMode: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/settings', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setSettings(response.data.settings);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch settings');
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, checked } = e.target;
    setSettings({
      ...settings,
      [name]: e.target.type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await axios.put('http://localhost:5000/api/settings', settings, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setSuccess('Settings updated successfully');
    } catch (err) {
      setError('Failed to update settings');
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
        <Container maxWidth="md">
          <Typography variant="h4" gutterBottom sx={{ mt: 4, mb: 4 }}>
            Settings
          </Typography>
          <Paper elevation={3} sx={{ p: 3 }}>
            {loading ? (
              <Typography>Loading...</Typography>
            ) : (
              <Box component="form" onSubmit={handleSubmit}>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
                
                <Typography variant="h6" gutterBottom>
                  Account Settings
                </Typography>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={settings.email}
                  onChange={handleChange}
                  margin="normal"
                />
                
                <Divider sx={{ my: 3 }} />
                
                <Typography variant="h6" gutterBottom>
                  Preferences
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications}
                      onChange={handleChange}
                      name="notifications"
                    />
                  }
                  label="Enable Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.darkMode}
                      onChange={handleChange}
                      name="darkMode"
                    />
                  }
                  label="Dark Mode"
                />
                
                <Box sx={{ mt: 3 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    size="large"
                  >
                    Save Changes
                  </Button>
                </Box>
              </Box>
            )}
          </Paper>
        </Container>
      </Box>
    </Box>
  );
};

export default Settings; 