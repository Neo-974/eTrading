"""Assistant intégré au dashboard — appelle l'API Anthropic (clé propre à
l'utilisateur, jamais partagée) avec un contexte sur l'état actuel du bot
(profils actifs, plateformes configurées, activité récente)."""
import datetime
import json as _json

import requests

from config import settings
from db import get_conn

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

SYSTEM_PROMPT_BASE = """Tu es l'assistant intégré au dashboard "eTrading", un bot personnel d'automatisation de trading (TradingView -> webhook -> Bybit / Kraken / OKX / Coinbase / Bitpanda / OANDA / MT5).

Ton rôle : aider l'utilisateur à régler sa stratégie (stop-loss/take-profit, taille de position, coupe-circuits, filtres horaires, levier, etc.), expliquer les résultats du moteur d'analyse du bot, et répondre à ses questions sur le fonctionnement de l'outil.

Règles :
- Tu n'exécutes aucune action toi-même (pas d'ordre, pas de modification de réglages) : tu conseilles, l'utilisateur applique lui-même les changements dans le dashboard.
- Sois concret : propose des valeurs précises et justifie-les brièvement, plutôt que de rester général.
- Tu n'es pas conseiller financier ; rappelle-le si la question s'y prête (décision d'investissement, prédiction de marché), mais ne le répète pas à chaque message pour des questions purement techniques de configuration.
- Réponds en français, de façon concise et directe.
"""


def build_context() -> str:
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    with get_conn() as conn:
        profiles = conn.execute("SELECT * FROM bot_profiles WHERE is_active=1").fetchall()
        recent_orders = conn.execute(
            "SELECT status, COUNT(*) as c FROM orders WHERE created_at LIKE ? GROUP BY status", (f"{today}%",)
        ).fetchall()
        keys = conn.execute("SELECT exchange, testnet FROM api_keys").fetchall()
        pending = conn.execute("SELECT COUNT(*) as c FROM pending_orders WHERE status='pending'").fetchone()

    lines = ["Contexte actuel de l'utilisateur (à utiliser pour personnaliser tes réponses) :"]

    if profiles:
        lines.append("Profils actifs :")
        for p in profiles:
            s = _json.loads(p["settings_json"])
            non_empty = {k: v for k, v in s.items() if v not in (None, False, "")}
            lines.append(f"- '{p['name']}' sur {p['exchange']}/{p['symbol']}: {_json.dumps(non_empty, ensure_ascii=False)}")
    else:
        lines.append("Aucun profil actif actuellement (le bot applique les alertes sans restriction).")

    configured = [k for k in keys if k["exchange"] != "okx_passphrase"]
    if configured:
        lines.append("Plateformes configurées : " + ", ".join(
            f"{k['exchange']} ({'testnet/dry-run' if k['testnet'] else 'RÉEL'})" for k in configured
        ))
    else:
        lines.append("Aucune plateforme configurée pour le moment.")

    if recent_orders:
        lines.append("Ordres aujourd'hui : " + ", ".join(f"{r['c']} {r['status']}" for r in recent_orders))
    else:
        lines.append("Aucun ordre aujourd'hui.")

    if pending and pending["c"]:
        lines.append(f"{pending['c']} ordre(s) en attente de validation manuelle.")

    return "\n".join(lines)


def chat(message: str, history: list, include_context: bool = True) -> str:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Clé API Anthropic non configurée (ANTHROPIC_API_KEY dans .env).")

    system_prompt = SYSTEM_PROMPT_BASE
    if include_context:
        system_prompt += "\n\n" + build_context()

    messages = history + [{"role": "user", "content": message}]

    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    body = {"model": settings.ANTHROPIC_MODEL, "max_tokens": 1024, "system": system_prompt, "messages": messages}
    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
