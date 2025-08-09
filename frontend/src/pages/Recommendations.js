import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  TextField,
  Alert,
  CircularProgress,
  InputAdornment,
  LinearProgress
} from '@mui/material';
import {
  Psychology,
  Search,
  Star,
  PlayCircleOutline,
  Refresh,
  RateReview
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import AIExplanationCard from '../components/recommendations/AIExplanation';

const Recommendations = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State management
  const [query, setQuery] = useState('');

  const [queryRecommendations, setQueryRecommendations] = useState(null);
  const [searching, setSearching] = useState(false);

  // Fetch default recommendations
  const { data: defaultRecommendations, isLoading, refetch } = useQuery(
    ['recommendations', user?.id],
    async () => {
      const response = await axios.get(`/api/recommendations/${user.id}?max_results=8`);
      return response.data;
    },
    { enabled: !!user }
  );

  // Query-based recommendations mutation
  const queryMutation = useMutation(
    async (searchQuery) => {
      // Pure semantic search (more accurate for specific queries)
      const response = await axios.post(
        `/api/recommendations/${user.id}/semantic-search?query=${encodeURIComponent(searchQuery)}&max_results=8`
      );
      return {
        courses: response.data,
        reasoning: `🧠 AI Semantic Analysis: Found ${response.data.length} courses matching "${searchQuery}" using pure vector similarity. Results ranked by semantic relevance.`,
        user_context: null,
        query_processed: searchQuery
      };
    },
    {
      onSuccess: (data) => {
        setQueryRecommendations(data);
        setSearching(false);
      },
      onError: () => {
        setSearching(false);
      }
    }
  );

  // Handle query search
  const handleQuerySearch = () => {
    if (!query.trim()) return;
    setSearching(true);
    queryMutation.mutate(query.trim());
  };

  // Clear query results
  const clearQuery = () => {
    setQueryRecommendations(null);
    setQuery('');
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

  // Course interaction handler
  const handleCourseClick = (courseId) => {
    // Log interaction
    axios.post(`/api/courses/${courseId}/interact`, {
      course_id: courseId,
      interaction_type: 'viewed'
    }).catch(err => console.error('Failed to log interaction:', err));
    
    navigate(`/courses/${courseId}`);
  };

  // Render course card
  const renderCourseCard = (course, index) => (
    <Grid item xs={12} sm={6} md={4} lg={3} key={course.id}>
      <Card sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        border: index < 3 ? '2px solid' : '1px solid',
        borderColor: index < 3 ? 'primary.light' : 'divider'
      }}>
        <CardContent sx={{ flexGrow: 1 }}>
          {index < 3 && (
            <Chip 
              label={`#${index + 1} Recommended`}
              color="primary"
              size="small"
              sx={{ mb: 1 }}
            />
          )}
          
          <Typography variant="h6" gutterBottom noWrap>
            {course.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, height: 60, overflow: 'hidden' }}>
            {course.description.substring(0, 120)}...
          </Typography>
          
          <Box display="flex" gap={0.5} flexWrap="wrap" mb={2}>
            {course.topics.slice(0, 3).map((topic) => (
              <Chip key={topic} label={topic} size="small" variant="outlined" />
            ))}
          </Box>

          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
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
            <Box>
              <Typography variant="caption" color="primary" gutterBottom display="block">
                AI Match: {Math.round((course.similarity_score || 0) * 100)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(course.similarity_score || 0) * 100}
                sx={{ height: 6, borderRadius: 3 }}
              />
            </Box>
          )}
        </CardContent>
        
        <CardActions>
          <Button 
            size="small" 
            startIcon={<PlayCircleOutline />}
            onClick={() => handleCourseClick(course.id)}
          >
            View Course
          </Button>
        </CardActions>
      </Card>
    </Grid>
  );

  const currentRecommendations = queryRecommendations || defaultRecommendations;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        🔍 AI Semantic Search
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Search for courses using natural language. For personalized recommendations, visit your Dashboard.
      </Typography>

      {/* Query-Based Recommendations */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          💬 Search for Courses
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Try natural language queries like "I want to learn web development" or "machine learning for beginners"
        </Typography>
        
        {/* AI Semantic Search Info */}
        <Box sx={{ mb: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
          <Typography variant="body2" color="primary.main" sx={{ fontWeight: 'medium' }}>
            🎯 Pure Semantic Search
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Direct vector matching for accurate query-based results. For personalized recommendations, check your Dashboard.
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <TextField
            fullWidth
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your learning goals..."
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Psychology color="primary" />
                </InputAdornment>
              ),
            }}
            onKeyPress={(e) => e.key === 'Enter' && handleQuerySearch()}
          />
          <Button
            variant="contained"
            startIcon={searching ? <CircularProgress size={20} /> : <Search />}
            onClick={handleQuerySearch}
            disabled={!query.trim() || searching}
          >
            Get AI Recommendations
          </Button>
          {queryRecommendations && (
            <Button
              variant="outlined"
              onClick={clearQuery}
              startIcon={<Refresh />}
            >
              Reset
            </Button>
          )}
        </Box>
      </Paper>

      {/* Loading State */}
      {(isLoading || searching) && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Recommendations Results */}
      {currentRecommendations && !isLoading && !searching && (
        <>
          {/* Query Results Info */}
          {queryRecommendations && (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2">
                🧠 AI analyzed your query "{query}" and found {currentRecommendations.courses?.length || 0} personalized recommendations
              </Typography>
            </Alert>
          )}

          {/* AI Reasoning */}
          {currentRecommendations.reasoning && (
            <AIExplanationCard
              reasoning={currentRecommendations.reasoning}
              userContext={currentRecommendations.user_context}
              courses={currentRecommendations.courses}
              compact={false}
            />
          )}

          {/* Courses Grid */}
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            {queryRecommendations ? '🔍 Search Results' : '⭐ Your Personalized Recommendations'}
          </Typography>
          
          <Grid container spacing={3}>
            {currentRecommendations.courses?.map((course, index) => renderCourseCard(course, index))}
          </Grid>

          {currentRecommendations.courses?.length === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
              <Typography variant="h6" color="text.secondary">
                No recommendations found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try a different query or update your preferences in your profile
              </Typography>
            </Paper>
          )}
        </>
      )}

      {/* No Default Recommendations */}
      {!currentRecommendations && !isLoading && !searching && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Psychology sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No recommendations yet
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Try describing what you want to learn above, or rate some courses to get personalized recommendations!
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/courses')}
            startIcon={<RateReview />}
          >
            Browse Courses
          </Button>
        </Paper>
      )}
    </Container>
  );
};

export default Recommendations; 