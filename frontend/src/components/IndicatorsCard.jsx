import React from 'react';
import { Paper, Typography, Box, LinearProgress, Divider } from '@mui/material';

function RSIBar({ value }) {
  const pct = value ?? 50;
  const color = pct < 30 ? 'success' : pct > 70 ? 'error' : 'primary';
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="caption" color="text.secondary">Survendu (30)</Typography>
        <Typography variant="caption" fontWeight={700} color={`${color}.main`}>{pct.toFixed(2)}</Typography>
        <Typography variant="caption" color="text.secondary">Surachete (70)</Typography>
      </Box>
      <LinearProgress variant="determinate" value={Math.min(pct, 100)} color={color} sx={{ height: 8, borderRadius: 4 }} />
    </Box>
  );
}

export default function IndicatorsCard({ symbol, data }) {
  const loading = !data;
  const rsi = data?.rsi;
  const macd = data?.macd;
  const bb = data?.bollinger;

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>Indicateurs - {symbol}</Typography>
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary">RSI (14)</Typography>
        {loading ? <LinearProgress /> : <RSIBar value={rsi} />}
      </Box>
      <Divider sx={{ my: 1.5 }} />
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>MACD (12/26/9)</Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="caption" color="text.secondary">Ligne MACD</Typography>
          <Typography fontWeight={700} color={macd?.macd >= 0 ? 'success.main' : 'error.main'}>
            {loading ? '...' : macd?.macd?.toFixed(5)}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">Signal</Typography>
          <Typography fontWeight={700}>{loading ? '...' : macd?.signal?.toFixed(5)}</Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">Histo</Typography>
          <Typography fontWeight={700} color={macd?.histogram >= 0 ? 'success.main' : 'error.main'}>
            {loading ? '...' : macd?.histogram?.toFixed(5)}
          </Typography>
        </Box>
      </Box>
      <Divider sx={{ my: 1.5 }} />
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Bollinger (20)</Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {[['Haute', bb?.upper], ['Milieu', bb?.middle], ['Basse', bb?.lower]].map(([label, val]) => (
          <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption" color="text.secondary">{label}</Typography>
            <Typography variant="caption" fontWeight={700}>{loading ? '...' : val?.toFixed(5)}</Typography>
          </Box>
        ))}
      </Box>
    </Paper>
  );
}
