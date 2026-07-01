"""Connecteur Coinbase — Advanced Trade API.

Coinbase dispose d'une licence MiCA/CASP (Luxembourg, CSSF).
Doc : https://docs.cdp.coinbase.com/advanced-trade/docs/welcome

⚠️ Coinbase utilise désormais des clés "CDP" (Cloud Developer Platform) avec
authentification JWT (clé EC), différentes des anciennes clés API HMAC.
Ce connecteur utilise le format JWT recommandé — générez vos clés sur
https://portal.cdp.coinbase.com/ (section "API Keys" → "Advanced Trade").
"""
import time
from typing import Optional

import jwt
import requests
from cryptography.hazmat.primitives import serialization

from .base import ExchangeAdapter, NotConfiguredError

BASE_URL = "https://api.coinbase.com"
BASE_HOST = "api.coinbase.com"


class CoinbaseAdapter(ExchangeAdapter):
    name = "coinbase"

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        # api_key = "organizations/{org_id}/apiKeys/{key_id}" (fourni par Coinbase CDP)
        # api_secret = clé privée EC au format PEM (fournie par Coinbase CDP)
        self.api_key = api_key
        self.api_secret = api_secret
        # Coinbase n'a pas de testnet public pour Advanced Trade : testnet=True
        # active un mode "dry run" (l'ordre n'est pas envoyé, juste journalisé).
        self.dry_run = testnet

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _build_jwt(self, method: str, path: str) -> str:
        private_key = serialization.load_pem_private_key(self.api_secret.encode(), password=None)
        uri = f"{method} {BASE_HOST}{path}"
        payload = {
            "sub": self.api_key,
            "iss": "cdp",
            "nbf": int(time.time()),
            "exp": int(time.time()) + 120,
            "uri": uri,
        }
        headers = {"kid": self.api_key, "nonce": str(int(time.time() * 1000))}
        return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        if not self.is_configured():
            raise NotConfiguredError("Clés API Coinbase manquantes (CDP key + private key)")

        token = self._build_jwt(method, path)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{BASE_URL}{path}"
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        else:
            resp = requests.post(url, headers=headers, json=body or {}, timeout=10)
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
                raise NotConfiguredError("Clés API Coinbase manquantes (CDP key + private key)")

            product_id = symbol.upper() if "-" in symbol else symbol.upper().replace("USD", "-USD")
            order_config = (
                {"market_market_ioc": {"base_size": str(quantity)}}
                if order_type.lower() == "market"
                else {"limit_limit_gtc": {"base_size": str(quantity), "limit_price": str(price)}}
            )
            body = {
                "client_order_id": f"tv-{int(time.time() * 1000)}",
                "product_id": product_id,
                "side": side.upper(),
                "order_configuration": order_config,
            }

            if self.dry_run:
                return {
                    "status": "executed",
                    "detail": f"Ordre Coinbase simulé (dry run, non envoyé): {body}",
                    "raw": None,
                }

            data = self._request("POST", "/api/v3/brokerage/orders", body)
            if data.get("success"):
                return {"status": "executed", "detail": "Ordre Coinbase exécuté", "raw": data}
            return {
                "status": "error",
                "detail": str(data.get("error_response", "Erreur Coinbase inconnue")),
                "raw": data,
            }
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e), "raw": None}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Coinbase: {e}", "raw": None}

    def get_account_balance(self) -> dict:
        try:
            data = self._request("GET", "/api/v3/brokerage/accounts")
            return {"status": "ok", "raw": data}
        except NotConfiguredError as e:
            return {"status": "error", "detail": str(e)}
        except requests.RequestException as e:
            return {"status": "error", "detail": f"Erreur réseau Coinbase: {e}"}
