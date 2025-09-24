import { Box, Typography, Chip, Tooltip } from '@mui/material';
import { Devices as DevicesIcon } from '@mui/icons-material';

const DeviceCounter = () => {
  const [deviceCount, setDeviceCount] = useState(0);
  const [totalAccesses, setTotalAccesses] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Track device access when component mounts
    trackDeviceAccess();
    
    // Get current device count
    fetchDeviceCount();
  }, []);

  const trackDeviceAccess = async () => {
    try {
      const response = await fetch('/api/device/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setDeviceCount(data.device_count);
      }
    } catch (error) {
      console.error('Error tracking device access:', error);
    }
  };

  const fetchDeviceCount = async () => {
    try {
      const response = await fetch('/api/device/count');
      
      if (response.ok) {
        const data = await response.json();
        setDeviceCount(data.device_count);
        setTotalAccesses(data.total_accesses);
      }
    } catch (error) {
      console.error('Error fetching device count:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return null; // Don't show anything while loading
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
      }}
    >
      <Tooltip 
        title={`Total unique devices: ${deviceCount} | Total accesses: ${totalAccesses}`}
        arrow
      >
        <Chip
          icon={<DevicesIcon sx={{ fontSize: 16 }} />}
          label={`${deviceCount} device${deviceCount !== 1 ? 's' : ''}`}
          size="small"
          sx={{
            backgroundColor: 'rgba(0, 171, 228, 0.1)',
            color: 'primary.main',
            border: '1px solid rgba(0, 171, 228, 0.3)',
            '&:hover': {
              backgroundColor: 'rgba(0, 171, 228, 0.2)',
            },
          }}
        />
      </Tooltip>
    </Box>
  );
};

export default DeviceCounter;
