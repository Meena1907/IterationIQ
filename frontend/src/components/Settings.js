import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Settings = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: 'primary.main' }}>
        Settings
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1" color="text.secondary">
            Settings component will be implemented here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Settings; 