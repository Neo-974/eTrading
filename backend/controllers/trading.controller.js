const broker = require('../brokers/broker.factory');
const supabaseService = require('../services/supabase.service');
const indicators = require('./indicators.controller');
const newsService = require('../services/news.service');
const notifier = require('../services/notification.service');
const config = require('../config');

const DEFAULT_SETTINGS = {
  rsiPeriod: 14,
  rsiBuyThreshold: 30,
  rsiSellThreshold: 70,
  macdFast: 12,
  macdSlow: 26,
  bollingerPeriod: 20,
  lotSize: 0.1,
  stopLossPips: 30,
  takeProfitPips: 60,
  maxDailyLossPercent: 5,
  targetDailyProfitPercent: 1,
  symbols: ['EURUSD', 'GBPUSD'],
};

class TradingController {
  constructor() {
    this.settings = { ...DEFAULT_SETTINGS };
    this.running = false;
    this.loadSettings();
  }

  async loadSettings() {
    try {
      const saved = await supabaseService.getSettings();
      if (saved) this.settings = { ...this.settings, ...saved };
    } catch (error) {
      console.error('Erreur chargement settings:', error.message);
    }
  }

  updateSettings(patch) {
    this.settings = { ...this.settings, ...patch };
    return this.settings;
  }

  async runCycle() {
    try {
      const { forexFactory } = await newsService.getForexNews();
      const now = new Date();
      const highImpactSoon = (forexFactory || []).some((ev) => {
        if (ev.impact !== 'High' || !ev.time) return false;
        const t = new Date(`${now.toDateString()} ${ev.time}`);
        const diffMin = (t - now) / 60000;
        return diffMin > 0 && diffMin < 30;
      });
      if (highImpactSoon) {
        console.log('⚠️ Événement à fort impact < 30 min → pas de nouveau trade');
        return { traded: false, reason: 'high_impact_event' };
      }
      const signals = [];
      for (const symbol of this.settings.symbols) {
        const sig = await this.checkSymbol(symbol);
        if (sig) signals.push(sig);
      }
      return { traded: signals.length > 0, signals };
    } catch (error) {
      console.error('Erreur runCycle:', error.message);
      return { traded: false, error: error.message };
    }
  }

  async checkSymbol(symbol) {
    try {
      const candles = await broker.getHistoricalData(symbol, 'M15', 100);
      if (!candles || candles.length < 50) return null;
      const closes = candles.map((c) => c.close);
      const tick = await broker.getSymbolPrice(symbol);
      const currentPrice = tick.bid;
      const point = tick.point;
      const rsi = indicators.calculateRSI(closes, this.settings.rsiPeriod);
      const { macd, signal } = indicators.calculateMACD(closes, this.settings.macdFast, this.settings.macdSlow);
      const { upper, lower } = indicators.calculateBollingerBands(closes, this.settings.bollingerPeriod);
      let action = null;
      if (rsi < this.settings.rsiBuyThreshold && macd > signal && currentPrice < lower) action = 'BUY';
      else if (rsi > this.settings.rsiSellThreshold && macd < signal && currentPrice > upper) action = 'SELL';
      if (!action) return null;
      console.log(`📈 Signal ${action} ${symbol} (RSI ${rsi.toFixed(2)}, MACD ${macd.toFixed(5)})`);
      const opened = await this.openTrade(symbol, action, currentPrice, point);
      return opened ? { symbol, action, rsi, price: currentPrice } : null;
    } catch (error) {
      console.error(`Erreur checkSymbol ${symbol}:`, error.message);
      return null;
    }
  }

  async _riskAllows() {
    const trades = await supabaseService.getTrades();
    const today = new Date().toISOString().split('T')[0];
    const todays = trades.filter((t) => (t.created_at || '').startsWith(today));
    const loss = todays.filter((t) => t.result === 'LOSS').reduce((s, t) => s + Math.abs(t.profit || 0), 0);
    const profit = todays.filter((t) => t.result === 'WIN').reduce((s, t) => s + (t.profit || 0), 0);
    const account = await broker.getAccountInfo();
    const balance = account.balance || config.demo.accountBalance;
    const maxLoss = balance * (this.settings.maxDailyLossPercent / 100);
    const targetProfit = balance * (this.settings.targetDailyProfitPercent / 100);
    if (loss >= maxLoss) return { ok: false, reason: 'daily_loss_limit' };
    if (profit >= targetProfit) return { ok: false, reason: 'daily_target_reached' };
    return { ok: true };
  }

  async openTrade(symbol, action, currentPrice, point) {
    const risk = await this._riskAllows();
    if (!risk.ok) { console.log(`⛔ Trade bloqué (${risk.reason})`); return null; }
    const slPips = this.settings.stopLossPips;
    const tpPips = this.settings.takeProfitPips;
    const sl = action === 'BUY' ? currentPrice - slPips * point : currentPrice + slPips * point;
    const tp = action === 'BUY' ? currentPrice + tpPips * point : currentPrice - tpPips * point;
    const trade = await broker.openTrade({ symbol, volume: this.settings.lotSize, action, sl, tp, comment: 'Auto RSI/MACD/BB' });
    if (!trade) return null;
    const saved = await supabaseService.saveTrade({
      ticket: trade.ticket, symbol, action, open_price: trade.open_price,
      sl, tp, lot_size: this.settings.lotSize, status: 'OPEN',
      mode: config.tradingMode, created_at: new Date().toISOString(),
    });
    await notifier.sendDiscord(`🚀 **Nouveau Trade** ${symbol} ${action} @ ${trade.open_price.toFixed(5)} | SL ${sl.toFixed(5)} | TP ${tp.toFixed(5)}`);
    console.log(`✅ Trade ouvert ${symbol} ${action} @ ${trade.open_price}`);
    return saved;
  }

  async closeAllTrades() {
    const open = await broker.getOpenTrades();
    const dbTrades = await supabaseService.getTrades();
    for (const t of open) {
      const result = await broker.closeTrade(t.ticket);
      const record = dbTrades.find((d) => d.ticket === t.ticket && d.status === 'OPEN');
      if (record) {
        await supabaseService.updateTrade(record.id, {
          status: 'CLOSED', close_price: result.close_price,
          result: result.profit > 0 ? 'WIN' : 'LOSS', profit: result.profit,
          closed_at: new Date().toISOString(),
        });
      }
    }
    await notifier.sendDiscord(`🔒 ${open.length} trade(s) fermé(s)`);
    return { closed: open.length };
  }
}

module.exports = new TradingController();
