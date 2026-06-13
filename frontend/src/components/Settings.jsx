import React, { useState, useEffect } from 'react';
import {
  Paper, Typography, Slider, TextField, Button, Box,
  FormControl, InputLabel, Select, MenuItem, Checkbox,
  ListItemText, OutlinedInput, Chip, Divider,
} from '@mui/material';

const SYMBOLS = ['EURUSD', 'GBPUSD', 'BTCUSD', 'ETHUSD'];

export default function Settings({ settings, onSave }) {
  const [local, setLocal] = useState(settings);
  useEffect(() => { setLocal(settings); }, [settings]);
  const set = (key, val) => setLocal((prev) => ({ ...prev, [key]: val }));

  const row = (label, key, min, max, step) => (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="body2" gutterBottom>{label}</Typography>
        <Typography variant="body2" fontWeight={700} color="primary.main">{local[key]}</Typography>
      </Box>
      <Slider value={local[key]} onChange={(_, v) => set(key, v)} min={min} max={max} step={step} size="small" />
      <TextField fullWidth size="small" type="number" value={local[key]}
        onChange={(e) => set(key, parseFloat(e.target.value))}
        inputProps={{ min, max, step }} sx={{ mt: 0.5 }} />
    </Box>
  );

  return (
    <Paper sx={{ p: 2, height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" gutterBottom>Parametres du Bot</Typography>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Indicateurs</Typography>
      {row('Seuil RSI Achat (survente)', 'rsiBuyThreshold', 10, 40, 1)}
      {row('Seuil RSI Vente (surachete)', 'rsiSellThreshold', 60, 90, 1)}
      {row('Periode RSI', 'rsiPeriod', 7, 21, 1)}
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Gestion du Risque</Typography>
      {row('Taille du Lot', 'lotSize', 0.01, 1, 0.01)}
      {row('Stop-Loss (Pips)', 'stopLossPips', 10, 100, 5)}
      {row('Take-Profit (Pips)', 'takeProfitPips', 20, 200, 5)}
      {row('Perte Max Quotidienne (%)', 'maxDailyLossPercent', 1, 20, 0.5)}
      {row('Objectif Profit Quotidien (%)', 'targetDailyProfitPercent', 0.5, 10, 0.5)}
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Symboles a trader</Typography>
      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
        <InputLabel>Symboles</InputLabel>
        <Select multiple value={local.symbols || []}
          onChange={(e) => set('symbols', e.target.value)}
          input={<OutlinedInput label="Symboles" />}
          renderValue={(sel) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {sel.map((v) => <Chip key={v} label={v} size="small" />)}
            </Box>
          )}>
          {SYMBOLS.map((s) => (
            <MenuItem key={s} value={s}>
              <Checkbox checked={(local.symbols || []).includes(s)} />
              <ListItemText primary={s} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Button variant="contained" color="primary" fullWidth onClick={() => onSave(local)}>
        Sauvegarder
      </Button>
    </Paper>
  );
}
