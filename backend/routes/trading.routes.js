const express = require('express');
const router = express.Router();
const broker = require('../brokers/broker.factory');
const tradingController = require('../controllers/trading.controller');
const indicators = require('../controllers/indicators.controller');
const supabaseService = require('../services/supabase.service');
const newsService = require('../services/news.service');
const config = require('../config');

router.get('/status', async (req, res) => {
  try {
    const account = await broker.getAccountInfo();
    res.json({ mode: config.tradingMode, broker: config.broker, connected: broker.connected, account });
  } catch (error) { res.status(500).json({ error: error.message }); }
});

router.post('/start', async (req, res) => {
  try {
    const result = await tradingController.runCycle();
    res.json({ success: true, ...result });
  } catch (error) { res.status(500).json({ success: false, error: error.message }); }
});

router.get('/trades', async (req, res) => {
  try { res.json(await supabaseService.getTrades()); }
  catch (error) { res.status(500).json({ error: error.message }); }
});

router.post('/close-all', async (req, res) => {
  try {
    const result = await tradingController.closeAllTrades();
    res.json({ success: true, ...result });
  } catch (error) { res.status(500).json({ error: error.message }); }
});

router.get('/news', async (req, res) => {
  try { res.json(await newsService.getForexNews()); }
  catch (error) { res.status(500).json({ error: error.message }); }
});

router.get('/indicators/:symbol', async (req, res) => {
  try {
    const candles = await broker.getHistoricalData(req.params.symbol, 'M15', 100);
    const closes = candles.map((c) => c.close);
    res.json(indicators.computeAll(closes));
  } catch (error) { res.status(500).json({ error: error.message }); }
});

router.get('/candles/:symbol', async (req, res) => {
  try {
    const count = parseInt(req.query.count || '50', 10);
    const candles = await broker.getHistoricalData(req.params.symbol, 'M15', count);
    res.json(candles);
  } catch (error) { res.status(500).json({ error: error.message }); }
});

router.get('/settings', async (req, res) => {
  try {
    const saved = await supabaseService.getSettings();
    res.json(saved || tradingController.settings);
  } catch (error) { res.status(500).json({ error: error.message }); }
});

router.post('/settings', async (req, res) => {
  try {
    const updated = tradingController.updateSettings(req.body);
    await supabaseService.saveSettings(req.body);
    res.json({ success: true, settings: updated });
  } catch (error) { res.status(500).json({ error: error.message }); }
});

module.exports = router;
