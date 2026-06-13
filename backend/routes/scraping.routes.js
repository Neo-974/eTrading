const express = require('express');
const router = express.Router();
const axios = require('axios');
const cheerio = require('cheerio');

const SITES = {
  forexfactory: {
    name: 'Forex Factory',
    url: 'https://www.forexfactory.com/calendar',
    selector: '.calendar__row',
    fields: [
      { name: 'time', selector: '.calendar__time' },
      { name: 'currency', selector: '.calendar__currency' },
      { name: 'event', selector: '.calendar__event' },
    ],
  },
};

router.get('/sites', (req, res) => {
  res.json(Object.keys(SITES).map((id) => ({ id, name: SITES[id].name })));
});

router.get('/scrape/:siteId', async (req, res) => {
  const site = SITES[req.params.siteId];
  if (!site) return res.status(404).json({ error: 'Site inconnu' });
  try {
    const response = await axios.get(site.url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 10000 });
    const $ = cheerio.load(response.data);
    const data = [];
    $(site.selector).each((i, el) => {
      const item = {};
      site.fields.forEach((f) => { item[f.name] = $(el).find(f.selector).text().trim(); });
      if (Object.values(item).some(Boolean)) data.push(item);
    });
    res.json(data);
  } catch (error) { res.status(500).json({ error: error.message }); }
});

module.exports = router;
