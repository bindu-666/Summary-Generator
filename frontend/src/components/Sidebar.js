import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Typography,
  Divider,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Upload as UploadIcon,
  Quiz as QuizIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const drawerWidth = 240;

const Sidebar = () => {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const fetchUploadedFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.get('http://localhost:5000/api/files', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setUploadedFiles(response.data.files);
    } catch (err) {
      console.error('Error fetching files:', err);
      setError('Failed to load uploaded files');
    } finally {
      setLoading(false);
    }
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleViewFile = async (filename) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      // Create a temporary link element
      const link = document.createElement('a');
      link.href = `http://localhost:5000/api/files/${filename}`;
      link.setAttribute('download', filename);
      
      // Add authorization header
      const response = await fetch(link.href, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to download file');
      }
      
      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);
      link.href = url;
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error viewing file:', err);
      // You might want to show an error message to the user here
    }
  };

  const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/dashboard' },
    { text: 'Upload', icon: <UploadIcon />, path: '/upload' },
    { text: 'Quiz', icon: <QuizIcon />, path: '/quiz' },
    { text: 'History', icon: <HistoryIcon />, path: '/history' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const drawer = (
    <Box sx={{ overflow: 'auto' }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" noWrap component="div">
          Study Guide
        </Typography>
      </Box>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton onClick={() => handleNavigation(item.path)}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Uploaded Files
        </Typography>
        {loading ? (
          <Typography variant="body2">Loading files...</Typography>
        ) : error ? (
          <Typography variant="body2" color="error">{error}</Typography>
        ) : uploadedFiles.length === 0 ? (
          <Typography variant="body2">No files uploaded yet</Typography>
        ) : (
          <List>
            {uploadedFiles.map((file) => (
              <ListItem
                key={file.filename}
                disablePadding
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  px: 2,
                  py: 1,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    maxWidth: '70%',
                  }}
                >
                  {file.filename}
                </Typography>
                <Tooltip title="View file">
                  <IconButton
                    size="small"
                    onClick={() => handleViewFile(file.filename)}
                  >
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </ListItem>
            ))}
          </List>
        )}
      </Box>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <Button
        variant="contained"
        onClick={handleDrawerToggle}
        sx={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          display: { sm: 'none' },
        }}
      >
        <MenuIcon />
      </Button>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
    </Box>
  );
};

export default Sidebar; 