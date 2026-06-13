import React from 'react';
import { Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Box } from '@mui/material';

export default function TradeList({ trades }) {
  const open = trades.filter((t) => t.status === 'OPEN');
  return (
    <Paper sx={{ p: 2, overflow: 'auto', maxHeight: 400 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="h6">Trades Ouverts</Typography>
        <Chip label={`${open.length} ouvert(s)`} size="small" color="primary" variant="outlined" />
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Symbole</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Prix d'entree</TableCell>
              <TableCell>SL</TableCell>
              <TableCell>TP</TableCell>
              <TableCell>Mode</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {open.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">Aucun trade ouvert</Typography>
                </TableCell>
              </TableRow>
            ) : (
              open.map((t, i) => (
                <TableRow key={t.id || i} hover>
                  <TableCell><strong>{t.symbol}</strong></TableCell>
                  <TableCell><Chip label={t.action} size="small" color={t.action === 'BUY' ? 'success' : 'error'} /></TableCell>
                  <TableCell>{t.open_price?.toFixed(5)}</TableCell>
                  <TableCell sx={{ color: 'error.main' }}>{t.sl?.toFixed(5)}</TableCell>
                  <TableCell sx={{ color: 'success.main' }}>{t.tp?.toFixed(5)}</TableCell>
                  <TableCell><Chip label={t.mode || 'demo'} size="small" color={t.mode === 'live' ? 'error' : 'warning'} variant="outlined" /></TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
