import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material';
import { TradingAPI } from '../api/client';

function StatCard({ label, value, color }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center', flex: 1 }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="h5" fontWeight={700} color={color}>{value}</Typography>
    </Paper>
  );
}

export default function History() {
  const [trades, setTrades] = useState([]);
  useEffect(() => { TradingAPI.trades().then(setTrades).catch(console.error); }, []);

  const closed = trades.filter((t) => t.status === 'CLOSED');
  const wins = closed.filter((t) => t.result === 'WIN');
  const losses = closed.filter((t) => t.result === 'LOSS');
  const winRate = closed.length > 0 ? ((wins.length / closed.length) * 100).toFixed(1) : '...';
  const totalProfit = closed.reduce((s, t) => s + (t.profit || 0), 0);
  const grossWin = wins.reduce((s, t) => s + (t.profit || 0), 0);
  const grossLoss = Math.abs(losses.reduce((s, t) => s + (t.profit || 0), 0));
  const profitFactor = grossLoss > 0 ? (grossWin / grossLoss).toFixed(2) : '...';

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>Historique des Trades</Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <StatCard label="Trades fermes" value={closed.length} />
        <StatCard label="Win Rate" value={winRate !== '...' ? `${winRate}%` : '...'} color={winRate >= 50 ? 'success.main' : 'error.main'} />
        <StatCard label="Profit Factor" value={profitFactor} color={profitFactor >= 1 ? 'success.main' : 'error.main'} />
        <StatCard label="Profit Total" value={`${totalProfit >= 0 ? '+' : ''}${totalProfit.toFixed(2)} $`} color={totalProfit >= 0 ? 'success.main' : 'error.main'} />
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Symbole</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Entree</TableCell>
              <TableCell>Sortie</TableCell>
              <TableCell>Mode</TableCell>
              <TableCell>Resultat</TableCell>
              <TableCell align="right">Profit ($)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>Aucun trade enregistre</Typography>
                </TableCell>
              </TableRow>
            ) : (
              trades.map((t, i) => (
                <TableRow key={t.id || i} hover>
                  <TableCell>{new Date(t.created_at).toLocaleString('fr-FR')}</TableCell>
                  <TableCell><strong>{t.symbol}</strong></TableCell>
                  <TableCell><Chip label={t.action} size="small" color={t.action === 'BUY' ? 'success' : 'error'} /></TableCell>
                  <TableCell>{t.open_price?.toFixed(5)}</TableCell>
                  <TableCell>{t.close_price?.toFixed(5) || '-'}</TableCell>
                  <TableCell><Chip label={t.mode || 'demo'} size="small" variant="outlined" color={t.mode === 'live' ? 'error' : 'warning'} /></TableCell>
                  <TableCell>
                    {t.result ? (
                      <Chip label={t.result} size="small" color={t.result === 'WIN' ? 'success' : 'error'} />
                    ) : (
                      <Chip label={t.status} size="small" color="primary" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell align="right" sx={{ color: (t.profit || 0) >= 0 ? 'success.main' : 'error.main', fontWeight: 700 }}>
                    {t.profit != null ? `${t.profit >= 0 ? '+' : ''}${t.profit.toFixed(2)}` : '-'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
