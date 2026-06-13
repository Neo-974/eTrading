import React from 'react';
import { Paper, Typography, Box, Chip, LinearProgress } from '@mui/material';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';

const impactColor = { High: 'error', Medium: 'warning', Low: 'default' };

export default function NewsCard({ events, loading }) {
  return (
    <Paper sx={{ p: 2, height: '100%', overflow: 'auto', maxHeight: 340 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <CalendarTodayIcon fontSize="small" color="primary" />
        <Typography variant="h6">Calendrier Economique</Typography>
      </Box>
      {loading && <LinearProgress />}
      {!loading && events.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          Aucun evenement disponible (Forex Factory peut bloquer le scraping serveur).
        </Typography>
      )}
      {events.slice(0, 8).map((ev, i) => (
        <Box key={i} sx={{
          display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1, p: 1,
          borderLeft: '3px solid',
          borderColor: ev.impact === 'High' ? 'error.main' : ev.impact === 'Medium' ? 'warning.main' : 'divider',
          borderRadius: '0 4px 4px 0',
        }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" fontWeight={600}>{ev.event}</Typography>
            <Typography variant="caption" color="text.secondary">{ev.time} · {ev.currency}</Typography>
          </Box>
          <Chip label={ev.impact} size="small" color={impactColor[ev.impact] || 'default'} variant="outlined" />
        </Box>
      ))}
    </Paper>
  );
}
