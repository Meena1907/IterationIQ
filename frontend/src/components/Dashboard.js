import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Paper,
  Chip,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  Psychology as PsychologyIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';

const Dashboard = ({ onNavigate }) => {
  const dashboardItems = [
    {
      title: 'Sprint Report',
      description: 'Analyze sprint performance, completion rates, and team velocity with detailed insights and AI-powered recommendations.',
      icon: <AssessmentIcon sx={{ fontSize: 40 }} />,
      color: '#00ABE4',
      tabIndex: 1,
      features: ['Sprint Analytics', 'AI Insights', 'Performance Metrics', 'Export Reports'],
      status: 'Active'
    },
    {
      title: 'Capacity Analysis',
      description: 'Track individual and team capacity, workload distribution, and productivity patterns across sprints.',
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      color: '#0066CC',
      tabIndex: 2,
      features: ['Team Capacity', 'Workload Analysis', 'Productivity Tracking', 'Resource Planning'],
      status: 'Active'
    },
    {
      title: 'Best Practices',
      description: 'Access comprehensive guidelines, tips, and strategies for effective sprint management and team collaboration.',
      icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
      color: '#4CAF50',
      tabIndex: 4,
      features: ['Sprint Guidelines', 'Team Collaboration', 'Performance Tips', 'Process Optimization'],
      status: 'Active'
    },
    {
      title: 'SprintCross',
      description: 'Analyze cross-sprint dependencies, blocked issues, and inter-sprint impact for better planning.',
      icon: <BugReportIcon sx={{ fontSize: 40 }} />,
      color: '#FF9800',
      tabIndex: 5,
      features: ['Dependency Tracking', 'Blocked Issues', 'Cross-Sprint Analysis', 'Impact Assessment'],
      status: 'Active'
    }
  ];

  const handleCardClick = (tabIndex) => {
    if (onNavigate) {
      onNavigate(tabIndex);
    }
  };

  return (
    <Box>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 700, color: 'primary.main' }}>
          Welcome to Spark
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          Team Performance Management Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Choose a module below to get started with your sprint analytics and team performance insights.
        </Typography>
      </Box>



      {/* Dashboard Cards */}
      <Grid container spacing={3}>
        {dashboardItems.map((item, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card 
              elevation={2} 
              sx={{ 
                height: '100%',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                }
              }}
            >
              <CardActionArea 
                onClick={() => handleCardClick(item.tabIndex)}
                sx={{ height: '100%', p: 0 }}
                disabled={item.status === 'Coming Soon'}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="flex-start" gap={2} mb={2}>
                    <Box 
                      sx={{ 
                        p: 2, 
                        borderRadius: 2, 
                        backgroundColor: `${item.color}15`,
                        color: item.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {item.icon}
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Typography variant="h5" sx={{ fontWeight: 600 }}>
                          {item.title}
                        </Typography>
                        <Chip 
                          label={item.status} 
                          size="small" 
                          color={item.status === 'Active' ? 'success' : 'default'}
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {item.description}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Features */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Key Features:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {item.features.map((feature, featureIndex) => (
                        <Chip
                          key={featureIndex}
                          label={feature}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.75rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity Section */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Recent Activity
        </Typography>
        <Paper elevation={0} sx={{ p: 3, backgroundColor: 'background.paper' }}>
          <Typography variant="body2" color="text.secondary">
            • Sprint Report generated for Board 2074 - 2 hours ago
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Capacity Analysis completed for team - 1 day ago
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • AI Insights updated for latest sprint - 3 days ago
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default Dashboard; 