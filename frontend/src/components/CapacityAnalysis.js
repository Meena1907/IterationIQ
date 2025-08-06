import React, { useState, useEffect, useRef } from 'react';
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Divider,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ContentCopy as ContentCopyIcon,
  CameraAlt as CameraIcon,
  WhatsApp as WhatsAppIcon,
  Email as EmailIcon,
  LinkedIn as LinkedInIcon,
  GetApp as GetAppIcon,
  Link as LinkIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
} from 'chart.js';
import html2canvas from 'html2canvas';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  ChartTooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title
);

const CapacityAnalysis = () => {
  const [userEmail, setUserEmail] = useState('');
  const [weeksBack, setWeeksBack] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('Initializing analysis...');
  const [results, setResults] = useState(null);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [progressInterval, setProgressInterval] = useState(null);
  
  // Share and export functionality
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [capturedScreenshot, setCapturedScreenshot] = useState(null);
  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  // Refs for screenshot capture
  const resultsSectionRef = useRef(null);

  // Email validation
  const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Start capacity analysis
  const handleStartAnalysis = async () => {
    if (!userEmail.trim()) {
      setError('Please enter a user email');
      return;
    }
    
    if (!isValidEmail(userEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    // Reset UI
    setError('');
    setResults(null);
    setProgress(0);
    setProgressText('Initializing analysis...');
    setLoading(true);
    
    try {
      const response = await fetch('/api/capacity/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_email: userEmail.trim(),
          weeks_back: weeksBack
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to start analysis');
      }
      
      setCurrentTaskId(data.task_id);
      startProgressPolling(data.task_id);
      
    } catch (error) {
      console.error('Error starting capacity analysis:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  // Progress polling
  const startProgressPolling = (taskId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/capacity/progress/${taskId}`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to get progress');
        }
        
        setProgress(data.progress);
        
        if (data.status === 'fetching_data') {
          setProgressText('Fetching user data from JIRA...');
        } else if (data.status === 'in_progress') {
          setProgressText('Analyzing performance patterns...');
        } else if (data.status === 'completed') {
          setProgressText('Analysis completed!');
          clearInterval(interval);
          setLoading(false);
          setResults(data.result);
        } else if (data.status === 'error') {
          clearInterval(interval);
          setLoading(false);
          setError(data.error || 'Analysis failed');
        }
        
      } catch (error) {
        console.error('Error polling progress:', error);
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get analysis progress');
      }
    }, 2000);
    
    setProgressInterval(interval);
  };

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  // Export report
  const handleExportReport = async () => {
    if (!currentTaskId) {
      setError('No analysis results to export');
      return;
    }
    
    try {
      const params = new URLSearchParams({
        include_charts: 'true',
        include_insights: 'true',
        format: 'csv'
      });
      
      const response = await fetch(`/api/capacity/export/${currentTaskId}?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('Failed to export report');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `capacity_analysis_${userEmail.split('@')[0]}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSnackbarMessage('Report exported successfully!');
      setSnackbarOpen(true);
      
    } catch (error) {
      console.error('Error exporting report:', error);
      setError('Failed to export report');
    }
  };

  // Share report
  const handleShareReport = async () => {
    setShareDialogOpen(true);
  };

  // Capture screenshot
  const handleCaptureScreenshot = async () => {
    if (!resultsSectionRef.current) return;
    
    setScreenshotLoading(true);
    try {
      const canvas = await html2canvas(resultsSectionRef.current, {
        useCORS: true,
        allowTaint: true,
        scale: 2,
        backgroundColor: '#ffffff'
      });
      
      const screenshot = canvas.toDataURL('image/png');
      setCapturedScreenshot(screenshot);
      
      setSnackbarMessage('Screenshot captured successfully!');
      setSnackbarOpen(true);
      
    } catch (error) {
      console.error('Error capturing screenshot:', error);
      setError('Failed to capture screenshot');
    } finally {
      setScreenshotLoading(false);
    }
  };

  // Download screenshot
  const handleDownloadScreenshot = () => {
    if (!capturedScreenshot) return;
    
    const link = document.createElement('a');
    link.download = `capacity_analysis_${userEmail.split('@')[0]}_${new Date().toISOString().split('T')[0]}.png`;
    link.href = capturedScreenshot;
    link.click();
  };

  // Share to WhatsApp
  const handleShareToWhatsApp = () => {
    const text = `Capacity Analysis Report for ${userEmail}\n\nKey Metrics:\n• Avg Completed/Week: ${results?.avg_completed_per_week || 'N/A'}\n• Completion Rate: ${results?.completion_rate || 'N/A'}\n• Avg Hours/Week: ${results?.avg_hours_per_week || 'N/A'}\n\nView full report: ${window.location.origin}`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  // Share to Slack
  const handleShareToSlack = () => {
    const text = `Capacity Analysis Report for ${userEmail}\n\nKey Metrics:\n• Avg Completed/Week: ${results?.avg_completed_per_week || 'N/A'}\n• Completion Rate: ${results?.completion_rate || 'N/A'}\n• Avg Hours/Week: ${results?.avg_hours_per_week || 'N/A'}\n\nView full report: ${window.location.origin}`;
    const url = `https://slack.com/intl/en-in/help/articles/206870106-Share-links-in-Slack`;
    window.open(url, '_blank');
  };

  // Copy to clipboard
  const handleCopyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setSnackbarMessage('Copied to clipboard!');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      setError('Failed to copy to clipboard');
    }
  };

  // Create visual share link
  const handleCreateVisualShareLink = async () => {
    if (!capturedScreenshot) {
      setError('Please capture a screenshot first');
      return;
    }
    
    try {
      const formData = new FormData();
      const blob = await fetch(capturedScreenshot).then(r => r.blob());
      formData.append('screenshot', blob, 'capacity_analysis.png');
      formData.append('report_type', 'capacity_analysis');
      formData.append('user_email', userEmail);
      
      const response = await fetch('/api/capacity/upload-screenshot', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to upload screenshot');
      }
      
      const shareUrl = `${window.location.origin}/shared-report/${data.share_id}`;
      setShareUrl(shareUrl);
      
      setSnackbarMessage('Visual share link created!');
      setSnackbarOpen(true);
      
    } catch (error) {
      console.error('Error creating visual share link:', error);
      setError('Failed to create visual share link');
    }
  };

  // Chart data preparation functions
  const prepareIssueTypeData = (issueTypes) => {
    if (!issueTypes) return null;
    
    const sortedTypes = Object.entries(issueTypes)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    return {
      labels: sortedTypes.map(([type]) => type),
      datasets: [{
        data: sortedTypes.map(([, count]) => count),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    };
  };

  const preparePriorityData = (priorities) => {
    if (!priorities) return null;
    
    const sortedPriorities = Object.entries(priorities)
      .sort((a, b) => b[1] - a[1]);
    
    return {
      labels: sortedPriorities.map(([priority]) => priority),
      datasets: [{
        data: sortedPriorities.map(([, count]) => count),
        backgroundColor: ['#FF6B6B', '#FFA726', '#FFD54F', '#81C784', '#4FC3F7'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    };
  };

  const prepareCompletionData = (completion) => {
    if (!completion) return null;
    
    return {
      labels: ['Completed', 'In Progress', 'Not Started'],
      datasets: [{
        data: [completion.completed || 0, completion.in_progress || 0, completion.not_started || 0],
        backgroundColor: ['#4CAF50', '#FF9800', '#9E9E9E'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    };
  };

  const prepareWeeklyChartData = (weeklySummary) => {
    if (!weeklySummary || !Array.isArray(weeklySummary)) return null;
    
    const weeks = weeklySummary.map(w => w.week);
    const completed = weeklySummary.map(w => w.completed);
    const started = weeklySummary.map(w => w.started);
    const hoursSpent = weeklySummary.map(w => w.hours_spent);
    
    return {
      labels: weeks,
      datasets: [{
        label: 'Completed Issues',
        data: completed,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
        yAxisID: 'y'
      }, {
        label: 'Started Issues',
        data: started,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.1,
        yAxisID: 'y'
      }, {
        label: 'Hours Spent',
        data: hoursSpent,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1,
        yAxisID: 'y1'
      }]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true
        }
      }
    }
  };

  const weeklyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Week'
        }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Issues'
        }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Hours'
        },
        grid: {
          drawOnChartArea: false,
        },
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.dataset.label === 'Hours Spent') {
              label += context.parsed.y.toFixed(1) + 'h';
            } else {
              label += context.parsed.y;
            }
            return label;
          }
        }
      }
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <AnalyticsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Individual Capacity Analysis
        </Typography>
      </Box>

      {/* Input Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="User Email"
                type="email"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                placeholder="Enter user email (e.g., john.doe@company.com)"
                helperText="Enter the email address of the user you want to analyze."
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Analysis Period</InputLabel>
                <Select
                  value={weeksBack}
                  onChange={(e) => setWeeksBack(e.target.value)}
                  label="Analysis Period"
                  disabled={loading}
                >
                  <MenuItem value={4}>Last 4 weeks</MenuItem>
                  <MenuItem value={8}>Last 8 weeks</MenuItem>
                  <MenuItem value={12}>Last 12 weeks</MenuItem>
                  <MenuItem value={16}>Last 16 weeks</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
              onClick={handleStartAnalysis}
              disabled={loading}
            >
              {loading ? 'Analyzing...' : 'Start Analysis'}
            </Button>
            
            <Button
              variant="outlined"
              color="success"
              startIcon={<DownloadIcon />}
              onClick={handleExportReport}
              disabled={!results}
            >
              Export Report
            </Button>
            
            <Button
              variant="outlined"
              color="info"
              startIcon={<ShareIcon />}
              onClick={handleShareReport}
              disabled={!results}
            >
              Share Report
            </Button>
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
        <Box ref={resultsSectionRef}>
                     {/* Overview Cards */}
           <Card sx={{ mb: 3 }}>
             <CardContent>
               <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                 <Typography variant="h6" sx={{ fontWeight: 600 }}>
                   Overview
                 </Typography>
                 {results.jira_link && (
                   <Button
                     size="small"
                     variant="outlined"
                     startIcon={<OpenInNewIcon />}
                     href={results.jira_link}
                     target="_blank"
                   >
                     View in JIRA
                   </Button>
                 )}
               </Box>
               <Grid container spacing={3}>
                 <Grid item xs={12} md={3}>
                   <Box sx={{ textAlign: 'center' }}>
                     <Typography variant="h4" color="primary" sx={{ fontWeight: 600 }}>
                       {results.metrics?.avg_completed_per_week?.toFixed(1) || '-'}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Avg Completed/Week
                     </Typography>
                   </Box>
                 </Grid>
                 <Grid item xs={12} md={3}>
                   <Box sx={{ textAlign: 'center' }}>
                     <Typography variant="h4" color="success.main" sx={{ fontWeight: 600 }}>
                       {results.metrics?.completion_rate ? `${(results.metrics.completion_rate * 100).toFixed(1)}%` : '-'}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Completion Rate
                     </Typography>
                   </Box>
                 </Grid>
                 <Grid item xs={12} md={3}>
                   <Box sx={{ textAlign: 'center' }}>
                     <Typography variant="h4" color="info.main" sx={{ fontWeight: 600 }}>
                       {results.metrics?.avg_hours_per_week?.toFixed(1) ? `${results.metrics.avg_hours_per_week.toFixed(1)}h` : '-'}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Avg Hours/Week
                     </Typography>
                   </Box>
                 </Grid>
                 <Grid item xs={12} md={3}>
                   <Box sx={{ textAlign: 'center' }}>
                     <Typography variant="h4" color="warning.main" sx={{ fontWeight: 600 }}>
                       {results.total_issues_analyzed || '-'}
                     </Typography>
                     <Typography variant="body2" color="text.secondary">
                       Total Issues
                     </Typography>
                     {results.jira_link && (
                       <Button
                         size="small"
                         variant="outlined"
                         startIcon={<OpenInNewIcon />}
                         href={results.jira_link}
                         target="_blank"
                         sx={{ mt: 1 }}
                       >
                         View All
                       </Button>
                     )}
                   </Box>
                 </Grid>
               </Grid>
             </CardContent>
           </Card>

                     {/* Charts Section */}
           <Grid container spacing={3} sx={{ mb: 3 }}>
             <Grid item xs={12} md={4}>
               <Card>
                 <CardContent>
                   <Typography variant="h6" gutterBottom>
                     📝 Issue Types
                   </Typography>
                   <Box sx={{ height: 300 }}>
                     {results.issue_breakdown?.by_type && (
                       <Doughnut 
                         data={prepareIssueTypeData(results.issue_breakdown.by_type)}
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
                   <Typography variant="h6" gutterBottom>
                     🚨 Priority Levels
                   </Typography>
                   <Box sx={{ height: 300 }}>
                     {results.issue_breakdown?.by_priority && (
                       <Doughnut 
                         data={preparePriorityData(results.issue_breakdown.by_priority)}
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
                   <Typography variant="h6" gutterBottom>
                     ✅ Completion Status
                   </Typography>
                   <Box sx={{ height: 300 }}>
                     {results.issue_breakdown?.by_completion && (
                       <Doughnut 
                         data={prepareCompletionData(results.issue_breakdown.by_completion)}
                         options={chartOptions}
                       />
                     )}
                   </Box>
                 </CardContent>
               </Card>
             </Grid>
           </Grid>

           {/* Weekly Performance Chart */}
           {results.weekly_summary && results.weekly_summary.length > 0 && (
             <Card sx={{ mb: 3 }}>
               <CardContent>
                 <Typography variant="h6" gutterBottom>
                   Weekly Trend
                 </Typography>
                 <Box sx={{ height: 400 }}>
                   <Line 
                     data={prepareWeeklyChartData(results.weekly_summary)}
                     options={weeklyChartOptions}
                   />
                 </Box>
               </CardContent>
             </Card>
           )}

           {/* Insights and Recommendations */}
           <Grid container spacing={3} sx={{ mb: 3 }}>
             <Grid item xs={12} md={6}>
               <Card>
                 <CardContent>
                   <Typography variant="h6" gutterBottom>
                     Key Insights
                   </Typography>
                   <Box component="ul" sx={{ pl: 0, listStyle: 'none' }}>
                     {results.insights && results.insights.map((insight, index) => (
                       <Box component="li" key={index} sx={{ mb: 2, display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                         <WarningIcon sx={{ color: 'warning.main', fontSize: 20, mt: 0.2 }} />
                         <Typography variant="body2">{insight}</Typography>
                       </Box>
                     ))}
                   </Box>
                 </CardContent>
               </Card>
             </Grid>
             <Grid item xs={12} md={6}>
               <Card>
                 <CardContent>
                   <Typography variant="h6" gutterBottom>
                     Recommendations
                   </Typography>
                   <Box component="ul" sx={{ pl: 0, listStyle: 'none' }}>
                     {results.recommendations && results.recommendations.map((rec, index) => (
                       <Box component="li" key={index} sx={{ mb: 2, display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                         <CheckCircleIcon sx={{ color: 'primary.main', fontSize: 20, mt: 0.2 }} />
                         <Typography variant="body2">{rec}</Typography>
                       </Box>
                     ))}
                   </Box>
                 </CardContent>
               </Card>
             </Grid>
           </Grid>
        </Box>
      )}

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ 
          borderBottom: '1px solid #e0e0e0', 
          pb: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
            Share Capacity Analysis Report
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {/* Report Summary */}
          <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">User Email</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{userEmail}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Analysis Period</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>Last {weeksBack} weeks</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Report Type</Typography>
                  <Chip label="Capacity Analysis" size="small" color="primary" variant="outlined" />
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Generated</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {new Date().toLocaleDateString()}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Sharing Options */}
          <Grid container spacing={3}>
            {/* Visual Share Column */}
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                Visual Share
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  variant="contained"
                  startIcon={screenshotLoading ? <CircularProgress size={20} /> : <CameraIcon />}
                  onClick={handleCaptureScreenshot}
                  disabled={screenshotLoading}
                  fullWidth
                >
                  {screenshotLoading ? 'Capturing...' : 'Capture Screenshot'}
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<WhatsAppIcon />}
                  onClick={handleShareToWhatsApp}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Share Image to WhatsApp
                </Button>
                <Button
                  variant="contained"
                  color="info"
                  startIcon={<LinkedInIcon />}
                  onClick={handleShareToSlack}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Share Image to Slack
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<GetAppIcon />}
                  onClick={handleDownloadScreenshot}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Download Screenshot
                </Button>
              </Box>
            </Grid>

            {/* Quick Share Column */}
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                Quick Share
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<LinkIcon />}
                  onClick={() => handleCreateVisualShareLink()}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Create Visual Share Link
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<EmailIcon />}
                  onClick={() => {
                    const subject = `Capacity Analysis Report - ${userEmail}`;
                    const body = `Hi,\n\nPlease find the capacity analysis report for ${userEmail}.\n\nKey Metrics:\n• Avg Completed/Week: ${results?.avg_completed_per_week || 'N/A'}\n• Completion Rate: ${results?.completion_rate || 'N/A'}\n• Avg Hours/Week: ${results?.avg_hours_per_week || 'N/A'}\n\nBest regards`;
                    window.open(`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
                  }}
                  fullWidth
                >
                  Email Summary
                </Button>
              </Box>
            </Grid>

            {/* Copy & Share Column */}
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                Copy & Share
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  variant="outlined"
                  startIcon={<ContentCopyIcon />}
                  onClick={() => {
                    const summary = `Capacity Analysis Report for ${userEmail}\n\nKey Metrics:\n• Avg Completed/Week: ${results?.avg_completed_per_week || 'N/A'}\n• Completion Rate: ${results?.completion_rate || 'N/A'}\n• Avg Hours/Week: ${results?.avg_hours_per_week || 'N/A'}\n• Total Issues: ${results?.total_issues || 'N/A'}`;
                    handleCopyToClipboard(summary);
                  }}
                  fullWidth
                >
                  Copy Summary
                </Button>
                {shareUrl && (
                  <Button
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={() => handleCopyToClipboard(shareUrl)}
                    fullWidth
                  >
                    Copy Share Link
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>

          {/* Screenshot Preview */}
          {capturedScreenshot && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Screenshot Preview
              </Typography>
              <Box sx={{ border: '1px solid #e0e0e0', borderRadius: 1, p: 1 }}>
                <img 
                  src={capturedScreenshot} 
                  alt="Capacity Analysis Screenshot" 
                  style={{ width: '100%', height: 'auto', borderRadius: 4 }}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default CapacityAnalysis; 