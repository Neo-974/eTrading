"""Connecteur Kraken — API REST privée.

Kraken dispose d'une licence CASP/MiCA (Irlande). Pas de vrai testnet public :
utilisez de très petites quantités pour vos premiers tests en réel, ou le
mode "dry run" ci-dessous qui journalise sans envoyer l'ordre.
Doc API : https://docs.kraken.com/rest/
"""
import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Optional

import requests

from .base import ExchangeAdapter, NotConfiguredError

BASE_URL = "https://api.kraken.com"


class KrakenAdapter(ExchangeAdapter):
    name = "kraken"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        # Kraken n'a pas de testnet public officiel pour le trading spot :
        # `testnet=True` active un mode "dry run" (aucun ordre réel envoyé).
        self.dry_run = testnet

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _sign(self, path: str, data: dict) -> str:
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + post_data).encode()
        message = path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _private_request(self, path: str, data: Optional[dict] = None) -> dict:
        if not self.is_configured():
            raise NotConfiguredError("Clés API Kraken manquantes")

        data = data or {}
        data["nonce"] = str(int(time.time() * 1000))
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._sign(path, data),
        }
        resp = requests.post(f"{BASE_URL}{path}", headers=headers, data=data, timeout=10)
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
            if not self.is_configured():
                raise NotConfiguredError("Clés API Kraken manquantes")

            params = {
                "pair": symbol.upper(),
                "type": side.lower(),
                "ordertype": "market" if order_type.lower() == "market" else "limit",
                "volume": str(quantity),
            }
            if order_type.lower() == "limit" and price is not None:
                params["price"] = str(price)

            if self.dry_run:
                params["validate"] = "true"  # Kraken: valide l'ordre sans l'exécuter

            data = self._private_request("/0/private/AddOrder", params)
            if not data.get("error"):
                mode = " (dry run, non exécuté)" if self.dry_run else ""
                return {"status": "executed", "detail": f"Ordre Kraken accepté{mode}", "raw": data}
            return {"status": "error", "detail": "; ".join(data["error"]), "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Kraken: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            data = self._private_request("/0/private/Balance")
            return {"status": "ok", "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Kraken: {e}"}

    def get_candles(self, symbol: str, interval: str = "1h", limit: int = 200) -> list:
        # Endpoint public, pas besoin de clés API.
        interval_map = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}
        params = {"pair": symbol.upper(), "interval": interval_map.get(interval, 60)}
        resp = requests.get(f"{BASE_URL}/0/public/OHLC", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise requests.RequestException("; ".join(data["error"]))
        result = data.get("result", {})
        # La clé du pair dans la réponse peut différer légèrement du symbole demandé.
        pair_key = next((k for k in result if k != "last"), None)
        rows = result.get(pair_key, []) if pair_key else []
        candles = [
            {"time": int(r[0]), "open": float(r[1]), "high": float(r[2]), "low": float(r[3]), "close": float(r[4])}
            for r in rows
        ]
        return candles[-limit:]
