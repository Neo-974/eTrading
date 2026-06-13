/**
 * Interface commune à tous les brokers (Demo, MT5/VTMarkets, ...).
 * Le reste de l'application ne parle qu'à cette interface : on peut donc
 * changer de broker via la config sans toucher à la logique de trading.
 */
class BaseBroker {
  constructor() {
    this.connected = false;
  }

  /** @returns {Promise<boolean>} */
  async connect() {
    throw new Error('connect() non implémenté');
  }

  async disconnect() {
    this.connected = false;
  }

  /** @returns {Promise<{balance:number,equity:number,currency:string}>} */
  async getAccountInfo() {
    throw new Error('getAccountInfo() non implémenté');
  }

  /** @returns {Promise<{symbol:string,bid:number,ask:number,point:number}>} */
  async getSymbolPrice(symbol) {
    throw new Error('getSymbolPrice() non implémenté');
  }

  /** @returns {Promise<Array<{time:number,open:number,high:number,low:number,close:number}>>} */
  async getHistoricalData(symbol, timeframe, count) {
    throw new Error('getHistoricalData() non implémenté');
  }

  /**
   * @returns {Promise<{ticket:number,symbol:string,action:string,volume:number,
   *   open_price:number,sl:number,tp:number}>}
   */
  async openTrade({ symbol, volume, action, sl, tp, comment }) {
    throw new Error('openTrade() non implémenté');
  }

  /** @returns {Promise<{ticket:number,profit:number,close_price:number}>} */
  async closeTrade(ticket) {
    throw new Error('closeTrade() non implémenté');
  }

  /** @returns {Promise<Array>} */
  async getOpenTrades() {
    throw new Error('getOpenTrades() non implémenté');
  }
}

module.exports = BaseBroker;
