const path = require('path');
// Charge le .env situé à la racine du projet (un niveau au-dessus de backend/)
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const config = {
  tradingMode: process.env.TRADING_MODE || 'demo',
  broker: process.env.BROKER || 'demo',

  demo: {
    accountBalance: parseFloat(process.env.DEMO_ACCOUNT_BALANCE || '10000'),
  },

  mt5: {
    login: process.env.MT5_LOGIN || '',
    password: process.env.MT5_PASSWORD || '',
    server: process.env.MT5_SERVER || '',
    pythonBin: process.env.PYTHON_BIN || 'python3',
    bridgePath: process.env.MT5_BRIDGE_PATH || path.resolve(__dirname, '../python/mt5_bridge.py'),
  },

  supabase: {
    url: process.env.SUPABASE_URL || '',
    key: process.env.SUPABASE_KEY || '',
    enabled: Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_KEY),
  },

  news: {
    newsApiKey: process.env.NEWSAPI_KEY || '',
    coingeckoApi: process.env.COINGECKO_API || 'https://api.coingecko.com/api/v3',
  },

  discordWebhookUrl: process.env.DISCORD_WEBHOOK_URL || '',

  port: parseInt(process.env.PORT || '3001', 10),
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
};

module.exports = config;
