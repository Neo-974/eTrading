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


def datetime_parse(iso_str: str) -> float:
    """Parse un timestamp OANDA (ISO8601 avec nanosecondes) en timestamp UNIX (secondes)."""
    import datetime as dt

    # OANDA renvoie parfois plus de 6 chiffres de précision décimale (nanosecondes),
    # que %f (microsecondes, 6 chiffres) ne gère pas directement.
    base, _, frac = iso_str.rstrip("Z").partition(".")
    frac6 = (frac + "000000")[:6]
    parsed = dt.datetime.strptime(f"{base}.{frac6}", "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


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

    def get_candles(self, symbol: str, interval: str = "1h", limit: int = 200) -> list:
        if not self.is_configured():
            raise NotImplementedError("Configurez d'abord vos clés OANDA pour voir le graphique (pas de données publiques sans authentification).")
        granularity_map = {"15m": "M15", "1h": "H1", "4h": "H4", "1d": "D"}
        url = f"{self.base_url}/v3/instruments/{symbol.upper()}/candles"
        params = {"granularity": granularity_map.get(interval, "H1"), "count": str(limit), "price": "M"}
        resp = requests.get(url, headers=self._headers(), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        candles = []
        for c in data.get("candles", []):
            if not c.get("complete", True):
                continue
            mid = c["mid"]
            candles.append({
                "time": int(datetime_parse(c["time"])),
                "open": float(mid["o"]), "high": float(mid["h"]), "low": float(mid["l"]), "close": float(mid["c"]),
            })
        return candles
