class IndicatorsController {
  calculateRSI(prices, period = 14) {
    if (prices.length < period + 1) return 50;
    const gains = [];
    const losses = [];
    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);
    }
    let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
    let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
    for (let i = period; i < gains.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    }
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - 100 / (1 + rs);
  }

  emaSeries(prices, period) {
    if (prices.length === 0) return [];
    const k = 2 / (period + 1);
    const ema = [prices[0]];
    for (let i = 1; i < prices.length; i++) {
      ema.push(prices[i] * k + ema[i - 1] * (1 - k));
    }
    return ema;
  }

  calculateMACD(prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    if (prices.length < slowPeriod + signalPeriod) return { macd: 0, signal: 0, histogram: 0 };
    const fast = this.emaSeries(prices, fastPeriod);
    const slow = this.emaSeries(prices, slowPeriod);
    const macdLine = fast.map((v, i) => v - slow[i]);
    const signalLine = this.emaSeries(macdLine, signalPeriod);
    const macd = macdLine[macdLine.length - 1];
    const signal = signalLine[signalLine.length - 1];
    return { macd, signal, histogram: macd - signal };
  }

  calculateSMA(prices, period) {
    if (prices.length < period) return 0;
    return prices.slice(-period).reduce((a, b) => a + b, 0) / period;
  }

  calculateStdDev(prices, period) {
    if (prices.length < period) return 0;
    const slice = prices.slice(-period);
    const mean = slice.reduce((a, b) => a + b, 0) / period;
    const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
    return Math.sqrt(variance);
  }

  calculateBollingerBands(prices, period = 20, deviation = 2) {
    if (prices.length < period) return { upper: 0, middle: 0, lower: 0 };
    const middle = this.calculateSMA(prices, period);
    const std = this.calculateStdDev(prices, period);
    return { upper: middle + std * deviation, middle, lower: middle - std * deviation };
  }

  computeAll(closes) {
    return {
      rsi: this.calculateRSI(closes),
      macd: this.calculateMACD(closes),
      bollinger: this.calculateBollingerBands(closes),
    };
  }
}

module.exports = new IndicatorsController();
