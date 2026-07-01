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


settings = Settings()
