# eTrading — TradingView → Automation de trading

Serveur webhook qui reçoit les alertes TradingView et passe des ordres
automatiquement sur des exchanges régulés en Europe (licence MiCA/CASP).

**État actuel :**
- ✅ Bybit (spot, testnet + réel) — fonctionnel, licence MiCA (Bybit EU)
- ✅ Kraken (spot, mode dry-run + réel) — fonctionnel, licence MiCA (Irlande)
- 🔜 MT4/MT5 via MetaApi — Phase 4 (stub en place, pas encore implémenté)

> ⚠️ **Binance a été retiré du projet** : la plateforme ne dispose plus d'une
> licence MiCA/CASP valide pour opérer en Europe. Le régime transitoire qui
> permettait encore d'y accéder se termine le **1er juillet 2026**.
> Voir le [registre officiel ESMA](https://www.esma.europa.eu) pour vérifier
> le statut d'une plateforme.

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

## 2. Lancer le serveur

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Ouvrez **http://localhost:8000** → le navigateur demande le login/mot de
passe (`admin` / votre `DASHBOARD_PASSWORD`). C'est votre dashboard.

## 3. Configurer vos clés API depuis le dashboard

Onglet **Clés API** → choisissez la plateforme → collez votre clé/secret
(testnet pour commencer) → Enregistrer. Les clés sont **chiffrées
localement** (fichier `master.key`, généré automatiquement — ne le
supprimez pas, ne le partagez pas) et ne sont jamais réaffichées en clair.

- **Bybit testnet** : créez vos clés sur https://testnet.bybit.com
- **Kraken** : pas de testnet public — laissez "Testnet" coché pour un mode
  *dry-run* (l'ordre est validé par l'API mais jamais exécuté réellement),
  décochez-le uniquement quand vous êtes prêt à trader en réel.

## 4. Exposer le serveur à internet (pour que TradingView puisse l'atteindre)

```bash
# Installation : https://ngrok.com/download
ngrok http 8000
```

Ngrok vous donne une URL publique (ex : `https://abcd1234.ngrok-free.app`).
C'est cette URL + `/webhook` qu'il faudra mettre dans TradingView.

⚠️ Le dashboard sera accessible publiquement via cette URL aussi — c'est
pour ça qu'il est protégé par mot de passe. Choisissez un
`DASHBOARD_PASSWORD` solide avant d'exposer le serveur.

## 5. Configurer l'alerte dans TradingView

1. Collez `demo_strategy.pine` dans l'éditeur Pine Script de TradingView,
   ajoutez-le à un graphique (BTCUSDT par exemple).
2. Remplacez `VOTRE_SECRET_ICI` dans le script par votre `WEBHOOK_SECRET`.
3. 🔔 → Créer une alerte → Condition : votre stratégie → "Ordre rempli".
4. Notifications → Webhook URL → votre URL ngrok + `/webhook`.
5. Validez.

## 6. Suivre l'activité

Tout apparaît en direct dans le dashboard (rafraîchi automatiquement toutes
les 5 secondes) :
- **Vue d'ensemble** : compteurs d'ordres
- **Ordres** : historique complet avec statut (exécuté / erreur / ignoré)
- **Stratégies** : une ligne apparaît automatiquement par couple
  exchange/symbole dès la première alerte reçue — interrupteur pour
  activer/désactiver sans toucher à TradingView
- **Clés API** : gestion centralisée, jamais affichées en clair

---

## Prochaines étapes (sur demande)

- **Phase 4 — MT4/MT5** : via MetaApi (https://metaapi.cloud)
- **Déploiement permanent** : migration de ngrok vers un VPS avec domaine fixe
- **Gestion du risque** : limites de taille d'ordre, stop-loss automatique,
  alertes par email/SMS en cas d'erreur

## ⚠️ Points importants

- Outil d'exécution technique, pas un conseil financier. La stratégie de
  démo (croisement de MA) est un exemple pédagogique, pas une recommandation.
- Testez **toujours** en testnet/dry-run plusieurs jours avant de passer en réel.
- Ne committez jamais `.env`, `master.key` ou `trading.db` dans un dépôt Git
  public (déjà ignorés via `.gitignore`).
- Le dashboard est protégé par mot de passe, mais reste pensé pour un usage
  personnel — pas pour une exposition publique à grande échelle.
- Vérifiez toujours le statut MiCA d'une plateforme avant d'y connecter des
  fonds réels : https://www.esma.europa.eu
