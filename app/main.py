import logging
import os
import secrets
import json as _json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import risk_manager
from adapters.bitpanda_adapter import BitpandaAdapter
from adapters.bybit_adapter import BybitAdapter
from adapters.coinbase_adapter import CoinbaseAdapter
from adapters.kraken_adapter import KrakenAdapter
from adapters.mt5_adapter import MT5Adapter
from adapters.oanda_adapter import OandaAdapter
from adapters.okx_adapter import OKXAdapter
from config import settings
from crypto_utils import decrypt, encrypt
from db import get_conn, init_db

# --- Logging ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/orders.log"), logging.StreamHandler()],
)
logger = logging.getLogger("tv-webhook")

init_db()

app = FastAPI(title="TradingView → Broker Automation")
app.mount("/assets", StaticFiles(directory="static"), name="assets")

security = HTTPBasic()

SUPPORTED_EXCHANGES = ("bybit", "kraken", "okx", "coinbase", "bitpanda", "oanda", "mt5")


def require_dashboard_auth(credentials: HTTPBasicCredentials = Depends(security)):
    valid_user = secrets.compare_digest(credentials.username, "admin")
    valid_pass = secrets.compare_digest(credentials.password, settings.DASHBOARD_PASSWORD)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=401,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def get_api_keys(exchange: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM api_keys WHERE exchange=?", (exchange,)).fetchone()
    if not row:
        return "", "", True
    return decrypt(row["api_key_enc"]), decrypt(row["api_secret_enc"]), bool(row["testnet"])


def get_okx_passphrase() -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM api_keys WHERE exchange='okx_passphrase'").fetchone()
    if not row:
        return ""
    return decrypt(row["api_key_enc"])


def build_adapter(exchange: str):
    exchange = exchange.lower()
    if exchange == "bybit":
        key, sec, testnet = get_api_keys("bybit")
        return BybitAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "kraken":
        key, sec, testnet = get_api_keys("kraken")
        return KrakenAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "okx":
        key, sec, testnet = get_api_keys("okx")
        return OKXAdapter(api_key=key, api_secret=sec, testnet=testnet, passphrase=get_okx_passphrase())
    if exchange == "coinbase":
        key, sec, testnet = get_api_keys("coinbase")
        return CoinbaseAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "bitpanda":
        key, sec, testnet = get_api_keys("bitpanda")
        return BitpandaAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "oanda":
        key, sec, testnet = get_api_keys("oanda")
        return OandaAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "mt5":
        account_id, token, _ = get_api_keys("mt5")
        return MT5Adapter(account_id=account_id, token=token)
    return None


class TradingViewAlert(BaseModel):
    secret: str
    exchange: str
    symbol: str
    side: str
    order_type: str = Field(default="market")
    quantity: float
    price: Optional[float] = None


class ApiKeyInput(BaseModel):
    exchange: str
    api_key: str
    api_secret: str
    testnet: bool = True
    okx_passphrase: Optional[str] = None  # uniquement utilisé pour exchange="okx"


class StrategyToggle(BaseModel):
    exchange: str
    symbol: str
    enabled: bool


class BotProfileInput(BaseModel):
    name: str
    exchange: str
    symbol: str = "*"  # "*" = profil global pour tout l'exchange
    is_active: bool = False
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_daily_loss: Optional[int] = None
    trading_start_hour: Optional[int] = None
    trading_end_hour: Optional[int] = None
    symbol_whitelist: Optional[str] = None
    max_concurrent_trades: Optional[int] = None


class ManualOrderInput(BaseModel):
    exchange: str
    symbol: str
    side: str
    order_type: str = Field(default="market")
    quantity: float
    price: Optional[float] = None
    bypass_profile_checks: bool = False


def _log_order(exchange, symbol, side, quantity, order_type, price, status, detail):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO orders
               (created_at, exchange, symbol, side, quantity, order_type, price, status, detail)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (now, exchange, symbol, side, quantity, order_type, price, status, detail),
        )
        conn.execute(
            """INSERT INTO strategies (exchange, symbol, enabled, created_at)
               VALUES (?, ?, 1, ?)
               ON CONFLICT(exchange, symbol) DO NOTHING""",
            (exchange, symbol, now),
        )


