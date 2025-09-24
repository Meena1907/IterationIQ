import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Divider,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  People as PeopleIcon,
  Visibility as VisibilityIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import axios from 'axios';
import analytics from '../utils/analytics';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

const AnalyticsDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetails, setUserDetails] = useState(null);
  const [userDetailsLoading, setUserDetailsLoading] = useState(false);
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(90);

  useEffect(() => {
    fetchAnalyticsStats();
    // Track analytics dashboard view
    analytics.trackAnalyticsView('dashboard');
  }, []);

  const fetchAnalyticsStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get('/api/analytics/stats');
      setStats(response.data);
      
      // Track successful stats fetch
      analytics.trackEvent('analytics_stats_fetched', {
        total_users: response.data.total_users,
        active_users_24h: response.data.active_users_24h
      });
    } catch (err) {
      setError('Failed to fetch analytics data');
      analytics.trackError(err, { context: 'fetch_analytics_stats' });
    } finally {
      setLoading(false);
    }
  };

  const fetchUserDetails = async (userId) => {
    try {
      setUserDetailsLoading(true);
      const response = await axios.get(`/api/analytics/user/${userId}`);
      setUserDetails(response.data);
      
      // Track user details view
      analytics.trackEvent('user_details_viewed', { user_id: userId });
    } catch (err) {
      setError('Failed to fetch user details');
      analytics.trackError(err, { context: 'fetch_user_details' });
    } finally {
      setUserDetailsLoading(false);
    }
  };

  const handleCleanupData = async () => {
    try {
      await axios.post('/api/analytics/cleanup', { days_to_keep: cleanupDays });
      setCleanupDialogOpen(false);
      fetchAnalyticsStats(); // Refresh stats
      
      // Track cleanup action
      analytics.trackEvent('analytics_cleanup_performed', { days_to_keep: cleanupDays });
    } catch (err) {
      setError('Failed to cleanup data');
      analytics.trackError(err, { context: 'cleanup_analytics_data' });
    }
  };

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
    analytics.trackUserInteraction('tab_click', `analytics_tab_${newValue}`);
  };

  const handleUserClick = (userId) => {
    setSelectedUser(userId);
    fetchUserDetails(userId);
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  // Chart configurations
  const dailyActiveUsersChart = {
    labels: stats?.daily_active_users?.map(d => new Date(d.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Daily Active Users',
        data: stats?.daily_active_users?.map(d => d.users) || [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const topPagesChart = {
    labels: stats?.top_pages?.slice(0, 10).map(p => p.page) || [],
    datasets: [
      {
        label: 'Page Views',
        data: stats?.top_pages?.slice(0, 10).map(p => p.views) || [],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
          'rgba(199, 199, 199, 0.8)',
          'rgba(83, 102, 255, 0.8)',
          'rgba(255, 99, 255, 0.8)',
          'rgba(99, 255, 132, 0.8)',
        ],
      },
    ],
  };

  const userActivityChart = {
    labels: ['Total Users', 'Active (24h)', 'Active (7d)', 'Active (30d)'],
    datasets: [
      {
        label: 'User Count',
        data: [
          stats?.total_users || 0,
          stats?.active_users_24h || 0,
          stats?.active_users_7d || 0,
          stats?.active_users_30d || 0,
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 99, 132, 0.8)',
          'rgba(255, 205, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
        ],
      },
    ],
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchAnalyticsStats}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" display="flex" alignItems="center" gap={1}>
          <AnalyticsIcon />
          User Analytics
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchAnalyticsStats}
            data-analytics="refresh_analytics"
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setCleanupDialogOpen(true)}
            data-analytics="open_cleanup_dialog"
          >
            Cleanup
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <PeopleIcon color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4">{stats?.total_users || 0}</Typography>
                  <Typography color="textSecondary">Total Users</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <VisibilityIcon color="success" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4">{stats?.active_users_24h || 0}</Typography>
                  <Typography color="textSecondary">Active (24h)</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <TrendingUpIcon color="info" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4">{stats?.total_sessions || 0}</Typography>
                  <Typography color="textSecondary">Total Sessions</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <ScheduleIcon color="warning" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h4">{formatDuration(stats?.avg_session_duration || 0)}</Typography>
                  <Typography color="textSecondary">Avg Session</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different views */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={selectedTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="User Activity" />
          <Tab label="Page Analytics" />
          <Tab label="User Details" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {selectedTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>Daily Active Users (Last 30 Days)</Typography>
                <Line data={dailyActiveUsersChart} options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'top',
                    },
                  },
                }} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>User Activity</Typography>
                <Bar data={userActivityChart} options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      display: false,
                    },
                  },
                }} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {selectedTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>Session Statistics</Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">Total Page Views</Typography>
                    <Typography variant="h5">{stats?.total_page_views || 0}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">New Users Today</Typography>
                    <Typography variant="h5">{stats?.new_users_today || 0}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">Active Users (7 days)</Typography>
                    <Typography variant="h5">{stats?.active_users_7d || 0}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">Active Users (30 days)</Typography>
                    <Typography variant="h5">{stats?.active_users_30d || 0}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>Top Pages</Typography>
                <Doughnut data={topPagesChart} options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    },
                  },
                }} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {selectedTab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Top Pages by Views</Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Page</TableCell>
                    <TableCell align="right">Views</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {stats?.top_pages?.map((page, index) => (
                    <TableRow key={index}>
                      <TableCell>{page.page}</TableCell>
                      <TableCell align="right">{page.views}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {selectedTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>User Details</Typography>
            {userDetails ? (
              <Box>
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">User ID</Typography>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                      {userDetails.user_id}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">IP Address</Typography>
                    <Typography variant="body1">{userDetails.ip_address}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">First Seen</Typography>
                    <Typography variant="body1">{formatDate(userDetails.first_seen)}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">Last Seen</Typography>
                    <Typography variant="body1">{formatDate(userDetails.last_seen)}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">Total Sessions</Typography>
                    <Typography variant="body1">{userDetails.total_sessions}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary">Total Page Views</Typography>
                    <Typography variant="body1">{userDetails.total_page_views}</Typography>
                  </Grid>
                </Grid>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="h6" mb={2}>Recent Page Views</Typography>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Page</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Time</TableCell>
                        <TableCell align="right">Load Time</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {userDetails.recent_page_views?.map((view, index) => (
                        <TableRow key={index}>
                          <TableCell>{view.page_path}</TableCell>
                          <TableCell>{view.page_title}</TableCell>
                          <TableCell>{formatDate(view.timestamp)}</TableCell>
                          <TableCell align="right">{view.load_time_ms}ms</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ) : (
              <Typography color="textSecondary">
                Click on a user ID to view detailed information
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Cleanup Dialog */}
      <Dialog open={cleanupDialogOpen} onClose={() => setCleanupDialogOpen(false)}>
        <DialogTitle>
          Cleanup Analytics Data
          <IconButton
            onClick={() => setCleanupDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" mb={2}>
            This will permanently delete analytics data older than the specified number of days.
          </Typography>
          <TextField
            label="Days to Keep"
            type="number"
            value={cleanupDays}
            onChange={(e) => setCleanupDays(parseInt(e.target.value) || 90)}
            fullWidth
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCleanupDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCleanupData} color="warning" variant="contained">
            Cleanup Data
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AnalyticsDashboard;
