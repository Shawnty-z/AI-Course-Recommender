import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip, 
  Collapse, 
  IconButton, 
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { 
  Psychology, 
  ExpandMore, 
  ExpandLess, 
  LightbulbOutlined, 
  TrendingUp,
  Star,
  CheckCircle,
  PlayCircleOutline
} from '@mui/icons-material';

const AIExplanationCard = ({ reasoning, userContext, courses, compact = false }) => {
  const [expanded, setExpanded] = useState(false);

  // Parse and format the reasoning text
  const parseReasoning = (text) => {
    if (!text) return { summary: '', sections: [] };

    // Split into sentences and group into logical sections
    const sentences = text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 10);
    
    // Extract course names (text between ** **)
    const courseNames = text.match(/\*\*(.*?)\*\*/g)?.map(match => match.replace(/\*\*/g, '')) || [];
    
    // Create summary (first 2 sentences)
    const summary = sentences.slice(0, 2).join('. ') + '.';
    
    // Group remaining sentences into sections
    const sections = [];
    let currentSection = [];
    
    sentences.slice(2).forEach(sentence => {
      if (sentence.includes('recommend') || sentence.includes('suggest') || sentence.includes('perfect')) {
        if (currentSection.length > 0) {
          sections.push({ type: 'recommendation', content: currentSection });
          currentSection = [];
        }
        currentSection.push(sentence.trim());
      } else if (sentence.includes('rating') || sentence.includes('well-structured')) {
        if (currentSection.length > 0) {
          sections.push({ type: 'quality', content: currentSection });
          currentSection = [];
        }
        currentSection.push(sentence.trim());
      } else if (sentence.includes('goals') || sentence.includes('future') || sentence.includes('prepare')) {
        if (currentSection.length > 0) {
          sections.push({ type: 'goals', content: currentSection });
          currentSection = [];
        }
        currentSection.push(sentence.trim());
      } else {
        currentSection.push(sentence.trim());
      }
    });
    
    if (currentSection.length > 0) {
      sections.push({ type: 'general', content: currentSection });
    }

    return { summary, sections, courseNames };
  };

  const { summary, sections, courseNames } = parseReasoning(reasoning);

  // Highlight course names in text
  const highlightCourseNames = (text) => {
    let highlightedText = text;
    courseNames.forEach(courseName => {
      const regex = new RegExp(`\\*\\*${courseName}\\*\\*`, 'g');
      highlightedText = highlightedText.replace(regex, courseName);
    });
    return highlightedText;
  };

  // Get section icon
  const getSectionIcon = (type) => {
    switch (type) {
      case 'recommendation': return <LightbulbOutlined color="primary" />;
      case 'quality': return <Star color="warning" />;
      case 'goals': return <TrendingUp color="success" />;
      default: return <CheckCircle color="action" />;
    }
  };

  // Get section title
  const getSectionTitle = (type) => {
    switch (type) {
      case 'recommendation': return 'Why This Course';
      case 'quality': return 'Course Quality';
      case 'goals': return 'Your Learning Goals';
      default: return 'Additional Notes';
    }
  };

  if (compact) {
    return (
      <Card sx={{ mb: 2, border: '1px solid', borderColor: 'primary.light' }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Psychology sx={{ color: 'primary.main', mr: 1, fontSize: 20 }} />
            <Typography variant="subtitle2" color="primary">
              🧠 AI Recommendation
            </Typography>
            {!expanded && (
              <IconButton 
                size="small"
                onClick={() => setExpanded(true)}
                sx={{ ml: 'auto' }}
              >
                <ExpandMore />
              </IconButton>
            )}
          </Box>
          
          <Typography variant="body2" sx={{ mb: 1 }}>
            {highlightCourseNames(summary)}
          </Typography>
          
          {courseNames.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {courseNames.map((course, index) => (
                <Chip 
                  key={index}
                  label={course}
                  size="small"
                  color="primary"
                  variant="outlined"
                  icon={<PlayCircleOutline />}
                />
              ))}
            </Box>
          )}

          <Collapse in={expanded}>
            <Divider sx={{ my: 2 }} />
            {sections.map((section, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {getSectionIcon(section.type)}
                  <Typography variant="subtitle2" sx={{ ml: 1 }}>
                    {getSectionTitle(section.type)}
                  </Typography>
                </Box>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    pl: 3, 
                    borderLeft: '2px solid', 
                    borderColor: 'primary.light',
                    lineHeight: 1.6
                  }}
                >
                  {highlightCourseNames(section.content.join('. ') + '.')}
                </Typography>
              </Box>
            ))}
            
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <IconButton 
                size="small"
                onClick={() => setExpanded(false)}
              >
                <ExpandLess />
              </IconButton>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  }

  // Full version (for recommendations page)
  return (
    <Card sx={{ mb: 3, border: '2px solid', borderColor: 'primary.light' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Psychology sx={{ color: 'primary.main', mr: 1 }} />
          <Typography variant="h6" color="primary">
            🧠 AI Recommendation Insights
          </Typography>
          <IconButton 
            onClick={() => setExpanded(!expanded)}
            sx={{ ml: 'auto' }}
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>

        {/* Quick Summary */}
        <Box sx={{ mb: 2 }}>
          <Chip 
            icon={<TrendingUp />} 
            label={`${courses?.length || 0} courses matched`} 
            color="success" 
            size="small"
            sx={{ mr: 1 }}
          />
          <Chip 
            icon={<LightbulbOutlined />} 
            label="AI-powered analysis" 
            color="primary" 
            variant="outlined" 
            size="small"
          />
        </Box>

        {/* Summary */}
        <Typography variant="body1" sx={{ mb: 2, fontWeight: 500 }}>
          {highlightCourseNames(summary)}
        </Typography>

        {/* Recommended Courses */}
        {courseNames.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              📚 Recommended Courses:
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {courseNames.map((course, index) => (
                <Chip 
                  key={index}
                  label={course}
                  color="primary"
                  icon={<PlayCircleOutline />}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Expandable Details */}
        <Collapse in={expanded}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle2" gutterBottom color="primary">
            📋 Detailed AI Analysis:
          </Typography>
          
          <List dense>
            {sections.map((section, index) => (
              <ListItem key={index} sx={{ pl: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {getSectionIcon(section.type)}
                </ListItemIcon>
                <ListItemText
                  primary={getSectionTitle(section.type)}
                  secondary={
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        mt: 0.5,
                        lineHeight: 1.6,
                        whiteSpace: 'pre-line'
                      }}
                    >
                      {highlightCourseNames(section.content.join('. ') + '.')}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>

          {/* User Context Summary */}
          {userContext && (
            <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                👤 Your Learning Profile:
              </Typography>
              {userContext.preferences?.topics?.length > 0 && (
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                  {userContext.preferences.topics.map(topic => (
                    <Chip key={topic} label={topic} size="small" color="primary" variant="outlined" />
                  ))}
                </Box>
              )}
              <Typography variant="caption" color="text.secondary">
                Learning Style: {userContext.preferences?.learning_style || 'Not set'} • 
                Difficulty: {userContext.preferences?.difficulty || 'Not set'} •
                Vector Search: {userContext.vector_search_available ? 'Active' : 'Inactive'}
              </Typography>
            </Box>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default AIExplanationCard; 