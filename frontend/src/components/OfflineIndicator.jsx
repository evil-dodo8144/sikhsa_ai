import React, { useState, useEffect } from 'react';
import {
  Alert,
  Snackbar,
  Box,
  Typography,
  Button,
  Badge
} from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SyncIcon from '@mui/icons-material/Sync';
import { syncService } from '../services/sync_service';

const OfflineIndicator = () => {
  const [open, setOpen] = useState(true);
  const [queuedCount, setQueuedCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const checkQueue = () => {
      const count = syncService.getQueuedCount();
      setQueuedCount(count);
    };
    
    checkQueue();
    const interval = setInterval(checkQueue, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncService.sync();
      setQueuedCount(0);
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <Snackbar
      open={open}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert 
        severity="warning"
        icon={<WifiOffIcon />}
        action={
          queuedCount > 0 && (
            <Button 
              color="inherit" 
              size="small"
              onClick={handleSync}
              disabled={syncing}
              startIcon={<SyncIcon />}
            >
              {syncing ? 'Syncing...' : `Sync (${queuedCount})`}
            </Button>
          )
        }
        sx={{ width: '100%' }}
      >
        <Box>
          <Typography variant="body2">
            You are currently offline
          </Typography>
          {queuedCount > 0 && (
            <Typography variant="caption">
              {queuedCount} question{queuedCount > 1 ? 's' : ''} queued for sync
            </Typography>
          )}
        </Box>
      </Alert>
    </Snackbar>
  );
};

export default OfflineIndicator;