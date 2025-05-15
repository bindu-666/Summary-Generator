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
  Collapse,
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
  Dashboard as DashboardIcon,
  Description as FileIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const drawerWidth = 280; // Increased width for better file display

const Sidebar = ({ open, onClose }) => {
  const navigate = useNavigate();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [filesOpen, setFilesOpen] = useState(true);

  useEffect(() => {
    // Fetch uploaded files when component mounts
    fetchUploadedFiles();
    
    // Set up polling to refresh files every 30 seconds
    const interval = setInterval(fetchUploadedFiles, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/files', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setUploadedFiles(response.data.files);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  // Add event listener for file upload success
  useEffect(() => {
    const handleFileUpload = () => {
      fetchUploadedFiles();
    };

    window.addEventListener('fileUploaded', handleFileUpload);
    return () => {
      window.removeEventListener('fileUploaded', handleFileUpload);
    };
  }, []);

  const handleQuizClick = (filename) => {
    navigate(`/quiz/${encodeURIComponent(filename)}`);
  };

  const handleDrawerToggle = () => {
    onClose();
  };

  const handleNavigation = (path) => {
    navigate(path);
    onClose();
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleViewFile = (filename) => {
    navigate(`/file/${encodeURIComponent(filename)}`);
  };

  const handleFilesToggle = () => {
    setFilesOpen(!filesOpen);
  };

  const menuItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Upload', icon: <UploadIcon />, path: '/upload' },
    { text: 'Generate Summary', icon: <FileIcon />, path: '/summary-generator' },
    { text: 'Quiz', icon: <QuizIcon />, path: '/quiz' },
  ];

  const drawer = (
    <Box sx={{ overflow: 'auto', height: '100%' }}>
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
      <List>
        <ListItemButton onClick={handleFilesToggle}>
          <ListItemIcon>
            <FileIcon />
          </ListItemIcon>
          <ListItemText primary="Uploaded Files" />
          {filesOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        <Collapse in={filesOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {uploadedFiles.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No files uploaded"
                  sx={{ pl: 4, color: 'text.secondary' }}
                />
              </ListItem>
            ) : (
              uploadedFiles.map((file) => (
                <ListItem 
                  button 
                  key={file.id}
                  onClick={() => handleViewFile(file.filename)}
                  sx={{ pl: 4 }}
                >
                  <ListItemIcon>
                    <FileIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary={file.filename}
                    secondary={`Uploaded: ${new Date(file.upload_date).toLocaleDateString()}`}
                    primaryTypographyProps={{
                      noWrap: true,
                      style: { maxWidth: '180px' }
                    }}
                  />
                </ListItem>
              ))
            )}
          </List>
        </Collapse>
      </List>
      <Box sx={{ flexGrow: 1, minHeight: '200px' }} />
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
          open={open}
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
              borderRight: '1px solid rgba(0, 0, 0, 0.12)',
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