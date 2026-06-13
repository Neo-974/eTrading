const config = require('../config');
const DemoBroker = require('./demo.broker');
const MT5Broker = require('./mt5.broker');

function createBroker() {
  switch (config.broker) {
    case 'mt5':
      return new MT5Broker(config);
    case 'demo':
    default:
      return new DemoBroker(config);
  }
}

module.exports = createBroker();
