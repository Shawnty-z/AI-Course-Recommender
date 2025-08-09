import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Rating,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert
} from '@mui/material';
import { Star } from '@mui/icons-material';
import axios from 'axios';

const CourseRatingDialog = ({ open, onClose, course, onRatingSubmitted }) => {
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [learningStyle, setLearningStyle] = useState('');
  const [difficultyPreference, setDifficultyPreference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;
    
    setSubmitting(true);
    try {
      await axios.post('/api/feedback/', {
        course_id: course.id,
        rating: rating,
        feedback_text: feedbackText,
        learning_style: learningStyle,
        difficulty_preference: difficultyPreference
      });
      
      setSuccess(true);
      setTimeout(() => {
        onClose();
        onRatingSubmitted();
        resetForm();
      }, 1500);
      
    } catch (error) {
      console.error('Failed to submit rating:', error);
    }
    setSubmitting(false);
  };

  const resetForm = () => {
    setRating(0);
    setFeedbackText('');
    setLearningStyle('');
    setDifficultyPreference('');
    setSuccess(false);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h6">Rate Course</Typography>
        <Typography variant="body2" color="text.secondary">
          {course?.title}
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        {success ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            Rating submitted! Recommendations will improve based on your feedback.
          </Alert>
        ) : (
          <>
            <Box sx={{ mb: 3, textAlign: 'center' }}>
              <Typography component="legend" gutterBottom>
                Overall Rating
              </Typography>
              <Rating
                name="course-rating"
                value={rating}
                onChange={(event, newValue) => setRating(newValue)}
                size="large"
                icon={<Star fontSize="inherit" />}
              />
            </Box>

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Your Feedback (Optional)"
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="What did you think of this course?"
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

            <FormControl fullWidth sx={{ mb: 2 }}>
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
          </>
        )}
      </DialogContent>

      {!success && (
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={rating === 0 || submitting}
          >
            {submitting ? 'Submitting...' : 'Submit Rating'}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default CourseRatingDialog; 