import React from 'react';
import { Paper, Box, Typography, Chip } from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';

export default function StatusBar({ status }) {
  if (!status) return null;
  const { mode, broker, connected, account } = status;
  return (
    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AccountBalanceWalletIcon color="primary" />
        <Typography variant="h6" fontWeight={700}>
          {account?.balance?.toFixed(2)} {account?.currency}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          (Equity: {account?.equity?.toFixed(2)})
        </Typography>
      </Box>
      <Chip label={`Broker: ${broker}`} variant="outlined" size="small" color={connected ? 'success' : 'error'} />
      <Chip
        label={mode === 'demo' ? 'DEMO - trades simules' : 'LIVE'}
        color={mode === 'demo' ? 'warning' : 'error'}
        size="small"
        variant="outlined"
      />
    </Paper>
  );
}
