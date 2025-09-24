import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  BugReport as BugReportIcon,
  Search as SearchIcon,
  OpenInNew as OpenInNewIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  ChartTooltip,
  Legend
);

const SprintCross = () => {
  const [boardInput, setBoardInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('Initializing...');
  const [results, setResults] = useState(null);
  const [progressInterval, setProgressInterval] = useState(null);

  // Helper to extract board ID from URL or input
  const extractBoardIdFromUrl = (input) => {
    if (/^\d+$/.test(input.trim())) {
      return input.trim();
    }
    const patterns = [
      /\/boards\/(\d+)/,
      /rapidView=(\d+)/,
      /board=(\d+)/,
      /boardId=(\d+)/
    ];
    for (const pattern of patterns) {
      const match = input.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return null;
  };

  // Start SprintCross analysis
  const handleSearch = async (e) => {
    e.preventDefault();
    const boardInputValue = boardInput.trim();
    
    if (!boardInputValue) {
      setError('Please enter a Jira board URL or Board ID.');
      return;
    }
    
    const boardId = extractBoardIdFromUrl(boardInputValue);
    if (!boardId) {
      setError('Could not extract board ID from the provided input.');
      return;
    }
    
    await loadSprintCrossDataByBoard(boardId);
  };

  // Fetch and display SprintCross data by board
  const loadSprintCrossDataByBoard = async (boardId) => {
    try {
      // Reset UI
      setError('');
      setResults(null);
      setProgress(0);
      setProgressText('Initializing request...');
      setLoading(true);
      
      // Simulate progress updates
      const progressSteps = [
        { progress: 20, text: 'Connecting to JIRA...' },
        { progress: 40, text: 'Fetching board data...' },
        { progress: 60, text: 'Analyzing sprint data...' },
        { progress: 80, text: 'Processing issues...' },
        { progress: 90, text: 'Generating charts...' }
      ];
      
      let currentStep = 0;
      const interval = setInterval(() => {
        if (currentStep < progressSteps.length) {
          const step = progressSteps[currentStep];
          setProgress(step.progress);
          setProgressText(step.text);
          currentStep++;
        }
      }, 300);
      
      setProgressInterval(interval);
      
      const response = await fetch(`/api/issues/multi_sprint?board_id=${boardId}`);
      clearInterval(interval);
      
      if (!response.ok) {
        throw new Error('Failed to load SprintCross data');
      }
      
      // Complete progress
      setProgress(100);
      setProgressText('Analysis complete!');
      
      const data = await response.json();
      setResults(data);
      
    } catch (error) {
      console.error('Error loading SprintCross data:', error);
      setError('Failed to load SprintCross data.');
    } finally {
      setLoading(false);
      setTimeout(() => {
        setProgress(0);
        setProgressText('');
      }, 1000);
    }
  };

  // Chart data preparation functions
  const prepareChartData = (countsObj, label) => {
    if (!countsObj || Object.keys(countsObj).length === 0) return null;
    
    const labels = Object.keys(countsObj);
    const data = Object.values(countsObj);
    const total = data.reduce((a, b) => a + b, 0);
    
    // Color palette
    const palette = [
      '#36A2EB', '#FF6384', '#4BC0C0', '#FFCE56', '#9966FF', '#FF9F40', 
      '#8BC34A', '#E91E63', '#00BCD4', '#FFC107', '#607D8B', '#795548'
    ];
    const backgroundColors = labels.map((_, i) => palette[i % palette.length]);
    
    return {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors,
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          boxWidth: 16,
          padding: 15,
          usePointStyle: true
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percent = ((value / total) * 100).toFixed(1);
            return `${context.label}: ${value} (${percent}%)`;
          }
        }
      }
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <BugReportIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          SprintCross (Multi-Sprint)
        </Typography>
      </Box>

      {/* Input Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box component="form" onSubmit={handleSearch}>
            <Grid container spacing={3} alignItems="end">
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  label="Jira Board URL or Board ID"
                  value={boardInput}
                  onChange={(e) => setBoardInput(e.target.value)}
                  placeholder="Enter Jira board URL or Board ID"
                  disabled={loading}
                  helperText="Enter a board URL or ID to analyze issues that span multiple sprints"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? 'Analyzing...' : 'Search'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Progress Section */}
      {loading && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Analysis Progress
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ mb: 2, height: 8, borderRadius: 4 }}
            />
            <Box display="flex" alignItems="center" gap={2}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                {progressText}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Error Section */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Results Section */}
      {results && (
        <Box>
          {/* Summary */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
                  <CheckCircleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  SprintCross Analysis Complete
                </Typography>
                {results.jira_link && (
                  <Button
                    variant="outlined"
                    startIcon={<OpenInNewIcon />}
                    href={results.jira_link}
                    target="_blank"
                  >
                    View in JIRA
                  </Button>
                )}
              </Box>
              <Typography variant="body1">
                Found <strong>{results.total}</strong> issues that have been in multiple sprints.
              </Typography>
            </CardContent>
          </Card>

          {/* Charts Section */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: 'info.main' }}>
                    📝 Issue Types
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    {results.type_counts && (
                      <Doughnut 
                        data={prepareChartData(results.type_counts, 'Issue Types')}
                        options={chartOptions}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: 'error.main' }}>
                    🚨 Priority Levels
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    {results.priority_counts && (
                      <Doughnut 
                        data={prepareChartData(results.priority_counts, 'Priority Levels')}
                        options={chartOptions}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
                    ✅ Completion Status
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    {results.status_counts && (
                      <Doughnut 
                        data={prepareChartData(results.status_counts, 'Completion Status')}
                        options={chartOptions}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Issues List */}
          {results.issues && results.issues.length > 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Multi-Sprint Issues ({results.issues.length})
                </Typography>
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  <Grid container spacing={2}>
                    {results.issues.map((issue, index) => (
                      <Grid item xs={12} key={index}>
                        <Card variant="outlined">
                          <CardContent sx={{ py: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Box>
                                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                  {issue.key}: {issue.summary}
                                </Typography>
                                <Box display="flex" gap={1} mt={1}>
                                  <Chip 
                                    label={issue.issuetype} 
                                    size="small" 
                                    color="primary" 
                                    variant="outlined" 
                                  />
                                  <Chip 
                                    label={issue.priority} 
                                    size="small" 
                                    color="secondary" 
                                    variant="outlined" 
                                  />
                                  <Chip 
                                    label={issue.status} 
                                    size="small" 
                                    color={issue.status === 'Completed' ? 'success' : 'default'} 
                                    variant="outlined" 
                                  />
                                  {issue.assignee !== 'Unassigned' && (
                                    <Chip 
                                      label={issue.assignee} 
                                      size="small" 
                                      color="info" 
                                      variant="outlined" 
                                    />
                                  )}
                                </Box>
                              </Box>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<OpenInNewIcon />}
                                href={`${window.location.origin.replace('3001', '5000')}/browse/${issue.key}`}
                                target="_blank"
                              >
                                View
                              </Button>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* No Issues Found */}
          {results.total === 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Alert severity="info">
                  <Typography variant="body1">
                    No issues found in multiple sprints for this board.
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
};

export default SprintCross; 