def _execute_order(exchange: str, symbol: str, side: str, quantity: float, order_type: str,
                    price: Optional[float], skip_risk_checks: bool = False, source: str = "webhook") -> dict:
    """Logique partagée entre le webhook TradingView et le terminal manuel du dashboard."""
    exchange = exchange.lower()
    if exchange not in SUPPORTED_EXCHANGES:
        detail = f"Exchange '{exchange}' non supporté (attendu: {', '.join(SUPPORTED_EXCHANGES)})"
        _log_order(exchange, symbol, side, quantity, order_type, price, "error", detail)
        return {"status": "error", "detail": detail}

    with get_conn() as conn:
        row = conn.execute(
            "SELECT enabled FROM strategies WHERE exchange=? AND symbol=?",
            (exchange, symbol.upper()),
        ).fetchone()
    if row is not None and not row["enabled"] and not skip_risk_checks:
        detail = "Stratégie désactivée depuis le dashboard"
        _log_order(exchange, symbol, side, quantity, order_type, price, "ignored", detail)
        return {"status": "ignored", "detail": detail}

    sl = tp = None
    profile = None
    if not skip_risk_checks:
        allowed, reason, profile, sl, tp = risk_manager.evaluate(exchange, symbol, side, price)
        if not allowed:
            _log_order(exchange, symbol, side, quantity, order_type, price, "ignored", reason)
            logger.info("Ordre bloqué par le profil '%s': %s", profile["name"] if profile else "?", reason)
            return {"status": "ignored", "detail": reason}

    adapter = build_adapter(exchange)
    if adapter is None or not adapter.is_configured():
        detail = f"Clés API manquantes pour {exchange}"
        _log_order(exchange, symbol, side, quantity, order_type, price, "error", detail)
        return {"status": "error", "detail": detail}

    result = adapter.place_order(symbol=symbol, side=side, quantity=quantity, order_type=order_type, price=price)
    detail = result.get("detail", "")
    if source == "manual":
        detail = f"[Terminal manuel] {detail}"
    if sl or tp:
        detail += f" | SL={sl} TP={tp} (profil '{profile['name']}')"

    _log_order(exchange, symbol, side, quantity, order_type, price, result["status"], detail)
    logger.info("Ordre %s sur %s %s (%s): %s", result["status"], exchange, symbol, source, detail)
    return {**result, "detail": detail, "stop_loss": sl, "take_profit": tp}


# ---------------------------------------------------------------------
# Webhook TradingView
# ---------------------------------------------------------------------


@app.post("/webhook")
async def receive_alert(alert: TradingViewAlert):
    if not secrets.compare_digest(alert.secret, settings.WEBHOOK_SECRET):
        logger.warning("Secret invalide reçu sur /webhook")
        raise HTTPException(status_code=401, detail="Secret invalide")

    result = _execute_order(
        alert.exchange, alert.symbol, alert.side, alert.quantity,
        alert.order_type, alert.price, skip_risk_checks=False, source="webhook",
    )
    if result["status"] == "error" and "non supporté" in result.get("detail", ""):
        raise HTTPException(status_code=400, detail=result["detail"])
    if result["status"] == "error" and "Clés API manquantes" in result.get("detail", ""):
        raise HTTPException(status_code=400, detail=result["detail"])
    return result


@app.post("/api/manual-order")
def manual_order(payload: ManualOrderInput, _auth: bool = Depends(require_dashboard_auth)):
    """Terminal manuel : passe un ordre directement depuis le dashboard, sans TradingView."""
    result = _execute_order(
        payload.exchange, payload.symbol, payload.side, payload.quantity,
        payload.order_type, payload.price, skip_risk_checks=payload.bypass_profile_checks, source="manual",
    )
    return result


@app.get("/api/portfolio")
def portfolio_overview(_auth: bool = Depends(require_dashboard_auth)):
    """Vue agrégée : tente de récupérer le solde sur chaque exchange configuré.
    Le format de solde diffère selon la plateforme (pas de normalisation), on
    renvoie donc la réponse brute par exchange pour affichage côté dashboard."""
    results = {}
    for ex in SUPPORTED_EXCHANGES:
        adapter = build_adapter(ex)
        if adapter is None or not adapter.is_configured():
            results[ex] = {"configured": False}
            continue
        balance = adapter.get_account_balance()
        results[ex] = {"configured": True, **balance}
    return results


@app.get("/api/candles")
def get_candles(exchange: str, symbol: str, interval: str = "1h", limit: int = 200,
                 _auth: bool = Depends(require_dashboard_auth)):
    exchange = exchange.lower()
    if exchange not in SUPPORTED_EXCHANGES:
        raise HTTPException(status_code=400, detail="Exchange non supporté")
    adapter = build_adapter(exchange)
    if adapter is None:
        raise HTTPException(status_code=400, detail="Exchange non supporté")
    try:
        candles = adapter.get_candles(symbol=symbol, interval=interval, limit=limit)
        return {"status": "ok", "candles": candles}
    except NotImplementedError as e:
        return {"status": "unavailable", "detail": str(e), "candles": []}
    except Exception as e:
        return {"status": "error", "detail": f"Erreur récupération des données de marché: {e}", "candles": []}


# ---------------------------------------------------------------------
# Dashboard (protégé par auth basique)
# ---------------------------------------------------------------------


@app.get("/")
def dashboard(_auth: bool = Depends(require_dashboard_auth)):
    return FileResponse("static/index.html")


