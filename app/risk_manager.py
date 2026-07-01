"""Vérifications de risque appliquées avant chaque ordre, selon le profil actif."""
import json
from datetime import datetime, timezone
from typing import Optional

from db import get_conn


def get_active_profile(exchange: str, symbol: str) -> Optional[dict]:
    """Cherche un profil actif pour ce couple exchange/symbole, sinon un profil
    'global' (symbol='*') pour cet exchange, sinon None (aucune restriction)."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM bot_profiles
               WHERE exchange=? AND symbol=? AND is_active=1
               ORDER BY id DESC LIMIT 1""",
            (exchange, symbol.upper()),
        ).fetchone()
        if row is None:
            row = conn.execute(
                """SELECT * FROM bot_profiles
                   WHERE exchange=? AND symbol='*' AND is_active=1
                   ORDER BY id DESC LIMIT 1""",
                (exchange,),
            ).fetchone()
    if row is None:
        return None
    profile = dict(row)
    profile["settings"] = json.loads(profile["settings_json"])
    return profile


def check_trading_hours(settings: dict) -> Optional[str]:
    start = settings.get("trading_start_hour")
    end = settings.get("trading_end_hour")
    if start is None or end is None:
        return None
    hour = datetime.now(timezone.utc).hour
    in_window = (start <= hour < end) if start <= end else (hour >= start or hour < end)
    if not in_window:
        return f"Hors plage horaire autorisée ({start}h-{end}h UTC)"
    return None


def check_symbol_whitelist(settings: dict, symbol: str) -> Optional[str]:
    whitelist = settings.get("symbol_whitelist")
    if not whitelist:
        return None
    allowed = [s.strip().upper() for s in whitelist.split(",") if s.strip()]
    if allowed and symbol.upper() not in allowed:
        return f"Symbole {symbol} non autorisé par la liste blanche du profil"
    return None


def check_direction(settings: dict, side: str) -> Optional[str]:
    direction = settings.get("direction")
    if not direction or direction == "both":
        return None
    if direction == "long_only" and side.lower() != "buy":
        return "Profil configuré en 'Long uniquement' — ordre de vente refusé"
    if direction == "short_only" and side.lower() != "sell":
        return "Profil configuré en 'Short uniquement' — ordre d'achat refusé"
    return None


def check_trading_days(settings: dict) -> Optional[str]:
    days = settings.get("trading_days")
    if not days:
        return None
    allowed = [d.strip().lower() for d in days.split(",") if d.strip()]
    if not allowed:
        return None
    today = datetime.now(timezone.utc).strftime("%a").lower()  # 'mon', 'tue', ...
    if today not in allowed:
        return f"Trading désactivé ce jour ({today}) par le profil"
    return None


def check_max_trades_per_day(settings: dict, exchange: str) -> Optional[str]:
    max_per_day = settings.get("max_trades_per_day")
    if not max_per_day:
        return None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM orders WHERE exchange=? AND status='executed' AND created_at LIKE ?",
            (exchange, f"{today}%"),
        ).fetchone()["c"]
    if count >= int(max_per_day):
        return f"Nombre max de trades aujourd'hui atteint ({count}/{max_per_day})"
    return None


def check_consecutive_losses(settings: dict, exchange: str) -> Optional[str]:
    max_consecutive = settings.get("consecutive_losses_pause")
    if not max_consecutive:
        return None
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT detail FROM orders WHERE exchange=? AND status='executed' ORDER BY id DESC LIMIT ?",
            (exchange, int(max_consecutive)),
        ).fetchall()
    if len(rows) < int(max_consecutive):
        return None
    # Approximation : basé sur le mot-clé 'loss' dans le détail journalisé (pas de P&L réel suivi).
    if all("loss" in (r["detail"] or "").lower() for r in rows):
        return f"Pause automatique : {max_consecutive} pertes consécutives détectées"
    return None


def check_daily_loss_limit(settings: dict, exchange: str) -> Optional[str]:
    max_daily_loss = settings.get("max_daily_loss")
    if not max_daily_loss:
        return None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM orders WHERE exchange=? AND status='executed'
               AND created_at LIKE ?""",
            (exchange, f"{today}%"),
        ).fetchall()
    # Approximation : sans flux de prix en temps réel, on ne peut pas calculer
    # un P&L exact ici. On compte le nombre d'ordres perdants explicitement
    # journalisés comme tels (si le champ 'detail' le mentionne), sinon on
    # laisse passer — le coupe-circuit précis nécessite un module de suivi
    # de position à part (roadmap).
    losing = [r for r in rows if "loss" in (r["detail"] or "").lower()]
    if len(losing) >= int(max_daily_loss):
        return f"Coupe-circuit : {len(losing)} pertes déjà enregistrées aujourd'hui (limite: {max_daily_loss})"
    return None


def check_max_concurrent_trades(settings: dict, exchange: str, symbol: str) -> Optional[str]:
    max_trades = settings.get("max_concurrent_trades")
    if not max_trades:
        return None
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT side, status FROM orders WHERE exchange=? AND symbol=? AND status='executed'
               ORDER BY id DESC LIMIT 50""",
            (exchange, symbol.upper()),
        ).fetchall()
    open_count = 0
    for r in rows:
        if r["side"].lower() == "buy":
            open_count += 1
        elif r["side"].lower() == "sell" and open_count > 0:
            open_count -= 1
    if open_count >= int(max_trades):
        return f"Nombre max de trades simultanés atteint ({open_count}/{max_trades})"
    return None


def compute_sl_tp(settings: dict, side: str, price: Optional[float]):
    """Retourne (stop_loss_price, take_profit_price) si un prix de référence est
    disponible et que le profil définit des pourcentages SL/TP, sinon (None, None)."""
    sl_pct = settings.get("stop_loss_pct")
    tp_pct = settings.get("take_profit_pct")
    if price is None or (not sl_pct and not tp_pct):
        return None, None
    if side.lower() == "buy":
        sl = price * (1 - sl_pct / 100) if sl_pct else None
        tp = price * (1 + tp_pct / 100) if tp_pct else None
    else:
        sl = price * (1 + sl_pct / 100) if sl_pct else None
        tp = price * (1 - tp_pct / 100) if tp_pct else None
    return sl, tp


def evaluate(exchange: str, symbol: str, side: str, price: Optional[float] = None):
    """Retourne (allowed, reason, profile, sl, tp)."""
    profile = get_active_profile(exchange, symbol)
    if profile is None:
        return True, None, None, None, None

    settings = profile["settings"]

    for check_fn, args in (
        (check_direction, (settings, side)),
        (check_trading_hours, (settings,)),
        (check_trading_days, (settings,)),
        (check_symbol_whitelist, (settings, symbol)),
        (check_daily_loss_limit, (settings, exchange)),
        (check_max_trades_per_day, (settings, exchange)),
        (check_consecutive_losses, (settings, exchange)),
        (check_max_concurrent_trades, (settings, exchange, symbol)),
    ):
        reason = check_fn(*args)
        if reason:
            return False, reason, profile, None, None

    sl, tp = compute_sl_tp(settings, side, price)
    return True, None, profile, sl, tp
