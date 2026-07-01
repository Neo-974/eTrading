"""Connecteur OKX — API v5.

OKX dispose d'une licence MiCA/CASP (Malte). Doc : https://www.okx.com/docs-v5/en/
"""
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from .base import ExchangeAdapter, NotConfiguredError

BASE_URL = "https://www.okx.com"


class OKXAdapter(ExchangeAdapter):
    name = "okx"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True, passphrase: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase  # OKX exige une passphrase définie à la création de la clé API
        self.testnet = testnet  # active x-simulated-trading: 1 (demo trading OKX)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret and self.passphrase)

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"

    def _sign(self, timestamp: str, method: str, path: str, body: str) -> str:
        message = f"{timestamp}{method}{path}{body}"
        mac = hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        if not self.is_configured():
            raise NotConfiguredError("Clés API OKX incomplètes (clé, secret et passphrase requis)")

        import json as _json

        body_str = _json.dumps(body) if body else ""
        timestamp = self._timestamp()
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._sign(timestamp, method, path, body_str),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }
        if self.testnet:
            headers["x-simulated-trading"] = "1"

        url = f"{BASE_URL}{path}"
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        else:
            resp = requests.post(url, headers=headers, data=body_str, timeout=10)
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
            # OKX attend un format d'instrument du type BTC-USDT
            inst_id = symbol.upper() if "-" in symbol else symbol.upper().replace("USDT", "-USDT")
            body = {
                "instId": inst_id,
                "tdMode": "cash",
                "side": side.lower(),
                "ordType": "market" if order_type.lower() == "market" else "limit",
                "sz": str(quantity),
            }
            if order_type.lower() == "limit" and price is not None:
                body["px"] = str(price)

            data = self._request("POST", "/api/v5/trade/order", body)
            if data.get("code") == "0":
                return {"status": "executed", "detail": "Ordre OKX exécuté", "raw": data}
            return {"status": "error", "detail": data.get("msg", "Erreur OKX inconnue"), "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau OKX: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            data = self._request("GET", "/api/v5/account/balance")
            return {"status": "ok", "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau OKX: {e}"}
