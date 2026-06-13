const { createClient } = require('@supabase/supabase-js');
const config = require('../config');

class SupabaseService {
  constructor() {
    this.enabled = config.supabase.enabled;
    if (this.enabled) {
      this.client = createClient(config.supabase.url, config.supabase.key);
      console.log('🗄️  Supabase connecté');
    } else {
      console.log('🗄️  Supabase non configuré → stockage en mémoire (dev)');
      this._memTrades = [];
      this._memSettings = null;
    }
  }

  async saveTrade(tradeData) {
    if (!this.enabled) {
      const record = { id: `mem-${this._memTrades.length + 1}`, ...tradeData };
      this._memTrades.unshift(record);
      return [record];
    }
    const { data, error } = await this.client.from('trades').insert([tradeData]).select();
    if (error) throw error;
    return data;
  }

  async updateTrade(id, patch) {
    if (!this.enabled) {
      const t = this._memTrades.find((x) => x.id === id);
      if (t) Object.assign(t, patch);
      return t;
    }
    const { data, error } = await this.client.from('trades').update(patch).eq('id', id).select();
    if (error) throw error;
    return data;
  }

  async getTrades() {
    if (!this.enabled) return this._memTrades;
    const { data, error } = await this.client.from('trades').select('*').order('created_at', { ascending: false });
    if (error) throw error;
    return data;
  }

  async saveSettings(settings) {
    if (!this.enabled) {
      this._memSettings = { ...(this._memSettings || {}), ...settings };
      return [this._memSettings];
    }
    const { data, error } = await this.client.from('settings').upsert([settings]).select();
    if (error) throw error;
    return data;
  }

  async getSettings() {
    if (!this.enabled) return this._memSettings;
    const { data, error } = await this.client.from('settings').select('*').limit(1).maybeSingle();
    if (error) throw error;
    return data;
  }
}

module.exports = new SupabaseService();
