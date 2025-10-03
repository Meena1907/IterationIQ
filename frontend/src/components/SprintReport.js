import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Psychology as PsychologyIcon,
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
  Info as InfoIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import html2canvas from 'html2canvas';

const SprintReport = () => {
  const [boardInput, setBoardInput] = useState('');
  const [boardId, setBoardId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sprintData, setSprintData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [totalSprints, setTotalSprints] = useState(0);
  const [filteredCount, setFilteredCount] = useState(0);
  const [progress, setProgress] = useState({ current: 0, total: 15, message: '' });
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [progressInterval, setProgressInterval] = useState(null);
  const [pollingStartTime, setPollingStartTime] = useState(null);
  
  // Share and screenshot functionality
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [capturedScreenshot, setCapturedScreenshot] = useState(null);
  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [aiInsightsDialogOpen, setAiInsightsDialogOpen] = useState(false);
  const [aiInsights, setAiInsights] = useState(null);
  const [aiInsightsLoading, setAiInsightsLoading] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  // Refs for screenshot capture
  const reportSectionRef = useRef(null);

  // Extract board ID from URL or input
  const extractBoardId = (input) => {
    const urlMatch = input.match(/boards\/(\d+)/);
    const idMatch = input.match(/^(\d+)$/);
    return urlMatch ? urlMatch[1] : (idMatch ? idMatch[1] : '');
  };

  const handleBoardInputChange = (event) => {
    const value = event.target.value;
    setBoardInput(value);
    const extractedId = extractBoardId(value);
    setBoardId(extractedId);
  };

  const handleGenerateReport = async () => {
    if (!boardId) {
      setError('Please enter a valid board URL or ID');
      return;
    }

    console.log('🚀 STEP 1: Starting sprint report generation for board:', boardId); // Debug log
    setLoading(true);
    setError('');
    setSprintData([]);
    setProgress({ current: 0, total: 15, message: 'Starting analysis...' });

    try {
      console.log('🚀 STEP 2: Making POST request to start sprint report'); // Debug log
      const response = await fetch('/api/jira_sprint_report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          board_id: boardId
        })
      });
      
      console.log('🚀 STEP 3: Response received:', response.status, response.statusText); // Debug log
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to start sprint report');
      }
      
      console.log('🚀 STEP 4: Task started, task_id:', data.task_id); // Debug log
      setCurrentTaskId(data.task_id);
      startProgressPolling(data.task_id);
      
    } catch (err) {
      console.error('🚀 STEP 20: Sprint report generation failed:', err); // Debug log
      setError(err.message || 'Failed to generate sprint report');
      setLoading(false);
    }
  };


  // Progress polling (same pattern as capacity analysis)
  const startProgressPolling = (taskId) => {
    console.log('🚀 STEP 5: Starting progress polling for task:', taskId); // Debug log
    setPollingStartTime(Date.now());
    const interval = setInterval(async () => {
      try {
        // Check for timeout (5 minutes)
        if (pollingStartTime && Date.now() - pollingStartTime > 300000) {
          console.log('🚀 STEP TIMEOUT: Polling timeout reached');
          clearInterval(interval);
          setLoading(false);
          setError('Sprint report generation timed out. Please try again.');
          return;
        }
        
        console.log('🚀 STEP 6: Polling progress for task:', taskId); // Debug log
        const response = await fetch(`/api/jira/sprint_report_progress?task_id=${taskId}`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to get progress');
        }
        
        console.log('🚀 STEP 7: Progress data received:', data); // Debug log
        
        if (data.status === 'fetching_data') {
          setProgress({ current: 0, total: data.total_sprints || 15, message: 'Fetching sprint data from JIRA...' });
        } else if (data.status === 'in_progress') {
          // Use real backend progress data if available, otherwise use percentage
          if (data.current_sprints !== undefined && data.total_sprints !== undefined) {
            setProgress({ current: data.current_sprints, total: data.total_sprints, message: 'Analyzing sprint data...' });
          } else {
            // Fallback to percentage-based progress
            const progressPercent = data.progress || 0;
            const currentSprints = Math.round((progressPercent / 100) * 15);
            setProgress({ current: currentSprints, total: 15, message: 'Analyzing sprint data...' });
          }
          
          // Show partial results as they come in
          if (data.partial_results && data.partial_results.length > 0) {
            setSprintData(data.partial_results);
          }
          
          // Log progress for debugging
          console.log('🚀 STEP 7.5: Progress update:', {
            progress: data.progress,
            current_sprints: data.current_sprints,
            total_sprints: data.total_sprints,
            status: data.status
          });
        } else if (data.status === 'completed') {
          console.log('🚀 STEP 8: Sprint report completed, results:', data.result); // Debug log
          setProgress({ current: data.total_sprints || 15, total: data.total_sprints || 15, message: 'Analysis completed!' });
          clearInterval(interval);
          setLoading(false);
          setSprintData(data.result || []);
        } else if (data.status === 'error') {
          console.error('🚀 STEP 9: Sprint report error:', data.error); // Debug log
          clearInterval(interval);
          setLoading(false);
          setError(data.error || 'Sprint report failed');
        }
        
      } catch (error) {
        console.error('🚀 STEP 10: Error polling progress:', error); // Debug log
        clearInterval(interval);
        setLoading(false);
        setError('Failed to get sprint report progress');
      }
    }, 2000);
    
    setProgressInterval(interval);
  };

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  // Filter sprint data based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredData(sprintData);
      setFilteredCount(sprintData.length);
    } else {
      const filtered = sprintData.filter(sprint =>
        sprint['Sprint Name']?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredData(filtered);
      setFilteredCount(filtered.length);
    }
    setTotalSprints(sprintData.length);
  }, [sprintData, searchTerm]);

  const getInsightColor = (insight) => {
    if (insight.includes('Good velocity') || insight.includes('✅')) return 'success';
    if (insight.includes('Low delivery') || insight.includes('❌')) return 'error';
    return 'warning';
  };

  const getCompletionColor = (completion) => {
    const percentage = parseFloat(completion.replace('%', ''));
    if (percentage >= 80) return 'success';
    if (percentage >= 50) return 'warning';
    return 'error';
  };

  const getInsightProgressValue = (insight) => {
    if (insight.includes('Good velocity') || insight.includes('✅')) return 100;
    if (insight.includes('Low delivery') || insight.includes('❌')) return 20;
    if (insight.includes('Moderate delivery') || insight.includes('⚠️')) return 60;
    return 40; // Default for other insights
  };

  // Download CSV handler
  const handleDownloadCSV = async () => {
    if (!sprintData.length) {
      setSnackbarMessage('No data to download');
      setSnackbarOpen(true);
      return;
    }

    try {
      const response = await fetch('/api/sprint/export-csv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sprint_data: sprintData,
          board_id: boardId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate CSV');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sprint_report_board_${boardId}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSnackbarMessage('CSV downloaded successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      setSnackbarMessage('Failed to download CSV: ' + error.message);
      setSnackbarOpen(true);
    }
  };

  // Share report handler
  const handleShareReport = async () => {
    if (!sprintData.length) {
      setSnackbarMessage('No data to share');
      setSnackbarOpen(true);
      return;
    }

    try {
      const response = await fetch('/api/capacity/share-link', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_data: {
            type: 'sprint_report',
            board_id: boardId,
            sprint_data: sprintData,
            generated_at: new Date().toISOString(),
            total_sprints: sprintData.length
          },
          expires_in_days: 7
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create share link');
      }

      const result = await response.json();
      setShareUrl(result.share_url);
      setShareDialogOpen(true);
    } catch (error) {
      setSnackbarMessage('Failed to create share link: ' + error.message);
      setSnackbarOpen(true);
    }
  };

  // AI Insights handler
  const handleAiInsights = async () => {
    if (!sprintData.length) {
      setSnackbarMessage('No data to analyze');
      setSnackbarOpen(true);
      return;
    }

    setAiInsightsLoading(true);
    setAiInsightsDialogOpen(true);

    try {
      const response = await fetch('/api/sprint/ai-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sprint_data: sprintData
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate AI insights');
      }

      const result = await response.json();
      setAiInsights(result.insights);
    } catch (error) {
      setSnackbarMessage('Failed to generate AI insights: ' + error.message);
      setSnackbarOpen(true);
      setAiInsightsDialogOpen(false);
    } finally {
      setAiInsightsLoading(false);
    }
  };

  // Screenshot capture handler
  const handleCaptureScreenshot = async () => {
    if (!reportSectionRef.current) {
      setSnackbarMessage('No report section to capture');
      setSnackbarOpen(true);
      return;
    }

    setScreenshotLoading(true);
    try {
      // Wait a bit for all elements to render properly
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const canvas = await html2canvas(reportSectionRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        allowTaint: false,
        scrollX: 0,
        scrollY: 0,
        width: reportSectionRef.current.scrollWidth,
        height: reportSectionRef.current.scrollHeight,
        logging: false,
        onclone: function(clonedDoc) {
          // Ensure all progress bars are visible in the clone
          const progressBars = clonedDoc.querySelectorAll('.MuiLinearProgress-root');
          progressBars.forEach(bar => {
            bar.style.opacity = '1';
            bar.style.visibility = 'visible';
          });
        }
      });

      const dataUrl = canvas.toDataURL('image/png');
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      
      setCapturedScreenshot({
        dataUrl,
        blob,
        timestamp: new Date().toISOString()
      });
      
      setSnackbarMessage('Screenshot captured successfully!');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Screenshot capture failed:', error);
      setSnackbarMessage('Failed to capture screenshot');
      setSnackbarOpen(true);
    } finally {
      setScreenshotLoading(false);
    }
  };

  // Download screenshot handler
  const handleDownloadScreenshot = () => {
    if (!capturedScreenshot) return;
    
    const link = document.createElement('a');
    const filename = `sprint-report-board-${boardId}-${new Date().toISOString().split('T')[0]}.png`;
    link.download = filename;
    link.href = capturedScreenshot.dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setSnackbarMessage('Screenshot downloaded!');
    setSnackbarOpen(true);
  };

  // Share screenshot to WhatsApp
  const handleShareToWhatsApp = () => {
    if (!capturedScreenshot) return;
    
    const avgCompletion = sprintData.reduce((sum, sprint) => 
      sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length;
    
    const summary = `🏃‍♂️ Sprint Analysis Report\n\n📋 Board: ${boardId}\n🎯 Sprints: ${sprintData.length}\n📈 Avg Completion: ${avgCompletion.toFixed(1)}%\n\nDetailed visual report attached! 📸`;
    
    navigator.clipboard.writeText(summary).then(() => {
      setSnackbarMessage('Summary copied! Download the screenshot and share both to WhatsApp.');
      setSnackbarOpen(true);
      handleDownloadScreenshot();
    });
  };

  // Share screenshot to Slack
  const handleShareToSlack = () => {
    if (!capturedScreenshot) return;
    
    const avgCompletion = sprintData.reduce((sum, sprint) => 
      sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length;
    
    const summary = `🏃‍♂️ *Sprint Analysis Report*\n\n📋 *Board:* ${boardId}\n🎯 *Sprints:* ${sprintData.length}\n📈 *Avg Completion:* ${avgCompletion.toFixed(1)}%\n\nDetailed visual report attached! 📸`;
    
    navigator.clipboard.writeText(summary).then(() => {
      setSnackbarMessage('Summary copied! Download the screenshot and share both to Slack.');
      setSnackbarOpen(true);
      handleDownloadScreenshot();
    });
  };

  // Email with screenshot
  const handleEmailWithScreenshot = () => {
    if (!capturedScreenshot) return;
    
    const avgCompletion = sprintData.reduce((sum, sprint) => 
      sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length;
    
    const subject = `Sprint Analysis Report - Board ${boardId} (Visual Report)`;
    const body = `Hi,\n\nPlease find attached the sprint analysis report for Board ${boardId}.\n\nKey Highlights:\n• Total Sprints Analyzed: ${sprintData.length}\n• Average Completion Rate: ${avgCompletion.toFixed(1)}%\n• Total Completed Issues: ${sprintData.reduce((sum, s) => sum + s["Completed"], 0)}\n• Total Issues Not Completed: ${sprintData.reduce((sum, s) => sum + s["Not Completed"], 0)}\n\nThe visual report screenshot will be downloaded automatically. Please attach it to your email.\n\nBest regards`;
    
    handleDownloadScreenshot();
    const mailtoUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
  };

  // Create visual share link with screenshot
  const handleCreateVisualShareLink = async () => {
    if (!capturedScreenshot) return;
    
    try {
      // Convert blob to file
      const file = new File([capturedScreenshot.blob], 'sprint-report.png', { type: 'image/png' });
      
      // Create form data
      const formData = new FormData();
      formData.append('screenshot', file);
      formData.append('report_data', JSON.stringify({
        type: 'sprint_report',
        board_id: boardId,
        sprint_data: sprintData,
        generated_at: new Date().toISOString(),
        total_sprints: sprintData.length
      }));

      // Upload screenshot
      const uploadResponse = await fetch('/api/capacity/upload-screenshot', {
        method: 'POST',
        body: formData
      });

      if (uploadResponse.ok) {
        const uploadResult = await uploadResponse.json();
        
        // Create share link with screenshot
        const shareResponse = await fetch('/api/capacity/share-link', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            report_data: {
              type: 'sprint_report',
              board_id: boardId,
              sprint_data: sprintData,
              generated_at: new Date().toISOString(),
              total_sprints: sprintData.length,
              screenshot_url: uploadResult.screenshot_url
            },
            expires_in_days: 7
          })
        });

        if (shareResponse.ok) {
          const shareResult = await shareResponse.json();
          setShareUrl(shareResult.share_url);
          setSnackbarMessage('Visual share link created with screenshot!');
          setSnackbarOpen(true);
        } else {
          setSnackbarMessage('Failed to create share link');
          setSnackbarOpen(true);
        }
      } else {
        setSnackbarMessage('Failed to upload screenshot');
        setSnackbarOpen(true);
      }
    } catch (error) {
      console.error('Error creating visual share link:', error);
      setSnackbarMessage('Error creating visual share link');
      setSnackbarOpen(true);
    }
  };

  // Copy to clipboard handler
  const handleCopyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setSnackbarMessage('Copied to clipboard!');
      setSnackbarOpen(true);
    } catch (error) {
      setSnackbarMessage('Failed to copy to clipboard');
      setSnackbarOpen(true);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
        Sprint Report
      </Typography>

      {/* Board Input Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Jira Board Configuration
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Jira Board URL or Board ID"
                value={boardInput}
                onChange={handleBoardInputChange}
                placeholder="Enter Jira board URL (e.g., https://thoughtspot.atlassian.net/jira/software/c/projects/SCAL/boards/2008) or Board ID (e.g., 2008)"
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleGenerateReport}
                disabled={!boardId || loading}
                startIcon={loading ? <CircularProgress size={20} /> : <RefreshIcon />}
                sx={{ height: 40 }}
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </Grid>
          </Grid>
          {boardId && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Board ID extracted: <strong>{boardId}</strong>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Progress Display */}
      {loading && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2}>
              <CircularProgress size={24} color="primary" />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {progress.message}
                </Typography>
                <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                  <Typography variant="body2" fontWeight={500}>
                    Progress: {progress.current}/{progress.total} sprints
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ({Math.round((progress.current / progress.total) * 100)}%)
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={(progress.current / progress.total) * 100}
                  sx={{ mt: 1, height: 6, borderRadius: 3 }}
                />
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Sprint Data Section */}
      {sprintData.length > 0 && (
        <Box ref={reportSectionRef}>
          {/* Search and Actions */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Search Sprints"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search sprints by name (e.g., 'CC Sprint', 'Codeflow')"
                    variant="outlined"
                    size="small"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                      endAdornment: searchTerm && (
                        <InputAdornment position="end">
                          <IconButton
                            size="small"
                            onClick={() => setSearchTerm('')}
                          >
                            <ClearIcon />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Chip
                        label={`Filtered: ${filteredCount}`}
                        color="primary"
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip
                        label={`Total: ${totalSprints}`}
                        color="default"
                        size="small"
                      />
                    </Box>
                    <Box>
                      <Tooltip title="Download CSV">
                        <IconButton color="primary" onClick={handleDownloadCSV} disabled={!sprintData.length}>
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Share Report">
                        <IconButton color="primary" onClick={handleShareReport} disabled={!sprintData.length}>
                          <ShareIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="API Information & Calculations">
                        <IconButton color="primary" onClick={() => setInfoDialogOpen(true)}>
                          <InfoIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="AI Insights">
                        <IconButton color="primary" onClick={handleAiInsights} disabled={!sprintData.length}>
                          <PsychologyIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Sprint Table */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Last {filteredData.length} Closed Sprints
              </Typography>
              <TableContainer component={Paper} elevation={0}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Sprint Name</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Start Date</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>End Date</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Initial Planned</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Completed</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Not Completed</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Added During Sprint</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Removed During Sprint</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Initial Planned SP</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Completed SP</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Completion %</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Insight</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredData.map((sprint, index) => (
                      <TableRow key={index} hover>
                        <TableCell sx={{ fontWeight: 500 }}>{sprint['Sprint Name']}</TableCell>
                        <TableCell>{sprint['Start Date']}</TableCell>
                        <TableCell>{sprint['End Date']}</TableCell>
                        <TableCell>{sprint['Initial Planned']}</TableCell>
                        <TableCell>{sprint['Completed']}</TableCell>
                        <TableCell>{sprint['Not Completed']}</TableCell>
                        <TableCell>{sprint['Added During Sprint']}</TableCell>
                        <TableCell>{sprint['Removed During Sprint']}</TableCell>
                        <TableCell>{sprint['Initial Planned SP'] || 0}</TableCell>
                        <TableCell>{sprint['Completed SP'] || 0}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" sx={{ minWidth: '40px', fontWeight: 500 }}>
                              {sprint['Completion %']}
                            </Typography>
                            <Box sx={{ flexGrow: 1, position: 'relative' }}>
                              <LinearProgress
                                variant="determinate"
                                value={parseFloat(sprint['Completion %'].replace('%', ''))}
                                color={getCompletionColor(sprint['Completion %'])}
                                sx={{
                                  height: 8,
                                  borderRadius: 4,
                                  backgroundColor: '#e0e0e0',
                                  '& .MuiLinearProgress-bar': {
                                    borderRadius: 4,
                                  }
                                }}
                              />
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" sx={{ minWidth: '40px', fontWeight: 500 }}>
                              {sprint['Insight']}
                            </Typography>
                            <Box sx={{ flexGrow: 1, position: 'relative' }}>
                              <LinearProgress
                                variant="determinate"
                                value={getInsightProgressValue(sprint['Insight'])}
                                color={getInsightColor(sprint['Insight'])}
                                sx={{
                                  height: 8,
                                  borderRadius: 4,
                                  backgroundColor: '#e0e0e0',
                                  '& .MuiLinearProgress-bar': {
                                    borderRadius: 4,
                                  }
                                }}
                              />
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={sprint['Status']}
                            color={sprint['Status'] === 'closed' ? 'default' : 'primary'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Sprint Analytics Charts */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'primary.main', mb: 3 }}>
              Sprint Analytics
            </Typography>
            
            <Grid container spacing={3}>
              {/* Completion Rate Trend */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                      Completion Rate Trend
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="Sprint Name" 
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          interval={0}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis 
                          domain={[0, 100]}
                          tickFormatter={(value) => `${value}%`}
                        />
                        <RechartsTooltip 
                          formatter={(value) => [`${value}%`, 'Completion Rate']}
                          labelFormatter={(label) => `Sprint: ${label}`}
                        />
                        <Line 
                          type="monotone" 
                          dataKey={(data) => parseFloat(data['Completion %'].replace('%', ''))}
                          stroke="#00ABE4" 
                          strokeWidth={3}
                          dot={{ fill: '#00ABE4', strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Sprint Scope Changes */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                      Sprint Scope Changes
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="Sprint Name" 
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          interval={0}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis />
                        <RechartsTooltip 
                          formatter={(value, name) => [value, name]}
                          labelFormatter={(label) => `Sprint: ${label}`}
                        />
                        <Bar 
                          dataKey="Added During Sprint" 
                          fill="#0066CC" 
                          name="Added During Sprint"
                        />
                        <Bar 
                          dataKey="Removed During Sprint" 
                          fill="#FF6B9D" 
                          name="Removed During Sprint"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Sprint Velocity Overview */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                      Sprint Velocity Overview
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="Sprint Name" 
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          interval={0}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis />
                        <RechartsTooltip 
                          formatter={(value, name) => [value, name]}
                          labelFormatter={(label) => `Sprint: ${label}`}
                        />
                        <Bar 
                          dataKey="Completed" 
                          stackId="a" 
                          fill="#00ABE4" 
                          name="Completed"
                        />
                        <Bar 
                          dataKey="Not Completed" 
                          stackId="a" 
                          fill="#FFD700" 
                          name="Not Completed"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
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
            Share Sprint Report
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {/* Report Summary */}
          <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Board ID</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{boardId}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Total Sprints</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{sprintData.length}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Report Type</Typography>
                  <Chip label="Sprint Analysis" size="small" color="primary" variant="outlined" />
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Average Completion</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Generated</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {new Date().toLocaleDateString()}
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Latest Sprint</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {sprintData[0]?.['Sprint Name'] || 'N/A'}
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
                  variant="contained"
                  color="warning"
                  startIcon={<EmailIcon />}
                  onClick={handleEmailWithScreenshot}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Email with Image
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<GetAppIcon />}
                  onClick={handleDownloadScreenshot}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Download Image
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<LinkIcon />}
                  onClick={handleCreateVisualShareLink}
                  disabled={!capturedScreenshot}
                  fullWidth
                >
                  Create Visual Share Link
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
                  startIcon={<LinkedInIcon />}
                  onClick={() => {
                    const text = `Sprint Analysis Report - Board ${boardId}\nTotal Sprints: ${sprintData.length}\nAverage Completion: ${(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%`;
                    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}&title=${encodeURIComponent('Sprint Analysis Report')}&summary=${encodeURIComponent(text)}`, '_blank');
                  }}
                  fullWidth
                >
                  Share to LinkedIn
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<WhatsAppIcon />}
                  onClick={() => {
                    const text = `🏃‍♂️ Sprint Analysis Report\n\n📋 Board: ${boardId}\n🎯 Sprints: ${sprintData.length}\n📈 Avg Completion: ${(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%\n\nView full report: ${shareUrl}`;
                    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
                  }}
                  fullWidth
                >
                  Share to WhatsApp
                </Button>
                <Button
                  variant="contained"
                  color="info"
                  startIcon={<LinkedInIcon />}
                  onClick={() => {
                    const text = `🏃‍♂️ *Sprint Analysis Report*\n\n📋 *Board:* ${boardId}\n🎯 *Sprints:* ${sprintData.length}\n📈 *Avg Completion:* ${(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%\n\nView full report: ${shareUrl}`;
                    navigator.clipboard.writeText(text);
                    setSnackbarMessage('Slack message copied! Paste it in your Slack channel.');
                    setSnackbarOpen(true);
                  }}
                  fullWidth
                >
                  Share to Slack
                </Button>
                <Button
                  variant="contained"
                  color="warning"
                  startIcon={<EmailIcon />}
                  onClick={() => {
                    const subject = `Sprint Analysis Report - Board ${boardId}`;
                    const body = `Hi,\n\nPlease find the sprint analysis report for Board ${boardId}.\n\nKey Highlights:\n• Total Sprints: ${sprintData.length}\n• Average Completion: ${(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%\n\nView full report: ${shareUrl}\n\nBest regards`;
                    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                  }}
                  fullWidth
                >
                  Share via Email
                </Button>
              </Box>
            </Grid>

            {/* Copy & Share Column */}
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                Copy & Share
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <FormControl fullWidth size="small">
                  <InputLabel>Format</InputLabel>
                  <Select value="executive" label="Format">
                    <MenuItem value="executive">Executive Summary</MenuItem>
                    <MenuItem value="detailed">Detailed Report</MenuItem>
                    <MenuItem value="brief">Brief Summary</MenuItem>
                  </Select>
                </FormControl>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<ContentCopyIcon />}
                  onClick={() => {
                    const summary = `SPRINT REPORT SUMMARY\n\nBoard ID: ${boardId}\nAnalysis Date: ${new Date().toLocaleDateString()}\nSprints Analyzed: ${sprintData.length}\n\nKEY METRICS:\n• Average Completion Rate: ${(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%\n• Total Completed Issues: ${sprintData.reduce((sum, s) => sum + s["Completed"], 0)}\n• Total Issues Not Completed: ${sprintData.reduce((sum, s) => sum + s["Not Completed"], 0)}\n• Total Added During Sprint: ${sprintData.reduce((sum, s) => sum + s["Added During Sprint"], 0)}\n• Total Removed During Sprint: ${sprintData.reduce((sum, s) => sum + s["Removed During Sprint"], 0)}\n\nView full report: ${shareUrl}`;
                    handleCopyToClipboard(summary);
                  }}
                  fullWidth
                >
                  Copy to Clipboard
                </Button>
                <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, maxHeight: 200, overflow: 'auto' }}>
                  <Typography variant="caption" color="text.secondary">
                    SPRINT REPORT SUMMARY
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Board ID: {boardId}<br />
                    Analysis Date: {new Date().toLocaleDateString()}<br />
                    Sprints Analyzed: {sprintData.length}<br />
                    <br />
                    KEY METRICS:<br />
                    • Average Completion Rate: {(sprintData.reduce((sum, sprint) => sum + parseFloat(sprint["Completion %"].replace('%', '')), 0) / sprintData.length).toFixed(1)}%<br />
                    • Total Completed Issues: {sprintData.reduce((sum, s) => sum + s["Completed"], 0)}<br />
                    • Total Issues Not Completed: {sprintData.reduce((sum, s) => sum + s["Not Completed"], 0)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Screenshot Preview */}
          {capturedScreenshot && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
                Screenshot Preview
              </Typography>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="center">
                    <img 
                      src={capturedScreenshot.dataUrl} 
                      alt="Report Screenshot" 
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: '300px', 
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }} 
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                    Screenshot captured successfully! Use the buttons above to share or download.
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Share Link Section */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
              Share Link
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <TextField
                fullWidth
                value={shareUrl}
                variant="outlined"
                size="small"
                InputProps={{ readOnly: true }}
              />
              <IconButton onClick={() => handleCopyToClipboard(shareUrl)}>
                <ContentCopyIcon />
              </IconButton>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              This link will expire in 7 days.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #e0e0e0' }}>
          <Button onClick={() => setShareDialogOpen(false)} variant="outlined">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Insights Dialog */}
      <Dialog open={aiInsightsDialogOpen} onClose={() => setAiInsightsDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ 
          borderBottom: '1px solid #e0e0e0', 
          pb: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
              AI-Powered Sprint Insights
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Powered by GPT-4 AI
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {aiInsightsLoading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
              <CircularProgress />
            </Box>
          ) : aiInsights ? (
            <Box>
              {/* Overall Sprint Health Assessment */}
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main', mb: 2, component: 'div' }}>
                Overall Sprint Health Assessment
              </Typography>
              <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
                <CardContent>
                  <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                    {aiInsights.overall_sprint_health_assessment || aiInsights.overall_assessment}
                  </Typography>
                </CardContent>
              </Card>

              {/* Actionable Recommendations */}
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main', mb: 2, component: 'div' }}>
                Actionable Recommendations
              </Typography>
              {(aiInsights.actionable_recommendations || []).map((rec, index) => (
                <Card key={index} sx={{ mb: 2, border: '1px solid #e0e0e0' }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                        {rec.title}
                      </Typography>
                      <Box display="flex" gap={1}>
                        <Chip 
                          label={rec.category} 
                          size="small" 
                          color="primary" 
                          variant="outlined"
                        />
                        <Chip 
                          label={rec.severity} 
                          size="small" 
                          color={
                            rec.severity === 'High' ? 'error' : 
                            rec.severity === 'Medium' ? 'warning' : 'success'
                          }
                        />
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>
                      {rec.description}
                    </Typography>
                  </CardContent>
                </Card>
              ))}

              {/* Key Observations */}
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: 'primary.main', mb: 2, component: 'div' }}>
                Key Observations
              </Typography>
              <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
                <CardContent>
                  <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    {(aiInsights.key_observations || []).map((observation, index) => (
                      <Typography key={index} component="li" variant="body2" sx={{ mb: 1, lineHeight: 1.5 }}>
                        {observation}
                      </Typography>
                    ))}
                  </Box>
                </CardContent>
              </Card>

              {aiInsights.fallback && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Using enhanced analysis engine. For more advanced AI insights, configure OpenAI settings.
                </Alert>
              )}
            </Box>
          ) : (
            <Typography>No insights available.</Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #e0e0e0' }}>
          <Button onClick={() => setAiInsightsDialogOpen(false)} variant="outlined">
            Close
          </Button>
          <Button 
            onClick={handleAiInsights} 
            variant="contained" 
            startIcon={<RefreshIcon />}
            disabled={aiInsightsLoading}
          >
            Regenerate Insights
          </Button>
        </DialogActions>
      </Dialog>

      {/* API Information Dialog */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ 
          borderBottom: '1px solid #e0e0e0', 
          pb: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <InfoIcon color="primary" />
          Jira API Information & Calculations
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom color="primary">
              🔗 Jira APIs Used
            </Typography>
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2" paragraph>
                <strong>1. Sprint Report API:</strong> <code>/rest/agile/1.0/board/&#123;boardId&#125;/sprint/&#123;sprintId&#125;/sprintreport</code>
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>2. Sprint API:</strong> <code>/rest/agile/1.0/board/&#123;boardId&#125;/sprint</code>
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>3. Issue API:</strong> <code>/rest/api/2/search</code> (for detailed issue information)
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom color="primary">
              📊 Data Calculations
            </Typography>
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2" paragraph>
                <strong>Start Date & End Date:</strong> Retrieved directly from Sprint API response fields <code>startDate</code> and <code>endDate</code>
                <br />
                <em>Result: ISO 8601 formatted dates (e.g., "2025-08-21T00:00:00.000Z")</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Initial Planned:</strong> Count of issues that were in the sprint at the beginning (before any changes)
                <br />
                <em>Calculation:</em> <code>sprintReport.completedIssuesInitialEstimateSum + sprintReport.issuesNotCompletedInitialEstimateSum</code>
                <br />
                <em>Result: Integer count of issues (e.g., 15, 0, -1)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Completed:</strong> Count of issues with status "Done" or "Closed" at sprint end
                <br />
                <em>Calculation:</em> <code>sprintReport.completedIssuesInitialEstimateSum</code>
                <br />
                <em>Result: Integer count (e.g., 22, 0, 12)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Not Completed:</strong> Count of issues that were planned but not completed
                <br />
                <em>Calculation:</em> <code>sprintReport.issuesNotCompletedInitialEstimateSum</code>
                <br />
                <em>Result: Integer count (e.g., 4, 0, 3)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Added During Sprint:</strong> Count of issues added to the sprint after it started
                <br />
                <em>Calculation:</em> <code>sprintReport.issueKeysAddedDuringSprint.length</code>
                <br />
                <em>Result: Integer count (e.g., 23, 1, 33)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Removed During Sprint:</strong> Count of issues removed from the sprint after it started
                <br />
                <em>Calculation:</em> <code>sprintReport.issueKeysRemovedDuringSprint.length</code>
                <br />
                <em>Result: Integer count (e.g., 1, 0, 13)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Initial Planned SP:</strong> Sum of story points for issues planned at sprint start
                <br />
                <em>Calculation:</em> <code>sprintReport.completedIssuesInitialEstimateSum + sprintReport.issuesNotCompletedInitialEstimateSum</code>
                <br />
                <em>Result: Decimal story points (e.g., 45.5, 0, -20)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Completed SP:</strong> Sum of story points for completed issues
                <br />
                <em>Calculation:</em> <code>sprintReport.completedIssuesEstimateSum</code>
                <br />
                <em>Result: Decimal story points (e.g., 38.0, 0, 12)</em>
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Completion %:</strong> Percentage of story points completed
                <br />
                <em>Calculation:</em> <code>Math.round((Completed SP / Initial Planned SP) × 100)</code>
                <br />
                <em>Result: Percentage (e.g., 84.6%, 100.0%, 57.1%)</em>
                <br />
                <em>Special Cases:</em> "N/A" when Initial Planned SP is 0 or negative
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom color="primary">
              🧠 Insight Generation
            </Typography>
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2" paragraph>
                <strong>Good Velocity (✔):</strong> 
                <br />
                <em>Criteria:</em> Completion % ≥ 80% AND scope stability &lt; 20%
                <br />
                <em>Calculation:</em> <code>completionPercent {'>='} 80 {'&&'} scopeChangePercent {'<'} 20</code>
                <br />
                <em>Result:</em> Green checkmark with "Good velocity" message
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Moderate Delivery Rate (!):</strong>
                <br />
                <em>Criteria:</em> Completion % between 50-79%
                <br />
                <em>Calculation:</em> <code>completionPercent {'>='} 50 {'&&'} completionPercent {'<'} 80</code>
                <br />
                <em>Result:</em> Orange exclamation with "Moderate delivery rate" message
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Low Delivery Rate (X):</strong>
                <br />
                <em>Criteria:</em> Completion % &lt; 50% OR no completed issues
                <br />
                <em>Calculation:</em> <code>completionPercent &#60; 50 || completedIssues === 0</code>
                <br />
                <em>Result:</em> Red X with "Low delivery rate" message
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Unstable Scope (!):</strong>
                <br />
                <em>Criteria:</em> High scope changes during sprint
                <br />
                <em>Calculation:</em> <code>scopeChangePercent = ((added + removed) / initialPlanned) × 100</code>
                <br />
                <em>Threshold:</em> &gt; 20% of initial planned issues
                <br />
                <em>Result:</em> Yellow exclamation with "Unstable scope" message
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Combined Insights:</strong>
                <br />
                <em>Multiple conditions can apply simultaneously:</em>
                <br />
                • "✔ Good velocity | ! Unstable scope" - Good completion but scope changes
                <br />
                • "! Moderate delivery rate | ! Unstable scope" - Moderate completion with scope issues
                <br />
                • "X Low delivery rate" - Poor performance
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom color="primary">
              📈 Data Sources
            </Typography>
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2" paragraph>
                • <strong>Sprint Report API:</strong> Provides comprehensive sprint metrics including completed, not completed, and scope changes
              </Typography>
              <Typography variant="body2" paragraph>
                • <strong>Issue Details:</strong> Fetched for story point calculations and status verification
              </Typography>
              <Typography variant="body2" paragraph>
                • <strong>Real-time Data:</strong> All calculations are based on current Jira data, not cached values
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom color="primary">
              ⚠️ Data Validation & Edge Cases
            </Typography>
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2" paragraph>
                <strong>Negative Values:</strong> Can occur when issues are removed from sprint after being completed
                <br />
                <em>Example:</em> Initial Planned: -1, Completed: 0 (issue was completed then removed)
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Zero Initial Planned:</strong> Sprint started with no planned issues
                <br />
                <em>Result:</em> Completion % shows "N/A" (division by zero protection)
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>High Scope Changes:</strong> More issues added/removed than initially planned
                <br />
                <em>Example:</em> Initial: 5, Added: 20, Removed: 3 (400% scope change)
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Missing Story Points:</strong> Issues without story point estimates
                <br />
                <em>Handling:</em> Treated as 0 story points in calculations
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>API Rate Limits:</strong> Jira API has rate limiting (100 requests/minute)
                <br />
                <em>Mitigation:</em> Requests are throttled and cached when possible
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: '1px solid #e0e0e0' }}>
          <Button onClick={() => setInfoDialogOpen(false)} variant="contained" color="primary">
            Close
          </Button>
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

export default SprintReport; 