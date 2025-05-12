import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Box,
  Typography,
} from '@mui/material';

const Sidebar = ({ open, onClose }) => {
  const menuItems = [
    {
      text: 'My Uploads',
      onClick: () => {
        // Handle My Uploads click
        console.log('My Uploads clicked');
      },
    },
  ];

  return (
    <>
      <IconButton
        color="inherit"
        aria-label="open drawer"
        onClick={onClose}
        edge="start"
        sx={{ 
          position: 'fixed',
          left: 16,
          top: 16,
          zIndex: 1200,
          color: 'white',
          padding: '4px',
          '&:hover': {
            backgroundColor: 'transparent',
          },
        }}
      >
        ☰
      </IconButton>
      <Drawer
        variant="temporary"
        anchor="left"
        open={open}
        onClose={onClose}
        sx={{
          width: 240,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 240,
            boxSizing: 'border-box',
            marginTop: '64px', // Add margin to account for the hamburger menu
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" noWrap component="div">
            Study Guide
          </Typography>
        </Box>
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={item.onClick}
              sx={{
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
              }}
            >
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>
    </>
  );
};

export default Sidebar; 