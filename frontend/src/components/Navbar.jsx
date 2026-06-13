import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Chip } from '@mui/material';
import { Link } from 'react-router-dom';
import ShowChartIcon from '@mui/icons-material/ShowChart';

export default function Navbar({ mode }) {
  return (
    <AppBar position="static" sx={{ background: '#1a237e' }}>
      <Toolbar>
        <ShowChartIcon sx={{ mr: 1 }} />
        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
          NeoTechno Trading Bot
        </Typography>
        {mode && (
          <Chip
            label={mode === 'demo' ? 'MODE DEMO' : 'MODE LIVE'}
            color={mode === 'demo' ? 'warning' : 'error'}
            size="small"
            sx={{ mr: 2, fontWeight: 700 }}
          />
        )}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button color="inherit" component={Link} to="/">Tableau de Bord</Button>
          <Button color="inherit" component={Link} to="/history">Historique</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
