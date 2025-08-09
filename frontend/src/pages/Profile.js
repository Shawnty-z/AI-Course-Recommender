import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Rating,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton
} from '@mui/material';
import {
  Person,
  Settings,
  Save,
  History,
  School,
  TrendingUp,
  Star,
  Edit,
  Delete
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State management
  const [editing, setEditing] = useState(false);
  const [topicInput, setTopicInput] = useState('');
  const [preferences, setPreferences] = useState({
    preferred_topics: [],
    difficulty_level: '',
    learning_style: '',
    time_commitment: ''
  });

  // Fetch user preferences
  const { data: currentPreferences, isLoading: preferencesLoading } = useQuery(
    ['user-preferences', user?.id],
    async () => {
      const response = await axios.get('/api/feedback/preferences');
      return response.data;
    },
    {
      enabled: !!user,
      onSuccess: (data) => {
        setPreferences({
          preferred_topics: data.preferred_topics || [],
          difficulty_level: data.difficulty_level || '',
          learning_style: data.learning_style || '',
          time_commitment: data.time_commitment || ''
        });
      }
    }
  );

  // Fetch user feedback history
  const { data: feedbackHistory, isLoading: feedbackLoading } = useQuery(
    ['user-feedback', user?.id],
    async () => {
      const response = await axios.get('/api/feedback/');
      return response.data;
    },
    { enabled: !!user }
  );

  // Fetch learning analytics
  const { data: analytics } = useQuery(
    ['user-analytics', user?.id],
    async () => {
      const response = await axios.get(`/api/recommendations/${user.id}/history`);
      return response.data;
    },
    { enabled: !!user }
  );

  // Update preferences mutation
  const updatePreferencesMutation = useMutation(
    async (newPreferences) => {
      return axios.put('/api/feedback/preferences', newPreferences);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['user-preferences']);
        queryClient.invalidateQueries(['recommendations', user.id]);
        setEditing(false);
      }
    }
  );

  // Handle adding topic
  const handleAddTopic = () => {
    if (topicInput.trim() && !preferences.preferred_topics.includes(topicInput.trim())) {
      setPreferences(prev => ({
        ...prev,
        preferred_topics: [...prev.preferred_topics, topicInput.trim()]
      }));
      setTopicInput('');
    }
  };

  // Handle removing topic
  const handleRemoveTopic = (topicToRemove) => {
    setPreferences(prev => ({
      ...prev,
      preferred_topics: prev.preferred_topics.filter(topic => topic !== topicToRemove)
    }));
  };

  // Handle saving preferences
  const handleSavePreferences = () => {
    updatePreferencesMutation.mutate(preferences);
  };

  // Reset preferences to current saved state
  const handleCancelEdit = () => {
    if (currentPreferences) {
      setPreferences({
        preferred_topics: currentPreferences.preferred_topics || [],
        difficulty_level: currentPreferences.difficulty_level || '',
        learning_style: currentPreferences.learning_style || '',
        time_commitment: currentPreferences.time_commitment || ''
      });
    }
    setEditing(false);
  };

  // Handle feedback deletion
  const handleDeleteFeedback = async (feedbackId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) {
      return;
    }
    
    try {
      await axios.delete(`/api/feedback/${feedbackId}`);
      // Refresh feedback history
      queryClient.invalidateQueries(['user-feedback', user?.id]);
      queryClient.invalidateQueries(['recommendations', user.id]);
    } catch (error) {
      console.error('Failed to delete feedback:', error);
      alert('Failed to delete review. Please try again.');
    }
  };

  // Get difficulty color
  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return 'success';
      case 'intermediate': return 'warning';
      case 'advanced': return 'error';
      default: return 'default';
    }
  };

  if (preferencesLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        👤 My Profile
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Manage your learning preferences and track your progress
      </Typography>

      <Grid container spacing={3}>
        {/* User Info & Preferences */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                <Person sx={{ mr: 1, verticalAlign: 'middle' }} />
                Learning Preferences
              </Typography>
              <Button
                startIcon={editing ? <Save /> : <Edit />}
                onClick={editing ? handleSavePreferences : () => setEditing(true)}
                variant={editing ? "contained" : "outlined"}
                disabled={updatePreferencesMutation.isLoading}
              >
                {editing ? 'Save Changes' : 'Edit Preferences'}
              </Button>
            </Box>

            {editing && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Updating your preferences will improve future course recommendations
              </Alert>
            )}

            {/* Preferred Topics */}
            <Box mb={3}>
              <Typography variant="subtitle1" gutterBottom>
                📚 Preferred Topics
              </Typography>
              <Box display="flex" gap={0.5} flexWrap="wrap" mb={2}>
                {preferences.preferred_topics.map((topic) => (
                  <Chip
                    key={topic}
                    label={topic}
                    onDelete={editing ? () => handleRemoveTopic(topic) : undefined}
                    color="primary"
                    variant={editing ? "filled" : "outlined"}
                  />
                ))}
              </Box>
              {editing && (
                <Box display="flex" gap={1}>
                  <TextField
                    size="small"
                    label="Add Topic"
                    value={topicInput}
                    onChange={(e) => setTopicInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTopic()}
                    placeholder="e.g., python, machine learning"
                  />
                  <Button
                    onClick={handleAddTopic}
                    disabled={!topicInput.trim()}
                  >
                    Add
                  </Button>
                </Box>
              )}
            </Box>

            <Grid container spacing={2}>
              {/* Difficulty Level */}
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty Level</InputLabel>
                  <Select
                    value={preferences.difficulty_level}
                    onChange={(e) => setPreferences(prev => ({ ...prev, difficulty_level: e.target.value }))}
                    label="Difficulty Level"
                    disabled={!editing}
                  >
                    <MenuItem value="">Not specified</MenuItem>
                    <MenuItem value="beginner">Beginner</MenuItem>
                    <MenuItem value="intermediate">Intermediate</MenuItem>
                    <MenuItem value="advanced">Advanced</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Learning Style */}
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Learning Style</InputLabel>
                  <Select
                    value={preferences.learning_style}
                    onChange={(e) => setPreferences(prev => ({ ...prev, learning_style: e.target.value }))}
                    label="Learning Style"
                    disabled={!editing}
                  >
                    <MenuItem value="">Not specified</MenuItem>
                    <MenuItem value="hands-on">Hands-on</MenuItem>
                    <MenuItem value="visual">Visual</MenuItem>
                    <MenuItem value="theoretical">Theoretical</MenuItem>
                    <MenuItem value="interactive">Interactive</MenuItem>
                    <MenuItem value="project-based">Project-based</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Time Commitment */}
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Time Commitment</InputLabel>
                  <Select
                    value={preferences.time_commitment}
                    onChange={(e) => setPreferences(prev => ({ ...prev, time_commitment: e.target.value }))}
                    label="Time Commitment"
                    disabled={!editing}
                  >
                    <MenuItem value="">Not specified</MenuItem>
                    <MenuItem value="1-2 hours/week">1-2 hours/week</MenuItem>
                    <MenuItem value="3-5 hours/week">3-5 hours/week</MenuItem>
                    <MenuItem value="6-10 hours/week">6-10 hours/week</MenuItem>
                    <MenuItem value="10+ hours/week">10+ hours/week</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {editing && (
              <Box mt={2} display="flex" gap={1}>
                <Button onClick={handleCancelEdit}>Cancel</Button>
              </Box>
            )}
          </Paper>

          {/* Feedback History */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <History sx={{ mr: 1, verticalAlign: 'middle' }} />
              Recent Feedback
            </Typography>
            
            {feedbackLoading && <CircularProgress />}
            
            {feedbackHistory && feedbackHistory.length > 0 ? (
              <List>
                {feedbackHistory.slice(0, 5).map((feedback) => (
                  <ListItem key={feedback.id} divider>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle2">
                            Course: {feedback.course_id}
                          </Typography>
                          <Rating value={feedback.rating} size="small" readOnly />
                        </Box>
                      }
                      secondary={
                        <Box>
                          {feedback.feedback_text && (
                            <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                              "{feedback.feedback_text}"
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary">
                            {new Date(feedback.created_at).toLocaleDateString()} • 
                            Style: {feedback.learning_style || 'Not specified'} • 
                            Difficulty: {feedback.difficulty_preference || 'Not specified'}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1}>
                        <Button
                          size="small"
                          onClick={() => navigate(`/courses/${feedback.course_id}`)}
                        >
                          View Course
                        </Button>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteFeedback(feedback.id)}
                          title="Delete Review"
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No feedback submitted yet. Rate some courses to see your history here!
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Analytics Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Learning Stats */}
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              📊 Learning Statistics
            </Typography>
            
            {analytics ? (
              <>
                <Box display="flex" justifyContent="space-between" mb={2}>
                  <Typography variant="body2">Total Feedback:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {analytics.feedback_summary?.length || 0}
                  </Typography>
                </Box>
                
                <Box display="flex" justifyContent="space-between" mb={2}>
                  <Typography variant="body2">Total Interactions:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {analytics.total_interactions || 0}
                  </Typography>
                </Box>

                {analytics.interaction_summary?.map((interaction) => (
                  <Box key={interaction.interaction_type} display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {interaction.interaction_type}:
                    </Typography>
                    <Typography variant="body2">{interaction.count}</Typography>
                  </Box>
                ))}

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle2" gutterBottom>Top Interests:</Typography>
                {analytics.preferred_topics?.slice(0, 5).map(([topic, count]) => (
                  <Box key={topic} display="flex" justifyContent="space-between" mb={1}>
                    <Chip label={topic} size="small" color="primary" variant="outlined" />
                    <Typography variant="caption">{count}</Typography>
                  </Box>
                ))}
              </>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Start interacting with courses to see your learning statistics!
              </Typography>
            )}
          </Paper>

          {/* Account Info */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <Box mb={2}>
              <Typography variant="body2" color="text.secondary">Username:</Typography>
              <Typography variant="body1" fontWeight="bold">{user?.username}</Typography>
            </Box>
            {user?.email && (
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">Email:</Typography>
                <Typography variant="body1">{user.email}</Typography>
              </Box>
            )}
            <Box mb={2}>
              <Typography variant="body2" color="text.secondary">Vector Search:</Typography>
              <Chip 
                label={analytics?.vector_search_enabled ? "Enabled" : "Disabled"} 
                color={analytics?.vector_search_enabled ? "success" : "warning"}
                size="small"
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Profile; 