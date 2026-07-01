"""Connecteur Bitpanda — Bitpanda Pro API.

Bitpanda dispose d'une licence MiCA/CASP (via Malte). Doc :
https://developers.bitpanda.com/exchange/
"""
from typing import Optional

import requests

from .base import ExchangeAdapter, NotConfiguredError

BASE_URL = "https://api.exchange.bitpanda.com/public/v1"


class BitpandaAdapter(ExchangeAdapter):
    name = "bitpanda"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        # Bitpanda Pro utilise une clé API simple (pas de secret HMAC séparé) en
        # en-tête Bearer. `api_secret` n'est pas utilisé mais gardé pour
        # cohérence d'interface avec les autres adapters.
        self.api_key = api_key
        self.dry_run = testnet  # Bitpanda n'a pas de testnet public : mode dry-run par défaut

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

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
                raise NotConfiguredError("Clé API Bitpanda manquante")

            instrument_code = symbol.upper() if "_" in symbol else symbol.upper().replace("EUR", "_EUR")
            body = {
                "instrument_code": instrument_code,
                "side": side.upper(),
                "type": "MARKET" if order_type.lower() == "market" else "LIMIT",
                "amount": str(quantity),
            }
            if order_type.lower() == "limit" and price is not None:
                body["price"] = str(price)

            if self.dry_run:
                return {
                    "status": "executed",
                    "detail": f"Ordre Bitpanda simulé (dry run, non envoyé): {body}",
                    "raw": None,
                }

            resp = requests.post(f"{BASE_URL}/account/orders", headers=self._headers(), json=body, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {"status": "executed", "detail": "Ordre Bitpanda exécuté", "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Bitpanda: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            if not self.is_configured():
                raise NotConfiguredError("Clé API Bitpanda manquante")
            resp = requests.get(f"{BASE_URL}/account/balances", headers=self._headers(), timeout=10)
            resp.raise_for_status()
            return {"status": "ok", "raw": resp.json()}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Bitpanda: {e}"}
