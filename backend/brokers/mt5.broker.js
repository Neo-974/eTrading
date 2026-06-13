const { execFile } = require('child_process');
const BaseBroker = require('./base.broker');

/**
 * Broker MetaTrader 5 (compatible VTMarkets, qui distribue des serveurs MT5).
 *
 * Prérequis :
 *   - Terminal MT5 installé et connecté au compte VTMarkets
 *   - pip install MetaTrader5
 *   - Renseigner MT5_LOGIN / MT5_PASSWORD / MT5_SERVER dans .env
 */
class MT5Broker extends BaseBroker {
  constructor(config) {
    super();
    this.cfg = config.mt5;
  }

  _call(command, args = {}) {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify({
        login: this.cfg.login,
        password: this.cfg.password,
        server: this.cfg.server,
        command,
        args,
      });
      execFile(
        this.cfg.pythonBin,
        [this.cfg.bridgePath],
        { timeout: 30000 },
        (error, stdout, stderr) => {
          if (error) return reject(new Error(`MT5 bridge: ${stderr || error.message}`));
          try {
            const parsed = JSON.parse(stdout);
            if (parsed.error) return reject(new Error(parsed.error));
            resolve(parsed);
          } catch (e) {
            reject(new Error(`Réponse MT5 invalide: ${stdout}`));
          }
        }
      ).stdin.end(payload);
    });
  }

  async connect() {
    const res = await this._call('connect');
    this.connected = Boolean(res.connected);
    if (this.connected) console.log('✅ Connecté à MetaTrader 5 (VTMarkets)');
    return this.connected;
  }

  async getAccountInfo() { return this._call('account_info'); }
  async getSymbolPrice(symbol) { return this._call('price', { symbol }); }
  async getHistoricalData(symbol, timeframe, count = 100) {
    const res = await this._call('rates', { symbol, timeframe, count });
    return res.candles || [];
  }
  async openTrade({ symbol, volume, action, sl, tp, comment = '' }) {
    return this._call('open', { symbol, volume, action, sl, tp, comment });
  }
  async closeTrade(ticket) { return this._call('close', { ticket }); }
  async getOpenTrades() {
    const res = await this._call('open_trades');
    return res.trades || [];
  }
}

module.exports = MT5Broker;
