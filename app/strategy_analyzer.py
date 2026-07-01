"""Analyse d'un ensemble de réglages de stratégie selon des règles de gestion
du risque usuelles (pas un conseil financier, pas d'IA externe — un moteur de
règles explicable et reproductible)."""


def analyze(s: dict) -> dict:
    positives = []
    warnings = []
    critical = []
    score = 100

    sl = s.get("stop_loss_pct")
    tp = s.get("take_profit_pct")
    leverage = s.get("leverage") or 1
    style = s.get("trading_style")
    timeframe = s.get("timeframe")
    direction = s.get("direction")
    risk_per_trade = s.get("risk_per_trade_pct")

    # --- Stop-loss / Take-profit ---
    if not sl:
        critical.append("Aucun stop-loss défini : une position peut théoriquement perdre bien plus que prévu si le marché se retourne fortement.")
        score -= 25
    elif sl > 15:
        warnings.append(f"Stop-loss large ({sl}%) : une seule perte peut effacer plusieurs gains habituels.")
        score -= 10
    elif sl < 0.3:
        warnings.append(f"Stop-loss très serré ({sl}%) : risque d'être sorti par du simple bruit de marché, hors mouvement réel.")
        score -= 8
    else:
        positives.append(f"Stop-loss dans une fourchette raisonnable ({sl}%).")

    if sl and tp:
        rr = tp / sl
        if rr < 1:
            warnings.append(f"Ratio risque/rendement défavorable ({rr:.1f}:1, TP < SL) : il faut un taux de réussite élevé pour être rentable dans la durée.")
            score -= 12
        elif rr >= 2:
            positives.append(f"Bon ratio risque/rendement ({rr:.1f}:1) : viable même avec un taux de réussite modeste (<50%).")
            score += 5
        else:
            positives.append(f"Ratio risque/rendement correct ({rr:.1f}:1).")
    elif tp and not sl:
        pass  # déjà signalé plus haut
    elif not tp:
        warnings.append("Aucun take-profit défini : les gains ne sont sécurisés que manuellement ou via le signal d'entrée inverse.")
        score -= 6

    # --- Trailing stop / breakeven / TP partiel ---
    if s.get("trailing_stop_enabled"):
        if style == "scalping":
            warnings.append("Trailing stop activé avec un style 'scalping' : sur des mouvements très courts et bruités, il peut couper la position prématurément.")
            score -= 5
        else:
            positives.append("Trailing stop activé : permet de laisser courir les gains sur une tendance forte.")
    if s.get("breakeven_enabled"):
        positives.append("Passage au seuil de rentabilité (breakeven) activé : réduit le risque une fois le trade en gain.")
    if s.get("partial_tp_enabled"):
        positives.append("Prise de profit partielle activée : sécurise une partie du gain tôt, réduit le risque de voir un trade gagnant se retourner en perte.")

    # --- Taille de position & levier ---
    if leverage and leverage > 20:
        critical.append(f"Levier très élevé ({leverage}x) : une position peut être liquidée sur un mouvement de marché de seulement quelques pourcents.")
        score -= 25
    elif leverage and leverage > 5:
        warnings.append(f"Levier modéré à élevé ({leverage}x) : amplifie fortement les pertes autant que les gains.")
        score -= 10
    elif leverage and leverage <= 1:
        positives.append("Pas d'effet de levier : le risque est limité au capital réellement engagé.")

    if risk_per_trade:
        if risk_per_trade > 5:
            critical.append(f"Risque par trade élevé ({risk_per_trade}% du capital) : quelques pertes consécutives peuvent entamer sérieusement le capital.")
            score -= 15
        elif risk_per_trade <= 1:
            positives.append(f"Risque par trade conservateur ({risk_per_trade}%), cohérent avec les pratiques de gestion de risque professionnelles (souvent 0,5–1%).")
        else:
            positives.append(f"Risque par trade modéré ({risk_per_trade}%).")

    # --- Coupe-circuits ---
    if not s.get("max_daily_loss") and not s.get("max_daily_loss_pct"):
        warnings.append("Aucun coupe-circuit de perte journalière : le bot peut continuer à trader après une série de pertes.")
        score -= 10
    else:
        positives.append("Coupe-circuit de perte journalière configuré.")

    if s.get("consecutive_losses_pause"):
        positives.append("Pause automatique après pertes consécutives configurée : évite de s'acharner sur une série perdante.")

    if not s.get("max_concurrent_trades"):
        warnings.append("Aucune limite de trades simultanés : l'exposition totale du compte n'est pas plafonnée.")
        score -= 8
    else:
        positives.append("Limite de trades simultanés définie.")

    if not s.get("max_trades_per_day"):
        warnings.append("Aucune limite de trades par jour : un marché très volatil pourrait déclencher un grand nombre d'ordres.")
        score -= 5

    # --- Filtres de marché ---
    if s.get("trading_start_hour") is None and s.get("trading_end_hour") is None:
        warnings.append("Trading actif 24h/24 : assurez-vous que la stratégie a été testée sur toutes les sessions de marché (asiatique, européenne, US).")
        score -= 3
    else:
        positives.append("Plage horaire de trading restreinte.")

    if not s.get("trading_days"):
        pass  # neutre, pas de restriction n'est pas forcément un défaut
    else:
        positives.append("Jours de trading restreints.")

    if not s.get("symbol_whitelist"):
        warnings.append("Aucune liste blanche de symboles : toute alerte reçue, même sur un symbole imprévu, sera traitée.")
        score -= 4

    # --- Cohérence style / timeframe ---
    short_tf = timeframe in ("1m", "5m", "15m")
    long_tf = timeframe in ("4h", "1d")
    if style == "scalping" and long_tf:
        warnings.append(f"Style 'scalping' associé à un timeframe long ({timeframe}) : incohérence possible entre la vitesse d'exécution visée et l'horizon des signaux.")
        score -= 6
    if style in ("swing", "position") and short_tf:
        warnings.append(f"Style '{style}' associé à un timeframe court ({timeframe}) : incohérence possible, le swing/position trading se base généralement sur des timeframes plus larges.")
        score -= 6
    if style and timeframe and not ((style == "scalping" and long_tf) or (style in ("swing", "position") and short_tf)):
        positives.append(f"Style '{style}' cohérent avec le timeframe choisi ({timeframe}).")

    # --- Sécurité opérationnelle ---
    if s.get("confirm_before_execution"):
        positives.append("Validation manuelle avant exécution activée : sécurité supplémentaire, au prix d'un temps de réaction plus long.")
    else:
        warnings.append("Exécution automatique sans validation manuelle : rapide, mais aucune vérification humaine avant l'envoi de l'ordre réel.")

    if direction and direction != "both":
        positives.append(f"Direction restreinte ({'achat uniquement' if direction == 'long_only' else 'vente uniquement'}) : réduit l'exposition à un seul sens de marché.")

    score = max(0, min(100, score))
    if score >= 80:
        verdict = "Réglages globalement solides et prudents. Testez tout de même en dry-run/testnet avant de passer en réel."
    elif score >= 55:
        verdict = "Profil correct mais avec plusieurs points d'attention à corriger avant une mise en production sérieuse."
    elif score >= 30:
        verdict = "Profil à risque élevé — plusieurs réglages fondamentaux de gestion du risque manquent ou sont agressifs. À revoir avant tout usage en réel."
    else:
        verdict = "Profil très risqué tel quel. Ne pas utiliser en réel sans revoir la gestion du risque en profondeur."

    return {
        "score": score,
        "verdict": verdict,
        "positives": positives,
        "warnings": warnings,
        "critical": critical,
    }
