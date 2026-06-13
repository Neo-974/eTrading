const axios = require('axios');
const config = require('../config');

class NotificationService {
  async sendDiscord(message) {
    if (!config.discordWebhookUrl) return;
    try {
      await axios.post(config.discordWebhookUrl, { content: message, username: 'NeoTechno Trading Bot' });
    } catch (error) { console.error('Erreur notification Discord:', error.message); }
  }
}

module.exports = new NotificationService();
