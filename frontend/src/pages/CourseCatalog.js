import React, { useState, useEffect } from 'react';
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  CircularProgress,
  Alert,
  Pagination
} from '@mui/material';
import {
  Search,
  Star,
  PlayCircleOutline,
  FilterList,
  Psychology
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const CourseCatalog = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // State management
  const [searchQuery, setSearchQuery] = useState('');
  const [semanticQuery, setSemanticQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [page, setPage] = useState(1);
  const [searchType, setSearchType] = useState('text'); // 'text' or 'semantic'
  const [searchResults, setSearchResults] = useState(null);
  const [semanticResults, setSemanticResults] = useState(null);
  const [searching, setSearching] = useState(false);

  const coursesPerPage = 12;

  // Fetch courses with filters
  const { data: coursesData, isLoading, error } = useQuery(
    ['courses', page, difficultyFilter, topicFilter],
    async () => {
      const params = new URLSearchParams({
        limit: coursesPerPage.toString(),
        offset: ((page - 1) * coursesPerPage).toString()
      });
      
      if (difficultyFilter) params.append('difficulty', difficultyFilter);
      if (topicFilter) params.append('topics', topicFilter);
      
      const response = await axios.get(`/api/courses/?${params}`);
      return response.data;
    }
  );

  // Extract courses and pagination data
  const courses = coursesData?.courses || [];
  const pagination = coursesData?.pagination || { total: 0, total_pages: 1 };

  // Calculate total pages based on actual data
  const totalPages = pagination.total_pages;

  // Handle text search
  const handleTextSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    setSearchType('text');
    try {
      const response = await axios.post('/api/courses/search', {
        query: searchQuery,
        filters: {
          topics: topicFilter ? [topicFilter] : null,
          difficulty: difficultyFilter || null,
          min_rating: null
        },
        limit: 20
      });
      setSearchResults(response.data);
      setSemanticResults(null);
    } catch (error) {
      console.error('Search failed:', error);
    }
    setSearching(false);
  };

  // Handle semantic search
  const handleSemanticSearch = async () => {
    if (!semanticQuery.trim() || !user) return;
    
    setSearching(true);
    setSearchType('semantic');
    try {
      const response = await axios.post(
        `/api/recommendations/${user.id}/semantic-search?query=${encodeURIComponent(semanticQuery)}&max_results=15`
      );
      setSemanticResults(response.data);
      setSearchResults(null);
    } catch (error) {
      console.error('Semantic search failed:', error);
    }
    setSearching(false);
  };

  // Clear search results
  const clearSearch = () => {
    setSearchResults(null);
    setSemanticResults(null);
    setSearchQuery('');
    setSemanticQuery('');
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
  const renderCourseCard = (course) => (
    <Grid item xs={12} sm={6} md={4} key={course.id}>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
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
              <Typography variant="caption" color="primary">
                AI Match: {Math.round((course.similarity_score || 0) * 100)}%
              </Typography>
            </Box>
          )}
          
          <Typography variant="caption" color="text.secondary" display="block">
            {course.duration} • {course.format}
          </Typography>
        </CardContent>
        
        <CardActions>
          <Button 
            size="small" 
            startIcon={<PlayCircleOutline />}
            onClick={() => handleCourseClick(course.id)}
          >
            View Details
          </Button>
        </CardActions>
      </Card>
    </Grid>
  );

  const displayedCourses = searchResults || semanticResults || courses || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Course Catalog
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Explore our comprehensive collection of courses designed to help you master new skills
        </Typography>
        {!searchResults && !semanticResults && pagination.total > 0 && (
          <Typography variant="body2" color="text.secondary">
            Showing {courses.length} of {pagination.total} courses
            {totalPages > 1 && ` • Page ${page} of ${totalPages}`}
          </Typography>
        )}
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          {/* Text Search */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search courses by title or description..."
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              onKeyPress={(e) => e.key === 'Enter' && handleTextSearch()}
            />
            <Button
              variant="outlined"
              onClick={handleTextSearch}
              disabled={!searchQuery.trim() || searching}
              sx={{ mt: 1 }}
            >
              Text Search
            </Button>
          </Grid>

          {/* Semantic Search */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              placeholder="Describe what you want to learn (AI-powered)..."
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Psychology color="primary" />
                  </InputAdornment>
                ),
              }}
              onKeyPress={(e) => e.key === 'Enter' && handleSemanticSearch()}
            />
            <Button
              variant="contained"
              onClick={handleSemanticSearch}
              disabled={!semanticQuery.trim() || searching || !user}
              sx={{ mt: 1 }}
              startIcon={searching ? <CircularProgress size={16} /> : <Psychology />}
            >
              AI Search
            </Button>
          </Grid>

          {/* Filters */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Difficulty</InputLabel>
              <Select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                label="Difficulty"
              >
                <MenuItem value="">All Levels</MenuItem>
                <MenuItem value="beginner">Beginner</MenuItem>
                <MenuItem value="intermediate">Intermediate</MenuItem>
                <MenuItem value="advanced">Advanced</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Topic Filter"
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
              placeholder="e.g., python, react"
            />
          </Grid>

          <Grid item xs={12} md={3}>
            {(searchResults || semanticResults) && (
              <Button variant="outlined" onClick={clearSearch} startIcon={<FilterList />}>
                Clear Search
              </Button>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Search Results Info */}
      {(searchResults || semanticResults) && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {searchType === 'semantic' ? '🧠 AI Semantic Search Results' : '🔍 Text Search Results'} 
            • Found {displayedCourses.length} courses
            {searchType === 'semantic' && ' • Results ranked by semantic similarity'}
          </Typography>
        </Alert>
      )}

      {/* Loading State */}
      {(isLoading || searching) && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load courses. Please try again.
        </Alert>
      )}

      {/* Courses Grid */}
      {!isLoading && !searching && (
        <>
          <Grid container spacing={3}>
            {displayedCourses.map(renderCourseCard)}
          </Grid>

          {displayedCourses.length === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
              <Typography variant="h6" color="text.secondary">
                {searchResults || semanticResults ? 'No courses found' : 'No courses available'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchResults || semanticResults 
                  ? 'Try adjusting your search terms or filters'
                  : 'Please check back later for new courses'
                }
              </Typography>
            </Paper>
          )}

          {/* Pagination for regular course browsing */}
          {!searchResults && !semanticResults && totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={4}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}
    </Container>
  );
};

export default CourseCatalog; 