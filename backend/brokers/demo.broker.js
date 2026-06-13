const BaseBroker = require('./base.broker');

/**
 * Broker simulé : aucune connexion réelle, aucun argent réel.
 * Génère des prix plausibles et simule l'exécution des ordres en mémoire.
 * Idéal pour développer le tableau de bord et tester la logique de trading.
 */
class DemoBroker extends BaseBroker {
  constructor(config) {
    super();
    this.balance = config.demo.accountBalance;
    this.equity = this.balance;
    this.trades = new Map(); // ticket -> trade
    this.nextTicket = 1000;

    // Prix de base par symbole + nombre de décimales (point = plus petite variation)
    this.basePrices = {
      EURUSD: { price: 1.085, point: 0.00001, spread: 0.00010 },
      GBPUSD: { price: 1.265, point: 0.00001, spread: 0.00012 },
      BTCUSD: { price: 64000, point: 0.01, spread: 5 },
      ETHUSD: { price: 3400, point: 0.01, spread: 1 },
    };
  }

  async connect() {
    this.connected = true;
    console.log('🧪 Broker DEMO connecté (trades simulés, aucun risque réel)');
    return true;
  }

  async getAccountInfo() {
    return { balance: this.balance, equity: this.equity, currency: 'USD' };
  }

  _meta(symbol) {
    return this.basePrices[symbol] || { price: 1.0, point: 0.00001, spread: 0.0001 };
  }

  _simulatedPrice(symbol) {
    const meta = this._meta(symbol);
    const drift = (Math.random() - 0.5) * meta.spread * 8;
    const mid = meta.price + drift;
    return {
      symbol,
      bid: mid,
      ask: mid + meta.spread,
      point: meta.point,
    };
  }

  async getSymbolPrice(symbol) {
    return this._simulatedPrice(symbol);
  }

  async getHistoricalData(symbol, timeframe, count = 100) {
    const meta = this._meta(symbol);
    const candles = [];
    let last = meta.price * (0.99 + Math.random() * 0.02);
    const now = Date.now();
    for (let i = count; i > 0; i--) {
      const open = last;
      const change = (Math.random() - 0.5) * meta.spread * 10;
      const close = open + change;
      const high = Math.max(open, close) + Math.random() * meta.spread * 3;
      const low = Math.min(open, close) - Math.random() * meta.spread * 3;
      candles.push({ time: now - i * 60000, open, high, low, close });
      last = close;
    }
    return candles;
  }

  async openTrade({ symbol, volume, action, sl, tp, comment = '' }) {
    const tick = await this.getSymbolPrice(symbol);
    const openPrice = action === 'BUY' ? tick.ask : tick.bid;
    const ticket = this.nextTicket++;
    const trade = {
      ticket,
      symbol,
      action,
      volume,
      open_price: openPrice,
      sl,
      tp,
      comment,
      opened_at: Date.now(),
    };
    this.trades.set(ticket, trade);
    return trade;
  }

  async closeTrade(ticket) {
    const trade = this.trades.get(ticket);
    if (!trade) throw new Error(`Trade ${ticket} introuvable`);
    const tick = await this.getSymbolPrice(trade.symbol);
    const closePrice = trade.action === 'BUY' ? tick.bid : tick.ask;
    const meta = this._meta(trade.symbol);

    const direction = trade.action === 'BUY' ? 1 : -1;
    const pointsMoved = (closePrice - trade.open_price) * direction / meta.point;
    const pointValue = meta.point * 100000 * trade.volume;
    const profit = parseFloat((pointsMoved * meta.point * pointValue).toFixed(2));

    this.balance += profit;
    this.equity = this.balance;
    this.trades.delete(ticket);
    return { ticket, profit, close_price: closePrice };
  }

  async getOpenTrades() {
    return Array.from(this.trades.values());
  }
}

module.exports = DemoBroker;
