"""Connecteur Bybit — API v5 (spot + dérivés).

Bybit EU dispose d'une licence CASP/MiCA. Testnet : https://testnet.bybit.com
Doc API : https://bybit-exchange.github.io/docs/v5/intro
"""
import hashlib
import hmac
import time
from typing import Optional

import requests

from .base import ExchangeAdapter, NotConfiguredError

MAINNET_URL = "https://api.bybit.com"
TESTNET_URL = "https://api-testnet.bybit.com"


class BybitAdapter(ExchangeAdapter):
    name = "bybit"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = TESTNET_URL if testnet else MAINNET_URL

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _sign(self, payload: str, timestamp: str, recv_window: str = "5000") -> str:
        pre_sign = f"{timestamp}{self.api_key}{recv_window}{payload}"
        return hmac.new(
            self.api_secret.encode("utf-8"), pre_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: Optional[dict] = None) -> dict:
        if not self.is_configured():
            raise NotConfiguredError("Clés API Bybit manquantes")

        params = params or {}
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"

        if method == "GET":
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = self._sign(query, timestamp, recv_window)
        else:
            import json as _json

            query = _json.dumps(params)
            signature = self._sign(query, timestamp, recv_window)

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{path}"
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=headers, json=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> dict:
        try:
            params = {
                "category": "spot",
                "symbol": symbol.upper(),
                "side": "Buy" if side.lower() == "buy" else "Sell",
                "orderType": "Market" if order_type.lower() == "market" else "Limit",
                "qty": str(quantity),
            }
            if order_type.lower() == "limit" and price is not None:
                params["price"] = str(price)

            data = self._request("POST", "/v5/order/create", params)
            if data.get("retCode") == 0:
                return {"status": "executed", "detail": "Ordre Bybit exécuté", "raw": data}
            return {
                "status": "error",
                "detail": data.get("retMsg", "Erreur Bybit inconnue"),
                "raw": data,
            }
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Bybit: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            data = self._request(
                "GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"}
            )
            return {"status": "ok", "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Bybit: {e}"}

    def get_candles(self, symbol: str, interval: str = "1h", limit: int = 200) -> list:
        # Endpoint public, pas besoin de clés API.
        interval_map = {"15m": "15", "1h": "60", "4h": "240", "1d": "D"}
        params = {
            "category": "spot",
            "symbol": symbol.upper(),
            "interval": interval_map.get(interval, "60"),
            "limit": str(limit),
        }
        resp = requests.get(f"{MAINNET_URL}/v5/market/kline", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("result", {}).get("list", [])
        candles = [
            {
                "time": int(int(r[0]) / 1000),
                "open": float(r[1]), "high": float(r[2]), "low": float(r[3]), "close": float(r[4]),
            }
            for r in rows
        ]
        return sorted(candles, key=lambda c: c["time"])
