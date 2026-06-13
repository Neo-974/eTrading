const axios = require('axios');
const cheerio = require('cheerio');
const config = require('../config');

class NewsService {
  async getForexNews() {
    const result = { newsapi: [], forexFactory: [] };
    if (config.news.newsApiKey) {
      try {
        const res = await axios.get('https://newsapi.org/v2/everything', {
          params: { q: 'forex', apiKey: config.news.newsApiKey, language: 'en', sortBy: 'publishedAt' },
          timeout: 10000,
        });
        result.newsapi = res.data.articles || [];
      } catch (error) { console.error('Erreur NewsAPI:', error.message); }
    }
    try {
      const res = await axios.get('https://www.forexfactory.com/calendar', {
        headers: { 'User-Agent': 'Mozilla/5.0' },
        timeout: 10000,
      });
      const $ = cheerio.load(res.data);
      $('.calendar__row').each((i, el) => {
        const time = $(el).find('.calendar__time').text().trim();
        const currency = $(el).find('.calendar__currency').text().trim();
        const impact = $(el).find('.calendar__impact span').attr('title') || 'Low';
        const event = $(el).find('.calendar__event').text().trim();
        const actual = $(el).find('.calendar__actual').text().trim();
        const forecast = $(el).find('.calendar__forecast').text().trim();
        if (event && impact !== 'Non-Economic') {
          result.forexFactory.push({ time, currency, impact, event, actual, forecast });
        }
      });
    } catch (error) { console.error('Erreur Forex Factory:', error.message); }
    return result;
  }

  async getCryptoMarkets() {
    try {
      const res = await axios.get(`${config.news.coingeckoApi}/coins/markets`, {
        params: { vs_currency: 'usd', order: 'market_cap_desc', per_page: 10, page: 1, sparkline: false },
        timeout: 10000,
      });
      return res.data;
    } catch (error) { console.error('Erreur CoinGecko:', error.message); return []; }
  }
}

module.exports = new NewsService();
