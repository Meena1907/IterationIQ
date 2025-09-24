import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Grid,
  Chip,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Link,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Download as DownloadIcon,
  Psychology as PsychologyIcon,
  Monitor as MonitorIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Link as LinkIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Help as HelpIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // JIRA Configuration
  const [jiraConfig, setJiraConfig] = useState({
    url: '',
    email: '',
    token: '',
  });
  const [showToken, setShowToken] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState({ status: 'not_tested', message: 'Not tested' });

  // Export Options
  const [exportConfig, setExportConfig] = useState({
    includeCharts: true,
    includeInsights: true,
    format: 'csv',
    autoExport: false,
  });

  // AI Configuration
  const [aiConfig, setAiConfig] = useState({
    apiKey: '',
    model: 'gpt-4',
    enabled: false,
  });
  const [showAiKey, setShowAiKey] = useState(false);
  const [aiStatus, setAiStatus] = useState({ status: 'not_tested', message: 'Not tested' });

  // UI Preferences
  const [uiConfig, setUiConfig] = useState({
    theme: 'light',
    compactMode: false,
    showAnimations: true,
    autoRefresh: true,
    refreshInterval: 30,
  });

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      // Load JIRA settings
      const jiraResponse = await fetch('/api/settings/load-jira');
      if (jiraResponse.ok) {
        const jiraData = await jiraResponse.json();
        setJiraConfig({
          url: jiraData.jira_url || '',
          email: jiraData.jira_email || '',
          token: jiraData.jira_token || '',
        });
      }

      // Load AI settings
      const aiResponse = await fetch('/api/settings/load-openai');
      if (aiResponse.ok) {
        const aiData = await aiResponse.json();
        setAiConfig({
          apiKey: aiData.api_key || '',
          model: aiData.model || 'gpt-4',
          enabled: aiData.ai_enabled || false,
        });
        setAiStatus({
          status: aiData.ai_enabled ? 'connected' : 'not_configured',
          message: aiData.ai_enabled ? 'Connected' : 'Not configured'
        });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const testJiraConnection = async () => {
    setConnectionStatus({ status: 'testing', message: 'Testing connection...' });
    try {
      const response = await fetch('/api/settings/test-jira', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jiraConfig),
      });

      if (response.ok) {
        setConnectionStatus({ status: 'connected', message: 'Connection successful!' });
        setMessage({ type: 'success', text: 'JIRA connection test successful!' });
      } else {
        const error = await response.json();
        setConnectionStatus({ status: 'error', message: error.error || 'Connection failed' });
        setMessage({ type: 'error', text: 'JIRA connection test failed' });
      }
    } catch (error) {
      setConnectionStatus({ status: 'error', message: 'Connection failed' });
      setMessage({ type: 'error', text: 'JIRA connection test failed' });
    }
  };

  const saveJiraConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/settings/save-jira', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jiraConfig),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'JIRA settings saved successfully!' });
      } else {
        setMessage({ type: 'error', text: 'Failed to save JIRA settings' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save JIRA settings' });
    } finally {
      setSaving(false);
    }
  };

  const testAiConnection = async () => {
    setAiStatus({ status: 'testing', message: 'Testing AI connection...' });
    try {
      const response = await fetch('/api/settings/test-openai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: aiConfig.apiKey }),
      });

      if (response.ok) {
        setAiStatus({ status: 'connected', message: 'AI connection successful!' });
        setMessage({ type: 'success', text: 'AI connection test successful!' });
      } else {
        const error = await response.json();
        setAiStatus({ status: 'error', message: error.error || 'Connection failed' });
        setMessage({ type: 'error', text: 'AI connection test failed' });
      }
    } catch (error) {
      setAiStatus({ status: 'error', message: 'Connection failed' });
      setMessage({ type: 'error', text: 'AI connection test failed' });
    }
  };

  const saveAiConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/settings/save-openai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(aiConfig),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'AI settings saved successfully!' });
      } else {
        setMessage({ type: 'error', text: 'Failed to save AI settings' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save AI settings' });
    } finally {
      setSaving(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'testing':
        return <CircularProgress size={20} />;
      default:
        return <HelpIcon color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'success.main';
      case 'error':
        return 'error.main';
      case 'testing':
        return 'info.main';
      default:
        return 'text.secondary';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Application Settings
        </Typography>
      </Box>

      {/* Message Alert */}
      {message.text && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage({ type: '', text: '' })}>
          {message.text}
        </Alert>
      )}

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
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
            icon={<StorageIcon />}
            label="JIRA Configuration"
            iconPosition="start"
          />
          <Tab
            icon={<DownloadIcon />}
            label="Export Options"
            iconPosition="start"
          />
          <Tab
            icon={<PsychologyIcon />}
            label="AI Configuration"
            iconPosition="start"
          />
          <Tab
            icon={<MonitorIcon />}
            label="UI Preferences"
            iconPosition="start"
          />
        </Tabs>
      </Card>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  JIRA Connection Settings
                </Typography>
                
                <TextField
                  fullWidth
                  label="JIRA URL"
                  value={jiraConfig.url}
                  onChange={(e) => setJiraConfig({ ...jiraConfig, url: e.target.value })}
                  placeholder="https://yourcompany.atlassian.net"
                  helperText="Your JIRA instance URL"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="Email"
                  value={jiraConfig.email}
                  onChange={(e) => setJiraConfig({ ...jiraConfig, email: e.target.value })}
                  placeholder="your.email@company.com"
                  helperText="Your JIRA account email"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="API Token"
                  type={showToken ? 'text' : 'password'}
                  value={jiraConfig.token}
                  onChange={(e) => setJiraConfig({ ...jiraConfig, token: e.target.value })}
                  placeholder="Enter your JIRA API token"
                  helperText={
                    <Box>
                      <Link href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener">
                        Generate API Token <LinkIcon sx={{ fontSize: 16, ml: 0.5 }} />
                      </Link>
                    </Box>
                  }
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowToken(!showToken)}>
                          {showToken ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 3 }}
                />

                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    startIcon={<RefreshIcon />}
                    onClick={testJiraConnection}
                    disabled={!jiraConfig.url || !jiraConfig.email || !jiraConfig.token}
                  >
                    Test Connection
                  </Button>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<SaveIcon />}
                    onClick={saveJiraConfig}
                    disabled={saving}
                  >
                    Save Configuration
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ backgroundColor: 'primary.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Connection Status
                </Typography>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  {getStatusIcon(connectionStatus.status)}
                  <Typography variant="body2">
                    {connectionStatus.message}
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Test your JIRA connection to ensure proper configuration.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Export Options
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={exportConfig.includeCharts}
                      onChange={(e) => setExportConfig({ ...exportConfig, includeCharts: e.target.checked })}
                    />
                  }
                  label="Include Charts in Exports"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={exportConfig.includeInsights}
                      onChange={(e) => setExportConfig({ ...exportConfig, includeInsights: e.target.checked })}
                    />
                  }
                  label="Include AI Insights"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Export Format</InputLabel>
                  <Select
                    value={exportConfig.format}
                    onChange={(e) => setExportConfig({ ...exportConfig, format: e.target.value })}
                    label="Export Format"
                  >
                    <MenuItem value="csv">CSV</MenuItem>
                    <MenuItem value="excel">Excel</MenuItem>
                    <MenuItem value="pdf">PDF</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={exportConfig.autoExport}
                      onChange={(e) => setExportConfig({ ...exportConfig, autoExport: e.target.checked })}
                    />
                  }
                  label="Auto-export on Report Generation"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  AI Configuration
                </Typography>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={aiConfig.enabled}
                      onChange={(e) => setAiConfig({ ...aiConfig, enabled: e.target.checked })}
                    />
                  }
                  label="Enable AI Insights"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="OpenAI API Key"
                  type={showAiKey ? 'text' : 'password'}
                  value={aiConfig.apiKey}
                  onChange={(e) => setAiConfig({ ...aiConfig, apiKey: e.target.value })}
                  placeholder="Enter your OpenAI API key"
                  disabled={!aiConfig.enabled}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowAiKey(!showAiKey)}>
                          {showAiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 3 }}
                />

                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>AI Model</InputLabel>
                  <Select
                    value={aiConfig.model}
                    onChange={(e) => setAiConfig({ ...aiConfig, model: e.target.value })}
                    label="AI Model"
                    disabled={!aiConfig.enabled}
                  >
                    <MenuItem value="gpt-4">GPT-4</MenuItem>
                    <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                  </Select>
                </FormControl>

                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    startIcon={<RefreshIcon />}
                    onClick={testAiConnection}
                    disabled={!aiConfig.enabled || !aiConfig.apiKey}
                  >
                    Test AI Connection
                  </Button>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<SaveIcon />}
                    onClick={saveAiConfig}
                    disabled={saving}
                  >
                    Save AI Settings
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ backgroundColor: 'primary.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  AI Status
                </Typography>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  {getStatusIcon(aiStatus.status)}
                  <Typography variant="body2">
                    {aiStatus.message}
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Test your AI connection to enable intelligent insights.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              UI Preferences
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={uiConfig.theme}
                    onChange={(e) => setUiConfig({ ...uiConfig, theme: e.target.value })}
                    label="Theme"
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto (System)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Refresh Interval (seconds)</InputLabel>
                  <Select
                    value={uiConfig.refreshInterval}
                    onChange={(e) => setUiConfig({ ...uiConfig, refreshInterval: e.target.value })}
                    label="Refresh Interval (seconds)"
                  >
                    <MenuItem value={15}>15 seconds</MenuItem>
                    <MenuItem value={30}>30 seconds</MenuItem>
                    <MenuItem value={60}>1 minute</MenuItem>
                    <MenuItem value={300}>5 minutes</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={uiConfig.compactMode}
                      onChange={(e) => setUiConfig({ ...uiConfig, compactMode: e.target.checked })}
                    />
                  }
                  label="Compact Mode"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={uiConfig.showAnimations}
                      onChange={(e) => setUiConfig({ ...uiConfig, showAnimations: e.target.checked })}
                    />
                  }
                  label="Show Animations"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={uiConfig.autoRefresh}
                      onChange={(e) => setUiConfig({ ...uiConfig, autoRefresh: e.target.checked })}
                    />
                  }
                  label="Auto Refresh"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Global Actions */}
      <Box display="flex" justifyContent="space-between" mt={3}>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadSettings}
            disabled={loading}
          >
            Reset to Saved
          </Button>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={() => {
              // Save all settings
              saveJiraConfig();
              saveAiConfig();
              setMessage({ type: 'success', text: 'All settings saved successfully!' });
            }}
            disabled={saving}
          >
            Save All Settings
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default Settings; 