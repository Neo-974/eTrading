"""Connecteur OANDA — API v20 (Forex/CFD).

OANDA est régulé en Europe (Irlande, banque centrale d'Irlande). Compte de
pratique (démo) gratuit et instantané sur https://www.oanda.com/apply/demo/
Doc : https://developer.oanda.com/rest-live-v20/introduction/

Champs utilisés (via le formulaire "Clés API" du dashboard) :
  - api_key    = jeton d'accès personnel OANDA ("Personal Access Token")
  - api_secret = identifiant de compte OANDA (ex: "101-004-12345678-001")
  - testnet    = True → environnement de pratique (fxpractice), False → réel (fxtrade)
"""
from typing import Optional

import requests

from .base import ExchangeAdapter, NotConfiguredError

PRACTICE_URL = "https://api-fxpractice.oanda.com"
LIVE_URL = "https://api-fxtrade.oanda.com"


class OandaAdapter(ExchangeAdapter):
    name = "oanda"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.access_token = api_key
        self.account_id = api_secret
        self.base_url = PRACTICE_URL if testnet else LIVE_URL

    def is_configured(self) -> bool:
        return bool(self.access_token and self.account_id)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

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
                raise NotConfiguredError("Jeton d'accès ou identifiant de compte OANDA manquant")

            # OANDA attend un format d'instrument du type EUR_USD, et des unités
            # négatives pour une vente.
            instrument = symbol.upper() if "_" in symbol else symbol.upper()
            units = quantity if side.lower() == "buy" else -quantity

            order = {
                "type": "MARKET" if order_type.lower() == "market" else "LIMIT",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK" if order_type.lower() == "market" else "GTC",
                "positionFill": "DEFAULT",
            }
            if order_type.lower() == "limit" and price is not None:
                order["price"] = str(price)

            url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
            resp = requests.post(url, headers=self._headers(), json={"order": order}, timeout=10)
            data = resp.json()
            if resp.ok and "orderFillTransaction" in data or "orderCreateTransaction" in data:
                return {"status": "executed", "detail": "Ordre OANDA exécuté", "raw": data}
            return {
                "status": "error",
                "detail": data.get("errorMessage", "Erreur OANDA inconnue"),
                "raw": data,
            }
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau OANDA: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            if not self.is_configured():
                raise NotConfiguredError("Jeton d'accès ou identifiant de compte OANDA manquant")
            url = f"{self.base_url}/v3/accounts/{self.account_id}/summary"
            resp = requests.get(url, headers=self._headers(), timeout=10)
            resp.raise_for_status()
            return {"status": "ok", "raw": resp.json()}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau OANDA: {e}"}
