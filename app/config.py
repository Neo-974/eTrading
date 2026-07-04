import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Secret partagé avec TradingView pour valider les alertes webhook.
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "change-me")

    # Mot de passe du dashboard (utilisateur fixe : "admin").
    DASHBOARD_PASSWORD: str = os.getenv("DASHBOARD_PASSWORD", "changeme")

    # Chemin de la base SQLite.
    DB_PATH: str = os.getenv("DB_PATH", "trading.db")

    # Fichier contenant la clé de chiffrement des clés API (généré au premier lancement).
    MASTER_KEY_PATH: str = os.getenv("MASTER_KEY_PATH", "master.key")

    # Assistant intégré (optionnel) : clé API Anthropic, distincte d'un abonnement Claude.ai.
    # Créez la vôtre sur https://console.anthropic.com/ — facturée à l'usage.
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


settings = Settings()
