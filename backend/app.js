const express = require('express');
const cors = require('cors');
const config = require('./config');
const broker = require('./brokers/broker.factory');
const tradingRoutes = require('./routes/trading.routes');
const scrapingRoutes = require('./routes/scraping.routes');

const app = express();

app.use(cors({ origin: config.corsOrigin }));
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', mode: config.tradingMode, broker: config.broker });
});

app.use('/api/trading', tradingRoutes);
app.use('/api/scraping', scrapingRoutes);

// Gestion d'erreur centralisée
app.use((err, req, res, next) => {
  console.error('Erreur non gérée:', err.message);
  res.status(500).json({ error: err.message });
});

async function start() {
  try {
    await broker.connect();
  } catch (error) {
    console.error('⚠️ Connexion broker échouée au démarrage:', error.message);
  }
  app.listen(config.port, () => {
    console.log(`\n🚀 Backend démarré sur http://localhost:${config.port}`);
    console.log(`   Mode: ${config.tradingMode} | Broker: ${config.broker}\n`);
  });
}

start();

module.exports = app;
