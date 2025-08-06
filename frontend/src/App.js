import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import SprintReport from './components/SprintReport';
import CapacityAnalysis from './components/CapacityAnalysis';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return <SprintReport />;
      case 1:
        return <CapacityAnalysis />;
      case 2:
        return <Settings />;
      default:
        return <SprintReport />;
    }
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: 'background.default' }}>
      {/* App Bar */}
      <AppBar position="static" elevation={0} sx={{ background: 'linear-gradient(90deg, #00ABE4 0%, #0066CC 100%)' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            🚀 Jira TPM - Sprint Analytics
          </Typography>
          <Tooltip title="Refresh">
            <IconButton color="inherit" onClick={() => window.location.reload()}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        <Grid container spacing={3}>
          {/* Navigation Tabs */}
          <Grid item xs={12}>
            <Paper elevation={0} sx={{ borderRadius: 2 }}>
              <Tabs
                value={activeTab}
                onChange={handleTabChange}
                variant="fullWidth"
                sx={{
                  '& .MuiTab-root': {
                    minHeight: 64,
                    fontSize: '1rem',
                    fontWeight: 500,
                  },
                }}
              >
                <Tab
                  icon={<AssessmentIcon />}
                  label="Sprint Report"
                  iconPosition="start"
                />
                <Tab
                  icon={<PeopleIcon />}
                  label="Capacity Analysis"
                  iconPosition="start"
                />
                <Tab
                  icon={<SettingsIcon />}
                  label="Settings"
                  iconPosition="start"
                />
              </Tabs>
            </Paper>
          </Grid>

          {/* Tab Content */}
          <Grid item xs={12}>
            <Paper elevation={0} sx={{ borderRadius: 2, p: 3, minHeight: '70vh' }}>
              {loading ? (
                <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                  <CircularProgress size={60} />
                </Box>
              ) : (
                renderTabContent()
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App; 