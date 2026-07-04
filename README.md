# eTrading — Bot d'automatisation TradingView multi-plateformes

Serveur webhook qui reçoit les alertes TradingView et passe des ordres
automatiquement sur des plateformes régulées en Europe (licence MiCA/CASP),
avec un système de **profils de réglages** pour piloter le comportement du
bot (stop-loss/take-profit, coupe-circuit de perte, plages horaires, listes
de symboles autorisés, limite de trades simultanés) — enregistrables et
activables selon vos scénarios de test ou la conjoncture du marché.

## Plateformes supportées

**Crypto** (licence MiCA/CASP) :
- ✅ **Bybit** — spot/dérivés, testnet + réel (Bybit EU)
- ✅ **Kraken** — spot, mode dry-run + réel (licence Irlande)
- ✅ **OKX** — spot, testnet (`x-simulated-trading`) + réel (licence Malte)
- ✅ **Coinbase** — Advanced Trade, mode dry-run + réel (licence Luxembourg)
- ✅ **Bitpanda** — Bitpanda Pro, mode dry-run + réel (licence Malte)

**Forex/CFD** :
- ✅ **OANDA** — compte de pratique + réel, régulé (Irlande)
- 🔜 **MT4/MT5 via MetaApi** — Phase 4, stub en place (connecte n'importe
  quel broker proposant MT4/MT5)

