import React, { useState, useEffect, useCallback } from 'react';
import { Grid, Paper, Typography, Button, Box, Snackbar, Alert } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { TradingAPI } from '../api/client';
import StatusBar from '../components/StatusBar';
import IndicatorsCard from '../components/IndicatorsCard';
import NewsCard from '../components/NewsCard';
import Charts from '../components/Charts';
import Settings from '../components/Settings';
import TradeList from '../components/TradeList';

const DEFAULT_SETTINGS = {
  rsiPeriod: 14, rsiBuyThreshold: 30, rsiSellThreshold: 70,
  lotSize: 0.1, stopLossPips: 30, takeProfitPips: 60,
  maxDailyLossPercent: 5, targetDailyProfitPercent: 1,
  symbols: ['EURUSD', 'GBPUSD'],
};

export default function Home() {
  const [status, setStatus] = useState(null);
  const [trades, setTrades] = useState([]);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [indicators, setIndicators] = useState(null);
  const [news, setNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'info' });

  const notify = (msg, severity = 'success') => setSnack({ open: true, msg, severity });

  const refreshAll = useCallback(async () => {
    try {
      const [s, t, ind] = await Promise.all([TradingAPI.status(), TradingAPI.trades(), TradingAPI.indicators('EURUSD')]);
      setStatus(s); setTrades(t); setIndicators(ind);
    } catch (e) { console.error('Refresh error:', e.message); }
  }, []);

  const refreshNews = useCallback(async () => {
    setNewsLoading(true);
    try {
      const n = await TradingAPI.news();
      setNews(n.forexFactory || []);
    } catch (e) { console.error('News error:', e.message); }
    finally { setNewsLoading(false); }
  }, []);

  useEffect(() => {
    TradingAPI.settings().then(setSettings).catch(() => {});
    refreshAll();
    refreshNews();
    const fast = setInterval(refreshAll, 5000);
    const slow = setInterval(refreshNews, 60000);
    return () => { clearInterval(fast); clearInterval(slow); };
  }, [refreshAll, refreshNews]);

  const handleStart = async () => {
    try {
      const r = await TradingAPI.start();
      notify(r.traded ? `Signal detecte ! ${r.signals?.length} trade(s) ouvert(s)` : 'Cycle lance - aucun signal pour le moment', r.traded ? 'success' : 'info');
      refreshAll();
    } catch (e) { notify(`Erreur: ${e.message}`, 'error'); }
  };

  const handleCloseAll = async () => {
    if (!window.confirm('Fermer TOUS les trades ouverts ?')) return;
    try {
      const r = await TradingAPI.closeAll();
      notify(`${r.closed} trade(s) ferme(s)`);
      refreshAll();
    } catch (e) { notify(`Erreur: ${e.message}`, 'error'); }
  };

  const handleSaveSettings = async (s) => {
    try {
      await TradingAPI.saveSettings(s);
      setSettings(s);
      notify('Parametres sauvegardes');
    } catch (e) { notify(`Erreur: ${e.message}`, 'error'); }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
            <Typography variant="h5" fontWeight={700}>Tableau de Bord</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="contained" color="success" startIcon={<PlayArrowIcon />} onClick={handleStart}>Lancer un Cycle</Button>
              <Button variant="outlined" color="error" startIcon={<StopIcon />} onClick={handleCloseAll}>Fermer Tous</Button>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12}><StatusBar status={status} /></Grid>
        <Grid item xs={12} md={4}><IndicatorsCard symbol="EURUSD" data={indicators} /></Grid>
        <Grid item xs={12} md={4}><NewsCard events={news} loading={newsLoading} /></Grid>
        <Grid item xs={12} md={4}><Paper sx={{ p: 2, height: '100%' }}><Charts symbol="EURUSD" /></Paper></Grid>
        <Grid item xs={12} md={6}><Settings settings={settings} onSave={handleSaveSettings} /></Grid>
        <Grid item xs={12} md={6}><TradeList trades={trades} /></Grid>
      </Grid>
      <Snackbar open={snack.open} autoHideDuration={4000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} variant="filled">{snack.msg}</Alert>
      </Snackbar>
    </Box>
  );
}
