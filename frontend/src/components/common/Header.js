import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Chip
} from '@mui/material';
import {
  AccountCircle,
  Dashboard as DashboardIcon,
  Recommend,
  School,
  Settings
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleClose();
  };

  const isActive = (path) => location.pathname === path;

  if (!isAuthenticated) {
    return (
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            🎓 AI Course Recommender
          </Typography>
        </Toolbar>
      </AppBar>
    );
  }

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography 
          variant="h6" 
          sx={{ 
            flexGrow: 1, 
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
          onClick={() => navigate('/')}
        >
          🎓 AI Course Recommender
        </Typography>

        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
          <Button
            color="inherit"
            startIcon={<DashboardIcon />}
            onClick={() => navigate('/')}
            variant={isActive('/') ? 'outlined' : 'text'}
            sx={{ 
              color: 'white',
              borderColor: isActive('/') ? 'white' : 'transparent'
            }}
          >
            Dashboard
          </Button>
          
          <Button
            color="inherit"
            startIcon={<Recommend />}
            onClick={() => navigate('/recommendations')}
            variant={isActive('/recommendations') ? 'outlined' : 'text'}
            sx={{ 
              color: 'white',
              borderColor: isActive('/recommendations') ? 'white' : 'transparent'
            }}
          >
            Recommendations
          </Button>
          
          <Button
            color="inherit"
            startIcon={<School />}
            onClick={() => navigate('/courses')}
            variant={isActive('/courses') ? 'outlined' : 'text'}
            sx={{ 
              color: 'white',
              borderColor: isActive('/courses') ? 'white' : 'transparent'
            }}
          >
            Courses
          </Button>
        </Box>

        {user && (
          <Box sx={{ ml: 2 }}>
            <Chip
              avatar={<Avatar sx={{ bgcolor: 'secondary.main' }}>{user.username[0].toUpperCase()}</Avatar>}
              label={user.username}
              variant="outlined"
              sx={{ 
                color: 'white',
                borderColor: 'white',
                '& .MuiChip-avatar': {
                  color: 'white !important'
                }
              }}
              onClick={handleMenu}
            />
            <Menu
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem onClick={() => { navigate('/profile'); handleClose(); }}>
                <Settings sx={{ mr: 1 }} />
                Profile & Settings
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <AccountCircle sx={{ mr: 1 }} />
                Logout
              </MenuItem>
            </Menu>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header; 