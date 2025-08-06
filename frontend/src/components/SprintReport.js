import React, { useState, useEffect } from 'react';
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
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

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

    setLoading(true);
    setError('');
    setSprintData([]);

    try {
      const response = await fetch(`/api/jira_sprint_report_stream?board_id=${boardId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch sprint data');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'sprint_result') {
                setSprintData(prev => [...prev, data.data]);
              }
            } catch (e) {
              // Ignore parsing errors for non-JSON lines
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to generate sprint report');
    } finally {
      setLoading(false);
    }
  };

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

      {/* Sprint Data Section */}
      {sprintData.length > 0 && (
        <Box>
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
                        <IconButton color="primary">
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Share Report">
                        <IconButton color="primary">
                          <ShareIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="AI Insights">
                        <IconButton color="primary">
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
                        <TableCell>
                          <Chip
                            label={sprint['Completion %']}
                            color={getCompletionColor(sprint['Completion %'])}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={sprint['Insight']}
                            color={getInsightColor(sprint['Insight'])}
                            size="small"
                            icon={
                              getInsightColor(sprint['Insight']) === 'success' ? <CheckCircleIcon /> :
                              getInsightColor(sprint['Insight']) === 'error' ? <ErrorIcon /> :
                              <WarningIcon />
                            }
                          />
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
        </Box>
      )}
    </Box>
  );
};

export default SprintReport; 