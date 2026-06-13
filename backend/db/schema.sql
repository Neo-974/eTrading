-- Schéma Supabase / PostgreSQL pour NeoTechno Trading Bot
-- À exécuter dans l'éditeur SQL de Supabase.

CREATE TABLE IF NOT EXISTS trades (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ticket      BIGINT,
  symbol      TEXT NOT NULL,
  action      TEXT NOT NULL,
  open_price  FLOAT NOT NULL,
  close_price FLOAT,
  sl          FLOAT NOT NULL,
  tp          FLOAT NOT NULL,
  lot_size    FLOAT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'OPEN',
  result      TEXT,
  profit      FLOAT,
  mode        TEXT DEFAULT 'demo',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades (created_at DESC);

CREATE TABLE IF NOT EXISTS settings (
  id                          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  rsi_period                  INTEGER NOT NULL DEFAULT 14,
  rsi_buy_threshold           INTEGER NOT NULL DEFAULT 30,
  rsi_sell_threshold          INTEGER NOT NULL DEFAULT 70,
  lot_size                    FLOAT NOT NULL DEFAULT 0.1,
  stop_loss_pips              INTEGER NOT NULL DEFAULT 30,
  take_profit_pips            INTEGER NOT NULL DEFAULT 60,
  symbols                     TEXT[] NOT NULL DEFAULT '{"EURUSD","GBPUSD"}',
  max_daily_loss_percent      FLOAT NOT NULL DEFAULT 5,
  target_daily_profit_percent FLOAT NOT NULL DEFAULT 1,
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO settings DEFAULT VALUES;
