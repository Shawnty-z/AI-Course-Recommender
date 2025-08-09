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
  Rating,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Star,
  PlayCircleOutline,
  RateReview,
  Recommend,
  AccessTime,
  School,
  CheckCircle,
  Delete,
  Edit,
  Warning
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const CourseDetails = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  // State management
  const [ratingDialogOpen, setRatingDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [newRating, setNewRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [learningStyle, setLearningStyle] = useState('');
  const [difficultyPreference, setDifficultyPreference] = useState('');
  const [enrolled, setEnrolled] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Fetch course details
  const { data: course, isLoading: courseLoading, error: courseError } = useQuery(
    ['course', courseId],
    async () => {
      const response = await axios.get(`/api/courses/${courseId}`);
      return response.data;
    }
  );

  // Fetch user's previous feedback for this course
  const { data: existingFeedback } = useQuery(
    ['feedback', courseId, user?.id],
    async () => {
      const response = await axios.get(`/api/feedback/course/${courseId}`);
      return response.data;
    },
    { enabled: !!user && !!courseId }
  );

  // Fetch similar courses
  const { data: similarCourses, isLoading: similarLoading } = useQuery(
    ['similar-courses', courseId, user?.id],
    async () => {
      const response = await axios.post(`/api/recommendations/${user.id}/similar`, {
        course_id: courseId,
        max_results: 4
      });
      return response.data;
    },
    { enabled: !!user && !!courseId }
  );

  // Fetch user interactions
  const { data: interactions } = useQuery(
    ['interactions', courseId, user?.id],
    async () => {
      const response = await axios.get(`/api/courses/${courseId}/interactions`);
      return response.data;
    },
    {
      enabled: !!user && !!courseId,
      onSuccess: (data) => {
        const isEnrolled = data.some(interaction => 
          interaction.interaction_type === 'enrolled' && 
          !data.some(later => later.interaction_type === 'dropped' && later.created_at > interaction.created_at)
        );
        setEnrolled(isEnrolled);
      }
    }
  );

  // Rating submission mutation
  const ratingMutation = useMutation(
    async (ratingData) => {
      return axios.post('/api/feedback/', ratingData);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['feedback', courseId]);
        queryClient.invalidateQueries(['recommendations', user.id]);
        setRatingDialogOpen(false);
        resetRatingForm();
      }
    }
  );

  // Enrollment mutation
  const enrollmentMutation = useMutation(
    async (interactionType) => {
      return axios.post(`/api/courses/${courseId}/interact`, {
        course_id: courseId,
        interaction_type: interactionType
      });
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['interactions', courseId]);
        setEnrolled(!enrolled);
      }
    }
  );

  // Delete review mutation
  const deleteReviewMutation = useMutation(
    async (feedbackId) => {
      return axios.delete(`/api/feedback/${feedbackId}`);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['feedback', courseId]);
        queryClient.invalidateQueries(['recommendations', user.id]);
        setDeleteDialogOpen(false);
        setDeleting(false);
      },
      onError: (error) => {
        console.error('Failed to delete review:', error);
        setDeleting(false);
      }
    }
  );

  // Handle review deletion
  const handleDeleteReview = () => {
    if (!userRating) return;
    setDeleting(true);
    deleteReviewMutation.mutate(userRating.id);
  };

  // Reset rating form
  const resetRatingForm = () => {
    setNewRating(0);
    setFeedbackText('');
    setLearningStyle('');
    setDifficultyPreference('');
  };

  // Submit rating
  const handleSubmitRating = () => {
    if (newRating === 0) return;
    
    ratingMutation.mutate({
      course_id: courseId,
      rating: newRating,
      feedback_text: feedbackText,
      learning_style: learningStyle,
      difficulty_preference: difficultyPreference
    });
  };

  // Handle enrollment toggle
  const handleEnrollmentToggle = () => {
    const interactionType = enrolled ? 'dropped' : 'enrolled';
    enrollmentMutation.mutate(interactionType);
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

  if (courseLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (courseError || !course) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Course not found or failed to load.
        </Alert>
      </Container>
    );
  }

  const userRating = existingFeedback?.[0];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={3}>
        {/* Main Course Info */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
              {course.title}
            </Typography>
            
            <Box display="flex" gap={1} alignItems="center" mb={2}>
              <Chip 
                label={course.difficulty} 
                color={getDifficultyColor(course.difficulty)}
                size="small"
              />
              <Box display="flex" alignItems="center" gap={0.5}>
                <Star sx={{ color: 'gold', fontSize: 18 }} />
                <Typography variant="body1">{course.rating}</Typography>
              </Box>
              <Chip 
                icon={<AccessTime />} 
                label={course.duration} 
                variant="outlined"
                size="small"
              />
              <Chip 
                icon={<School />} 
                label={course.format} 
                variant="outlined"
                size="small"
              />
            </Box>

            <Typography variant="body1" paragraph sx={{ lineHeight: 1.7 }}>
              {course.description}
            </Typography>

            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                📚 Topics Covered
              </Typography>
              <Box display="flex" gap={0.5} flexWrap="wrap">
                {course.topics.map((topic) => (
                  <Chip key={topic} label={topic} variant="outlined" />
                ))}
              </Box>
            </Box>

            {/* Action Buttons */}
            <Box display="flex" gap={2}>
              <Button
                variant={enrolled ? "outlined" : "contained"}
                size="large"
                startIcon={enrolled ? <CheckCircle /> : <PlayCircleOutline />}
                onClick={handleEnrollmentToggle}
                disabled={enrollmentMutation.isLoading}
              >
                {enrolled ? 'Enrolled' : 'Enroll Now'}
              </Button>
              
              <Button
                variant="outlined"
                size="large"
                startIcon={<RateReview />}
                onClick={() => setRatingDialogOpen(true)}
                disabled={!user}
              >
                Rate Course
              </Button>
            </Box>
          </Paper>

          {/* User's Previous Rating */}
          {userRating && (
            <Paper sx={{ p: 3, mt: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  📝 Your Review
                </Typography>
                <Box>
                  <Tooltip title="Edit Review">
                    <IconButton 
                      size="small" 
                      onClick={() => {
                        setNewRating(userRating.rating);
                        setFeedbackText(userRating.feedback_text || '');
                        setLearningStyle(userRating.learning_style || '');
                        setDifficultyPreference(userRating.difficulty_preference || '');
                        setRatingDialogOpen(true);
                      }}
                      sx={{ mr: 1 }}
                    >
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete Review">
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => setDeleteDialogOpen(true)}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Rating value={userRating.rating} readOnly />
                <Typography variant="body2" color="text.secondary">
                  Rated {userRating.rating}/5 stars
                </Typography>
              </Box>
              {userRating.feedback_text && (
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  "{userRating.feedback_text}"
                </Typography>
              )}
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                {userRating.learning_style && `Learning Style: ${userRating.learning_style} • `}
                {userRating.difficulty_preference && `Difficulty: ${userRating.difficulty_preference} • `}
                Submitted: {new Date(userRating.created_at).toLocaleDateString()}
              </Typography>
            </Paper>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Similar Courses */}
          {similarCourses && similarCourses.length > 0 && (
            <Paper sx={{ p: 3, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                🎯 Similar Courses
              </Typography>
              {similarLoading && <CircularProgress size={20} />}
              {similarCourses.map((similarCourse) => (
                <Card key={similarCourse.id} sx={{ mb: 2, cursor: 'pointer' }}
                  onClick={() => navigate(`/courses/${similarCourse.id}`)}>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      {similarCourse.title}
                    </Typography>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Chip 
                        label={similarCourse.difficulty} 
                        size="small"
                        color={getDifficultyColor(similarCourse.difficulty)}
                      />
                      {similarCourse.similarity_score && (
                        <Typography variant="caption" color="primary">
                          {Math.round(similarCourse.similarity_score * 100)}% match
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Paper>
          )}

          {/* Course Stats */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📊 Course Details
            </Typography>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">Duration:</Typography>
              <Typography variant="body2" fontWeight="bold">{course.duration}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">Format:</Typography>
              <Typography variant="body2" fontWeight="bold">{course.format}</Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2">Difficulty:</Typography>
              <Chip 
                label={course.difficulty} 
                size="small"
                color={getDifficultyColor(course.difficulty)}
              />
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2">Average Rating:</Typography>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Star sx={{ color: 'gold', fontSize: 16 }} />
                <Typography variant="body2" fontWeight="bold">{course.rating}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Rating Dialog */}
      <Dialog open={ratingDialogOpen} onClose={() => setRatingDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rate This Course</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Typography component="legend" gutterBottom>
              Overall Rating
            </Typography>
            <Rating
              name="course-rating"
              value={newRating}
              onChange={(event, newValue) => setNewRating(newValue)}
              size="large"
            />
          </Box>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Your Feedback (Optional)"
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Share your thoughts about this course..."
            sx={{ mb: 2 }}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Learning Style Preference</InputLabel>
            <Select
              value={learningStyle}
              onChange={(e) => setLearningStyle(e.target.value)}
              label="Learning Style Preference"
            >
              <MenuItem value="hands-on">Hands-on</MenuItem>
              <MenuItem value="visual">Visual</MenuItem>
              <MenuItem value="theoretical">Theoretical</MenuItem>
              <MenuItem value="interactive">Interactive</MenuItem>
              <MenuItem value="project-based">Project-based</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Difficulty Preference</InputLabel>
            <Select
              value={difficultyPreference}
              onChange={(e) => setDifficultyPreference(e.target.value)}
              label="Difficulty Preference"
            >
              <MenuItem value="beginner">Beginner</MenuItem>
              <MenuItem value="intermediate">Intermediate</MenuItem>
              <MenuItem value="advanced">Advanced</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRatingDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmitRating}
            variant="contained"
            disabled={newRating === 0 || ratingMutation.isLoading}
          >
            {ratingMutation.isLoading ? 'Submitting...' : 'Submit Rating'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Warning color="warning" />
          Delete Review
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete your review for this course? This action cannot be undone.
          </Typography>
          {userRating && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <Rating value={userRating.rating} size="small" readOnly />
                <Typography variant="body2">
                  {userRating.rating}/5 stars
                </Typography>
              </Box>
              {userRating.feedback_text && (
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  "{userRating.feedback_text}"
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteReview}
            color="error"
            variant="contained"
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <Delete />}
          >
            {deleting ? 'Deleting...' : 'Delete Review'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CourseDetails; 