import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Tab,
  Tabs,
  CircularProgress
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Login form state
  const [loginData, setLoginData] = useState({
    username: 'demo_user'  // Pre-fill with demo user
  });
  
  // Registration form state
  const [registerData, setRegisterData] = useState({
    username: '',
    email: ''
  });

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(loginData.username);
    
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!registerData.username.trim()) {
      setError('Username is required');
      setLoading(false);
      return;
    }

    const result = await register(registerData);
    
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  // Helper function to safely render error messages
  const renderError = (error) => {
    if (typeof error === 'string') {
      return error;
    } else if (error && typeof error === 'object') {
      // Handle object errors by extracting message
      if (error.message) {
        return error.message;
      } else if (error.detail) {
        return Array.isArray(error.detail) ? error.detail.map(e => e.msg).join(', ') : error.detail;
      } else {
        return 'An error occurred. Please try again.';
      }
    }
    return 'An error occurred. Please try again.';
  };

  return (
    <Container component="main" maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box textAlign="center" mb={3}>
          <Typography component="h1" variant="h4" gutterBottom>
            🎓 AI Course Recommender
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Discover personalized learning paths powered by AI
          </Typography>
        </Box>

        <Tabs value={tab} onChange={handleTabChange} centered sx={{ mb: 3 }}>
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {renderError(error)}
          </Alert>
        )}

        {tab === 0 ? (
          // Login Form
          <Box component="form" onSubmit={handleLogin}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={loginData.username}
              onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
              disabled={loading}
            />
            
            <Box mt={2} mb={2}>
              <Alert severity="info">
                <Typography variant="body2">
                  <strong>Demo Login:</strong> Use username "demo_user" to try the system with sample data.
                </Typography>
              </Alert>
            </Box>
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
          </Box>
        ) : (
          // Registration Form
          <Box component="form" onSubmit={handleRegister}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={registerData.username}
              onChange={(e) => setRegisterData({ ...registerData, username: e.target.value })}
              disabled={loading}
            />
            <TextField
              margin="normal"
              fullWidth
              id="email"
              label="Email Address (Optional)"
              name="email"
              autoComplete="email"
              type="email"
              value={registerData.email}
              onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
              disabled={loading}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Register'}
            </Button>
          </Box>
        )}

        <Box mt={4}>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            This demo showcases an AI-powered course recommendation system built with React, FastAPI, and Llama 3.2
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login; 