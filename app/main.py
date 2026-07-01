import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from adapters.bybit_adapter import BybitAdapter
from adapters.kraken_adapter import KrakenAdapter
from adapters.mt5_adapter import MT5Adapter
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

SUPPORTED_EXCHANGES = ("bybit", "kraken", "mt5")


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


def build_adapter(exchange: str):
    exchange = exchange.lower()
    if exchange == "bybit":
        key, sec, testnet = get_api_keys("bybit")
        return BybitAdapter(api_key=key, api_secret=sec, testnet=testnet)
    if exchange == "kraken":
        key, sec, testnet = get_api_keys("kraken")
        return KrakenAdapter(api_key=key, api_secret=sec, testnet=testnet)
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


class StrategyToggle(BaseModel):
    exchange: str
    symbol: str
    enabled: bool


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


# ---------------------------------------------------------------------
# Webhook TradingView
# ---------------------------------------------------------------------


@app.post("/webhook")
async def receive_alert(alert: TradingViewAlert):
    if not secrets.compare_digest(alert.secret, settings.WEBHOOK_SECRET):
        logger.warning("Secret invalide reçu sur /webhook")
        raise HTTPException(status_code=401, detail="Secret invalide")

    exchange = alert.exchange.lower()
    if exchange not in SUPPORTED_EXCHANGES:
        detail = f"Exchange '{alert.exchange}' non supporté (attendu: {', '.join(SUPPORTED_EXCHANGES)})"
        _log_order(exchange, alert.symbol, alert.side, alert.quantity, alert.order_type, alert.price, "error", detail)
        raise HTTPException(status_code=400, detail=detail)

    # Stratégie désactivée manuellement depuis le dashboard ?
    with get_conn() as conn:
        row = conn.execute(
            "SELECT enabled FROM strategies WHERE exchange=? AND symbol=?",
            (exchange, alert.symbol.upper()),
        ).fetchone()
    if row is not None and not row["enabled"]:
        detail = "Stratégie désactivée depuis le dashboard"
        _log_order(exchange, alert.symbol, alert.side, alert.quantity, alert.order_type, alert.price, "ignored", detail)
        return {"status": "ignored", "detail": detail}

    adapter = build_adapter(exchange)
    if adapter is None or not adapter.is_configured():
        detail = f"Clés API manquantes pour {exchange}"
        _log_order(exchange, alert.symbol, alert.side, alert.quantity, alert.order_type, alert.price, "error", detail)
        raise HTTPException(status_code=400, detail=detail)

    result = adapter.place_order(
        symbol=alert.symbol, side=alert.side, quantity=alert.quantity,
        order_type=alert.order_type, price=alert.price,
    )
    _log_order(
        exchange, alert.symbol, alert.side, alert.quantity, alert.order_type, alert.price,
        result["status"], result.get("detail", ""),
    )
    logger.info("Ordre %s sur %s %s: %s", result["status"], exchange, alert.symbol, result.get("detail"))
    return result


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
    return {"status": "ok"}
