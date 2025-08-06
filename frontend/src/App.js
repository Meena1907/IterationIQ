import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Grid,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  ThemeProvider,
  createTheme,
  CssBaseline,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Home as HomeIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';
import Dashboard from './components/Dashboard';
import SprintReport from './components/SprintReport';
import CapacityAnalysis from './components/CapacityAnalysis';
import Settings from './components/Settings';
import BestPractices from './components/BestPractices';
import SprintCross from './components/SprintCross';

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);

  // Create theme based on dark mode state
  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#00ABE4',
      },
      secondary: {
        main: '#0066CC',
      },
      background: {
        default: darkMode ? '#121212' : '#f5f5f5',
        paper: darkMode ? '#1e1e1e' : '#ffffff',
      },
    },
    components: {
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: darkMode 
              ? 'linear-gradient(90deg, #1a1a1a 0%, #2d2d2d 100%)' 
              : 'linear-gradient(90deg, #00ABE4 0%, #0066CC 100%)',
          },
        },
      },
    },
  });



  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return <Dashboard onNavigate={setActiveTab} />;
      case 1:
        return <SprintReport />;
      case 2:
        return <CapacityAnalysis />;
      case 3:
        return <Settings />;
      case 4:
        return <BestPractices />;
      case 5:
        return <SprintCross />;
      default:
        return <Dashboard onNavigate={setActiveTab} />;
    }
  };



  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', backgroundColor: 'background.default' }}>
        {/* App Bar */}
        <AppBar position="static" elevation={0}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600, color: 'white' }}>
              🚀 Spark - Sprint Analytics
            </Typography>
            
            {/* Home Button */}
            <Tooltip title="Dashboard">
              <IconButton 
                color="inherit" 
                onClick={() => setActiveTab(0)}
                sx={{ mr: 1, color: 'white' }}
              >
                <HomeIcon sx={{ fontSize: 28 }} />
              </IconButton>
            </Tooltip>
            
            {/* Dark Mode Toggle */}
            <Tooltip title={darkMode ? 'Light Mode' : 'Dark Mode'}>
              <IconButton color="inherit" onClick={toggleDarkMode} sx={{ mr: 1, color: 'white' }}>
                {darkMode ? <LightModeIcon sx={{ fontSize: 28 }} /> : <DarkModeIcon sx={{ fontSize: 28 }} />}
              </IconButton>
            </Tooltip>
            
            {/* Settings */}
            <Tooltip title="Settings">
              <IconButton 
                color="inherit" 
                onClick={() => setSettingsDialogOpen(true)}
                sx={{ color: 'white' }}
              >
                <SettingsIcon sx={{ fontSize: 28 }} />
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Settings Dialog */}
        <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ 
            borderBottom: '1px solid #e0e0e0', 
            pb: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
              Settings
            </Typography>
          </DialogTitle>
          <DialogContent sx={{ pt: 3 }}>
            <Settings />
          </DialogContent>
          <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #e0e0e0' }}>
            <Button onClick={() => setSettingsDialogOpen(false)} variant="outlined">
              Close
            </Button>
          </DialogActions>
        </Dialog>

        {/* Main Content */}
        <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
          <Grid container spacing={3}>
            {/* Main Content Area */}
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
    </ThemeProvider>
  );
}

export default App; 