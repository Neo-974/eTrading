"""Connecteur MT4/MT5 via MetaApi — stub, non implémenté (Phase 4).

Doc : https://metaapi.cloud/docs/client/
"""
from typing import Optional

from .base import ExchangeAdapter


class MT5Adapter(ExchangeAdapter):
    name = "mt5"

    def __init__(self, account_id: str = "", token: str = ""):
        self.account_id = account_id
        self.token = token

    def is_configured(self) -> bool:
        return bool(self.account_id and self.token)

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> dict:
        return {
            "status": "error",
            "detail": "Connecteur MT4/MT5 pas encore implémenté (Phase 4, via MetaApi).",
            "raw": None,
        }

    def get_account_balance(self) -> dict:
        return {"status": "error", "detail": "Non implémenté (Phase 4)."}
