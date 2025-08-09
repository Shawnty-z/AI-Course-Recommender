import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  Star,
  PlayCircleOutline,
  CheckCircle
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AIExplanationCard from '../components/recommendations/AIExplanation';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // State to track enrolled courses
  const [enrolledCourses, setEnrolledCourses] = useState(new Set());
  
  const { data: recommendations, isLoading: recommendationsLoading, error: recommendationsError, refetch: refetchRecommendations } = useQuery(
    ['recommendations', user?.id],
    async () => {
      const response = await axios.get(`/api/recommendations/${user.id}?max_results=4`);
      return response.data;
    },
    { 
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes - data stays fresh for 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes - cache for 10 minutes
      refetchOnWindowFocus: false, // Don't refetch when window regains focus
      refetchOnMount: false, // Don't refetch on component mount if data exists
      refetchOnReconnect: false // Don't refetch on internet reconnect
    }
  );

  const { data: recentActivity, isLoading: activityLoading } = useQuery(
    ['user-activity', user?.id],
    async () => {
      const response = await axios.get(`/api/recommendations/${user.id}/history`);
      return response.data;
    },
    { 
      enabled: !!user,
      staleTime: 10 * 60 * 1000, // 10 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false
    }
  );

  const { data: preferences } = useQuery(
    ['user-preferences', user?.id],
    async () => {
      const response = await axios.get('/api/feedback/preferences');
      return response.data;
    },
    { 
      enabled: !!user,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false
    }
  );

  // Load initial enrollment status on component mount
  useEffect(() => {
    const loadEnrollmentStatus = async () => {
      if (user?.id) {
        try {
          // Get user's interactions to see which courses they're enrolled in
          const response = await axios.get(`/api/recommendations/${user.id}/history`);
          const interactions = response.data.interaction_summary || [];
          
          // Find enrolled courses from interaction history
          const enrolled = new Set();
          interactions.forEach(interaction => {
            if (interaction.interaction_type === 'enrolled') {
              enrolled.add(interaction.course_id);
            }
          });
          
          setEnrolledCourses(enrolled);
        } catch (error) {
          console.error('Failed to load enrollment status:', error);
        }
      }
    };

    loadEnrollmentStatus();
  }, [user?.id]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return 'success';
      case 'intermediate': return 'warning';
      case 'advanced': return 'error';
      default: return 'default';
    }
  };

  const handleCourseInteraction = async (courseId, interactionType) => {
    try {
      await axios.post(`/api/courses/${courseId}/interact`, {
        course_id: courseId,
        interaction_type: interactionType
      });
    } catch (error) {
      console.error('Failed to log interaction:', error);
    }
  };

  const handleEnrollToggle = async (courseId) => {
    const isCurrentlyEnrolled = enrolledCourses.has(courseId);
    const newInteractionType = isCurrentlyEnrolled ? 'dropped' : 'enrolled';
    
    try {
      // Log the interaction with the backend
      await handleCourseInteraction(courseId, newInteractionType);
      
      // Update local state
      const newEnrolledCourses = new Set(enrolledCourses);
      if (isCurrentlyEnrolled) {
        newEnrolledCourses.delete(courseId);
      } else {
        newEnrolledCourses.add(courseId);
      }
      setEnrolledCourses(newEnrolledCourses);
      
    } catch (error) {
      console.error('Failed to toggle enrollment:', error);
    }
  };

  if (recommendationsLoading || activityLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <Box textAlign="center">
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Loading your personalized recommendations...
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              This may take a few seconds on first load
            </Typography>
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Welcome Section */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.username}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Here's your personalized learning dashboard with course recommendations tailored just for you.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Recommendations Section */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
              <Typography variant="h6" gutterBottom>
                🎯 Recommended for You
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/recommendations')}
              >
                View All
              </Button>
            </Box>
            
            {recommendationsError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                Failed to load recommendations. Please try again later.
              </Alert>
            )}

            {/* AI Reasoning Display */}
            {recommendations?.reasoning && (
              <AIExplanationCard 
                reasoning={recommendations.reasoning}
                userContext={recommendations.user_context}
                courses={recommendations.courses}
                compact={true}
              />
            )}

            <Grid container spacing={2}>
              {recommendations?.courses?.slice(0, 4).map((course) => {
                const isEnrolled = enrolledCourses.has(course.id);
                
                return (
                  <Grid item xs={12} sm={6} key={course.id}>
                    <Card sx={{ 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column',
                      opacity: isEnrolled ? 0.7 : 1,
                      transition: 'opacity 0.3s ease-in-out'
                    }}>
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom noWrap>
                          {course.title}
                          {isEnrolled && (
                            <CheckCircle 
                              sx={{ 
                                ml: 1, 
                                color: 'success.main', 
                                fontSize: 20,
                                verticalAlign: 'middle'
                              }} 
                            />
                          )}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {course.description.substring(0, 120)}...
                        </Typography>
                        
                        <Box display="flex" gap={0.5} flexWrap="wrap" mb={2}>
                          {course.topics.slice(0, 3).map((topic) => (
                            <Chip 
                              key={topic} 
                              label={topic} 
                              size="small" 
                              variant="outlined"
                            />
                          ))}
                        </Box>

                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Chip 
                            label={course.difficulty} 
                            size="small"
                            color={getDifficultyColor(course.difficulty)}
                          />
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <Star sx={{ color: 'gold', fontSize: 16 }} />
                            <Typography variant="body2">{course.rating}</Typography>
                          </Box>
                        </Box>

                        {course.similarity_score && (
                          <Box mt={1}>
                            <Typography variant="caption" color="text.secondary">
                              Match: {Math.round(course.similarity_score * 100)}%
                            </Typography>
                            <LinearProgress 
                              variant="determinate" 
                              value={course.similarity_score * 100}
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        )}
                      </CardContent>
                      
                      <CardActions>
                        <Button 
                          size="small" 
                          startIcon={<PlayCircleOutline />}
                          onClick={() => {
                            handleCourseInteraction(course.id, 'viewed');
                            navigate(`/courses/${course.id}`);
                          }}
                        >
                          View Course
                        </Button>
                        <Button 
                          size="small" 
                          variant={isEnrolled ? "outlined" : "contained"}
                          startIcon={isEnrolled ? <CheckCircle /> : null}
                          onClick={() => handleEnrollToggle(course.id)}
                          sx={{
                            opacity: isEnrolled ? 0.2 : 1,
                            transition: 'opacity 0.3s ease-in-out',
                            '&:hover': {
                              opacity: isEnrolled ? 0.4 : 1,
                            }
                          }}
                        >
                          {isEnrolled ? 'Enrolled' : 'Enroll'}
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Grid>

        {/* Learning Progress & Preferences */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            {/* User Preferences */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  🎯 Your Learning Profile
                </Typography>
                
                {preferences?.preferred_topics?.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Preferred Topics:
                    </Typography>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {preferences.preferred_topics.map((topic) => (
                        <Chip key={topic} label={topic} size="small" color="primary" />
                      ))}
                    </Box>
                  </Box>
                )}

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Learning Style:
                  </Typography>
                  <Chip 
                    label={preferences?.learning_style || 'Not set'} 
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Difficulty Level:
                  </Typography>
                  <Chip 
                    label={preferences?.difficulty_level || 'Not set'} 
                    size="small"
                    color={getDifficultyColor(preferences?.difficulty_level)}
                  />
                </Box>
              </Paper>
            </Grid>

            {/* Recent Activity Summary */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📊 Recent Activity
                </Typography>
                
                {recentActivity?.interaction_summary?.map((interaction) => (
                  <Box key={interaction.interaction_type} display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {interaction.interaction_type}:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {interaction.count}
                    </Typography>
                  </Box>
                ))}
                
                {recentActivity?.preferred_topics?.slice(0, 5).map(([topic, count]) => (
                  <Box key={topic} mb={1}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">{topic}</Typography>
                      <Typography variant="body2">{count}</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(count / Math.max(...recentActivity.preferred_topics.map(([,c]) => c))) * 100} 
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                ))}
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard; 