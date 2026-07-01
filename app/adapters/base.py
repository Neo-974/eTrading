"""Interface commune à tous les connecteurs d'exchange."""
from abc import ABC, abstractmethod
from typing import Optional


class ExchangeAdapter(ABC):
    """Tout connecteur (Bybit, Kraken, MT5, ...) doit implémenter cette interface."""

    name: str = "base"

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> dict:
        """Passe un ordre. Doit retourner un dict avec au minimum:
        {"status": "executed" | "error", "detail": str, "raw": Any}
        """
        raise NotImplementedError

    @abstractmethod
    def get_account_balance(self) -> dict:
        """Retourne le solde du compte (pour affichage dashboard)."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        """Retourne False si les clés API sont manquantes."""
        return True


class NotConfiguredError(Exception):
    """Levée quand un adapter est appelé sans clés API configurées."""