**Autre** : si vous avez besoin d'**Interactive Brokers**, il est déjà
accessible séparément via son propre connecteur MCP — pas besoin de
dupliquer l'intégration ici sauf si vous voulez le piloter par les mêmes
alertes TradingView (dites-le et on l'ajoute).

> ⚠️ **Binance a été retiré du projet** : la plateforme ne dispose plus
> d'une licence MiCA/CASP valide pour opérer en Europe depuis le
> **1er juillet 2026**. Vérifiez toujours le statut d'une plateforme sur le
> [registre officiel ESMA](https://www.esma.europa.eu) avant d'y connecter
> des fonds réels.

---

## 1. Installation

```bash
git clone https://github.com/Neo-974/eTrading.git
cd eTrading
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Ouvrez `.env` et remplacez `WEBHOOK_SECRET` et `DASHBOARD_PASSWORD` par des
valeurs solides (génération : `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`).

### Raccourci Windows (lancement en un clic)

Si vous êtes sous Windows, deux scripts sont fournis dans `scripts/` pour
éviter de retaper les commandes à chaque fois :

1. **Une seule fois** : double-cliquez sur `scripts/create-desktop-shortcut.vbs`
   → un raccourci **"eTrading"** apparaît sur votre Bureau.
2. **À chaque lancement** : double-cliquez sur ce raccourci. Il installe
   automatiquement l'environnement virtuel et les dépendances si besoin
   (uniquement au premier lancement), crée le `.env` s'il n'existe pas, puis
   démarre le serveur et ouvre http://localhost:8000 dans votre navigateur.

Le fichier `.env` est chargé automatiquement par le serveur (via
`python-dotenv`) — pas besoin de le charger manuellement dans le terminal.

## 2. Lancer le serveur

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Ouvrez **http://localhost:8000** → login `admin` / votre `DASHBOARD_PASSWORD`.

## 3. Configurer vos clés API depuis le dashboard (onglet "Clés API")

| Plateforme | Champs à renseigner |
|---|---|
| Bybit | API Key / API Secret (testnet : https://testnet.bybit.com) |
| Kraken | API Key / API Secret (pas de testnet public → laissez "Testnet" coché = mode dry-run, l'ordre est validé mais jamais exécuté) |
| OKX | API Key / API Secret / **Passphrase** (définie à la création de la clé) — testnet = demo trading OKX |
| Coinbase | API Key = `organizations/{org_id}/apiKeys/{key_id}`, API Secret = clé privée EC (format PEM) — générées sur https://portal.cdp.coinbase.com/. Pas de testnet public → mode dry-run par défaut |
| Bitpanda | API Key uniquement (laissez API Secret vide) — pas de testnet public → mode dry-run par défaut |
| OANDA | API Key = jeton d'accès personnel, API Secret = identifiant de compte (ex `101-004-...`) — compte de pratique gratuit sur https://www.oanda.com/apply/demo/ |
| MT5 | Non implémenté (Phase 4) |

Les clés sont **chiffrées localement** (`master.key`, généré
automatiquement — ne le supprimez pas, ne le partagez pas) et jamais
réaffichées en clair.

## 4. Configurer les réglages du bot (onglet "Profils / Réglages")

Créez un profil par couple exchange/symbole (ou `*` pour tout l'exchange) :
stop-loss/take-profit en %, nombre max de pertes/jour (coupe-circuit),
plage horaire de trading (UTC), liste blanche de symboles, nombre max de
trades simultanés. Enregistrez plusieurs profils ("Agressif BTC", "Prudent
nuit forex"...) et activez celui qui correspond à votre scénario — un seul
profil actif à la fois par couple exchange/symbole.

Le webhook applique automatiquement le profil actif avant de transmettre
l'ordre à la plateforme, et journalise la raison si un ordre est bloqué.

> ℹ️ Le coupe-circuit de perte journalière et le calcul SL/TP sont des
> approximations en beta (pas de suivi de P&L en temps réel intégré) —
> testez en dry-run/testnet avant d'en dépendre en réel.

## 5. Exposer le serveur à internet (pour que TradingView puisse l'atteindre)

```bash
ngrok http 8000
```

C'est l'URL ngrok + `/webhook` qu'il faut mettre dans TradingView.
⚠️ Le dashboard sera aussi accessible via cette URL — protégez-le avec un
`DASHBOARD_PASSWORD` solide avant d'exposer le serveur.

## 6. Configurer l'alerte dans TradingView

1. Collez `demo_strategy.pine` dans l'éditeur Pine Script, ajoutez-le à un
   graphique.
2. Remplacez `VOTRE_SECRET_ICI` par votre `WEBHOOK_SECRET`.
3. 🔔 → Créer une alerte → Condition : votre stratégie → "Ordre rempli".
4. Notifications → Webhook URL → votre URL ngrok + `/webhook`.

Format JSON attendu par `/webhook` :
```json
{"secret": "...", "exchange": "bybit", "symbol": "BTCUSDT", "side": "buy", "order_type": "market", "quantity": 0.001, "price": null}
```

## 7. Suivre l'activité

Dashboard rafraîchi automatiquement toutes les 5 secondes :
- **Vue d'ensemble** : compteurs d'ordres
- **Ordres** : historique complet, statut (exécuté / erreur / ignoré) et
  raison (ex : bloqué par un profil, clé API manquante...)
- **Stratégies** : activation/désactivation par couple exchange/symbole
- **Profils / Réglages** : gestion des scénarios de trading

---

## 8. Assistant intégré (optionnel)

Un onglet **"Assistant"** vous accompagne pour régler votre stratégie, en
dialoguant directement avec Claude (API Anthropic — clé personnelle,
facturée à l'usage, distincte d'un abonnement Claude.ai) :

1. Créez une clé sur https://console.anthropic.com/
2. Ajoutez-la dans `.env` : `ANTHROPIC_API_KEY=sk-ant-...`
3. Redémarrez le serveur

L'assistant voit automatiquement vos profils actifs, vos plateformes
configurées et votre activité du jour (décochez la case "Inclure mes
profils..." si vous préférez une discussion sans ce contexte). Il conseille
et explique — il ne modifie jamais vos réglages ni ne passe d'ordre lui-même.

## Prochaines étapes (sur demande)

- **MT4/MT5 via MetaApi** (Phase 4)
- **Interactive Brokers** en connecteur direct dans le webhook (si besoin
  de le piloter par les mêmes alertes TradingView que le reste)
- **Position sizing en % du capital** (actuellement quantité fixe dans
  l'alerte — un calcul automatique nécessite une normalisation fiable du
  solde par plateforme, en cours de conception)
- **Déploiement permanent** : migration de ngrok vers un VPS avec domaine fixe
- **Suivi de P&L en temps réel** pour un coupe-circuit de perte précis

## ⚠️ Points importants

- Outil d'exécution technique, pas un conseil financier. La stratégie de
  démo (croisement de MA) est un exemple pédagogique.
- Testez **toujours** en testnet/dry-run plusieurs jours avant de passer en réel.
- Ne committez jamais `.env`, `master.key` ou `trading.db` (déjà ignorés
  via `.gitignore`).
- Le dashboard est protégé par mot de passe mais pensé pour un usage
  personnel, pas pour une exposition publique à grande échelle.
- Vérifiez toujours le statut MiCA d'une plateforme avant d'y connecter des
  fonds réels : https://www.esma.europa.eu