@app.get("/api/health")
def health_check(_auth: bool = Depends(require_dashboard_auth)):
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/orders")
def list_orders(limit: int = 200, _auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/strategies")
def list_strategies(_auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM strategies ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/strategies/toggle")
def toggle_strategy(payload: StrategyToggle, _auth: bool = Depends(require_dashboard_auth)):
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO strategies (exchange, symbol, enabled, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(exchange, symbol) DO UPDATE SET enabled=excluded.enabled""",
            (payload.exchange.lower(), payload.symbol.upper(), int(payload.enabled), now),
        )
    return {"status": "ok"}


@app.get("/api/keys")
def list_keys(_auth: bool = Depends(require_dashboard_auth)):
    # Ne renvoie JAMAIS les clés en clair — juste leur présence et statut.
    with get_conn() as conn:
        rows = conn.execute("SELECT exchange, testnet, updated_at FROM api_keys").fetchall()
    configured = {r["exchange"]: dict(r) for r in rows}
    return [
        {
            "exchange": ex,
            "configured": ex in configured,
            "testnet": configured.get(ex, {}).get("testnet"),
            "updated_at": configured.get(ex, {}).get("updated_at"),
        }
        for ex in SUPPORTED_EXCHANGES
    ]


@app.post("/api/keys")
def save_keys(payload: ApiKeyInput, _auth: bool = Depends(require_dashboard_auth)):
    if payload.exchange.lower() not in SUPPORTED_EXCHANGES:
        raise HTTPException(status_code=400, detail="Exchange non supporté")
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO api_keys (exchange, api_key_enc, api_secret_enc, testnet, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(exchange) DO UPDATE SET
                 api_key_enc=excluded.api_key_enc,
                 api_secret_enc=excluded.api_secret_enc,
                 testnet=excluded.testnet,
                 updated_at=excluded.updated_at""",
            (payload.exchange.lower(), encrypt(payload.api_key), encrypt(payload.api_secret), int(payload.testnet), now),
        )
        if payload.exchange.lower() == "okx" and payload.okx_passphrase:
            conn.execute(
                """INSERT INTO api_keys (exchange, api_key_enc, api_secret_enc, testnet, updated_at)
                   VALUES ('okx_passphrase', ?, '', 1, ?)
                   ON CONFLICT(exchange) DO UPDATE SET api_key_enc=excluded.api_key_enc, updated_at=excluded.updated_at""",
                (encrypt(payload.okx_passphrase), now),
            )
    return {"status": "ok"}


# ---------------------------------------------------------------------
# Profils / scénarios de trading (réglages du bot)
# ---------------------------------------------------------------------


@app.get("/api/profiles")
def list_profiles(_auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM bot_profiles ORDER BY id DESC").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["settings"] = _json.loads(d.pop("settings_json"))
        result.append(d)
    return result


@app.post("/api/profiles")
def create_profile(payload: BotProfileInput, _auth: bool = Depends(require_dashboard_auth)):
    now = datetime.now(timezone.utc).isoformat()
    symbol = payload.symbol.upper() if payload.symbol != "*" else "*"
    profile_settings = {
        "stop_loss_pct": payload.stop_loss_pct,
        "take_profit_pct": payload.take_profit_pct,
        "max_daily_loss": payload.max_daily_loss,
        "trading_start_hour": payload.trading_start_hour,
        "trading_end_hour": payload.trading_end_hour,
        "symbol_whitelist": payload.symbol_whitelist,
        "max_concurrent_trades": payload.max_concurrent_trades,
    }
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO bot_profiles (name, exchange, symbol, is_active, settings_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (payload.name, payload.exchange.lower(), symbol, int(payload.is_active), _json.dumps(profile_settings), now, now),
        )
        profile_id = cur.lastrowid
        if payload.is_active:
            # Un seul profil actif à la fois pour ce couple exchange/symbole.
            conn.execute(
                "UPDATE bot_profiles SET is_active=0 WHERE exchange=? AND symbol=? AND id!=?",
                (payload.exchange.lower(), symbol, profile_id),
            )
    return {"status": "ok", "id": profile_id}


@app.post("/api/profiles/{profile_id}/activate")
def activate_profile(profile_id: int, _auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bot_profiles WHERE id=?", (profile_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profil introuvable")
        conn.execute(
            "UPDATE bot_profiles SET is_active=0 WHERE exchange=? AND symbol=?",
            (row["exchange"], row["symbol"]),
        )
        conn.execute("UPDATE bot_profiles SET is_active=1 WHERE id=?", (profile_id,))
    return {"status": "ok"}


@app.post("/api/profiles/{profile_id}/deactivate")
def deactivate_profile(profile_id: int, _auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        conn.execute("UPDATE bot_profiles SET is_active=0 WHERE id=?", (profile_id,))
    return {"status": "ok"}


@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int, _auth: bool = Depends(require_dashboard_auth)):
    with get_conn() as conn:
        conn.execute("DELETE FROM bot_profiles WHERE id=?", (profile_id,))
    return {"status": "ok"}
