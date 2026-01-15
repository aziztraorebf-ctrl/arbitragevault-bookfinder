# SneakerVault - Design Document

**Date**: 2026-01-14
**Status**: Approved for Implementation
**Author**: Claude + Aziz (Brainstorming Session)

---

## Executive Summary

SneakerVault est une application d'arbitrage sneakers "bricks" (modeles de commodite, non-hype) permettant d'acheter en ligne et revendre sur StockX, GOAT, eBay et Poizon. L'application est un fork d'ArbitrageVault, reutilisant 60-70% de l'architecture existante.

### Objectifs

| Phase | Objectif | Timeline |
|-------|----------|----------|
| Validation | Prouver le processus (sourcing -> vente -> profit) | Mois 1-3 |
| Side Hustle | $500-2000/mois de profit | Mois 4-12 |
| Business Serieux | $3000-8000/mois | Annee 2+ |

### Profil Utilisateur Cible

- Capital initial: $1500 USD
- Localisation: Canada (ventes aux US via 3PL)
- Experience: Deja vendu sur StockX/GOAT
- Temps disponible: Variable (travail full-time)
- Approche: 100% online, automatisation maximale
- Tolerance risque: Moderee -> Evolutive

---

## Architecture Technique

### Stack Technology

| Composant | Technologie | Source |
|-----------|-------------|--------|
| Backend | FastAPI + PostgreSQL + SQLAlchemy 2.0 | Fork ArbitrageVault |
| Frontend | React + TypeScript + Vite + Tailwind | Fork ArbitrageVault |
| Auth | Firebase | Reutilise |
| Database | Neon PostgreSQL | Nouveau cluster |
| Hosting Backend | Render | Nouveau service |
| Hosting Frontend | Netlify | Nouveau site |
| API Pricing | KicksDB | Nouveau |
| API eBay | eBay Browse API | Nouveau |
| Email | SendGrid ou Resend | Nouveau |

### Structure du Projet

```
sneakervault/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── roi_calculations.py      # Adapte: fees multi-plateforme
│   │   │   ├── fees_config.py           # NOUVEAU: StockX/GOAT/eBay/Poizon
│   │   │   └── scoring.py               # Adapte: liquidity scoring
│   │   │
│   │   ├── services/
│   │   │   ├── kicksdb_service.py       # NOUVEAU: API KicksDB
│   │   │   ├── ebay_service.py          # NOUVEAU: eBay Browse API
│   │   │   ├── advisor_service.py       # NOUVEAU: conseiller contextuel
│   │   │   ├── alerts_service.py        # NOUVEAU: alertes email
│   │   │   └── inventory_service.py     # NOUVEAU: gestion inventaire
│   │   │
│   │   ├── models/
│   │   │   ├── sneaker.py               # Modele produit
│   │   │   ├── inventory.py             # Stock + localisation
│   │   │   └── transaction.py           # Achats/ventes
│   │   │
│   │   └── schemas/
│   │       └── *.py                     # Pydantic schemas
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── Advisor/
│   │   │   ├── Inventory/
│   │   │   └── Search/
│   │   │
│   │   └── pages/
│   │       ├── Dashboard.tsx
│   │       ├── Analyze.tsx
│   │       ├── Inventory.tsx
│   │       └── Settings.tsx
│
└── docs/
```

### Ce qu'on Reutilise d'ArbitrageVault (60-70%)

- Auth Firebase (100%)
- Job orchestration async (100%)
- UI Components generiques (ErrorBoundary, EmptyState, Tables)
- Patterns (circuit breaker, caching, validation Pydantic/Zod)
- Structure de tests (unit/integration/e2e)
- ROI calculation logic (adapte pour nouveaux fees)

### Ce qu'on Cree Nouveau (30-40%)

- Integration KicksDB API
- Integration eBay Browse API
- Fee calculator multi-plateforme
- Conseiller contextuel (rules-based)
- Systeme d'alertes email
- Gestion inventaire avec localisation

---

## Modele de Donnees

### Entites Principales

```
USER (Firebase Auth)
    |
    ├── SNEAKER_MODEL
    │   ├── id (PK)
    │   ├── sku
    │   ├── name
    │   ├── brand
    │   ├── colorway
    │   ├── retail_price
    │   ├── release_date
    │   ├── image_url
    │   ├── category (running/basketball/lifestyle)
    │   ├── stockx_url
    │   └── goat_url
    │
    ├── PRICE_DATA (cache)
    │   ├── sneaker_id (FK)
    │   ├── platform (stockx/goat/ebay/poizon)
    │   ├── size
    │   ├── ask_price
    │   ├── bid_price
    │   ├── last_sale
    │   ├── volume_30d
    │   └── timestamp
    │
    ├── INVENTORY
    │   ├── id (PK)
    │   ├── user_id (FK)
    │   ├── sneaker_id (FK)
    │   ├── size
    │   ├── purchase_price
    │   ├── purchase_source
    │   ├── purchase_date
    │   ├── location (enum)
    │   ├── status (enum)
    │   ├── photos (JSON array)
    │   ├── notes
    │   ├── tracking_number
    │   └── 3pl_reference
    │
    └── TRANSACTION
        ├── id (PK)
        ├── user_id (FK)
        ├── inventory_id (FK)
        ├── type (BUY/SELL)
        ├── platform
        ├── amount
        ├── fees (JSON detailed)
        ├── net_profit
        └── date
```

### Enums

```python
class InventoryLocation(str, Enum):
    AT_HOME = "at_home"
    IN_TRANSIT_TO_3PL = "in_transit_to_3pl"
    AT_3PL = "at_3pl"
    CONSIGNMENT_GOAT = "consignment_goat"
    IN_TRANSIT_TO_BUYER = "in_transit_to_buyer"
    SOLD = "sold"

class InventoryStatus(str, Enum):
    NOT_LISTED = "not_listed"
    LISTED_STOCKX = "listed_stockx"
    LISTED_GOAT = "listed_goat"
    LISTED_EBAY = "listed_ebay"
    LISTED_MULTIPLE = "listed_multiple"
    PENDING_SALE = "pending_sale"
    SOLD = "sold"

class Platform(str, Enum):
    STOCKX = "stockx"
    GOAT = "goat"
    EBAY = "ebay"
    POIZON = "poizon"
```

### Fees Structure (JSON)

```json
{
  "platform_fee": 12.50,
  "payment_processing": 3.75,
  "shipping_to_platform": 14.00,
  "3pl_handling": 5.00,
  "original_shipping": 8.00,
  "total_fees": 43.25
}
```

---

## Features par Phase

### Phase 1 - MVP (Semaines 1-5)

#### P0 - Core (Semaines 1-2)

| Feature | Description | Effort |
|---------|-------------|--------|
| Auth Firebase | Login/Register (reutilise) | 1 jour |
| KicksDB Integration | Prix temps reel StockX/GOAT | 3 jours |
| Recherche Sneaker | Par SKU, nom, ou URL | 2 jours |
| ROI Calculator | Fees multi-plateforme, profit net | 2 jours |
| Compare Platforms | StockX vs GOAT vs eBay - ou vendre | 1 jour |

#### P1 - Inventory (Semaines 2-3)

| Feature | Description | Effort |
|---------|-------------|--------|
| CRUD Inventory | Ajouter/modifier/supprimer paires | 2 jours |
| Location Tracking | Home, 3PL, Consignment, Transit | 1 jour |
| Photo Upload | Stocker photos pour reference | 1 jour |
| P&L Auto | Calcul profit automatique a la vente | 1 jour |

#### P1 - Dashboard (Semaines 3-4)

| Feature | Description | Effort |
|---------|-------------|--------|
| ROI Moyen | Metriques globales | 1 jour |
| Temps Vente Moyen | Rotation du capital | 1 jour |
| Top Modeles | Liste "a surveiller" (liquides) | 2 jours |
| P&L Global | Profit/perte total | 1 jour |

#### P1 - Conseiller (Semaine 4)

| Feature | Description | Effort |
|---------|-------------|--------|
| Recommandation Plateforme | "Vends sur X pour marge Y%" | 2 jours |
| Alertes ROI | Warning si ROI < seuil | 1 jour |
| Size Analysis | Quelle taille a le meilleur ROI | 1 jour |

#### P2 - Alertes (Semaine 5)

| Feature | Description | Effort |
|---------|-------------|--------|
| Email Prix Cible | Notifier quand prix atteint | 2 jours |
| Email Opportunite | Deal detecte (si source dispo) | 2 jours |
| Configuration Seuils | User definit ses criteres | 1 jour |

### Phase 2 - Post-Validation (Semaines 6-10)

| Feature | Description | Effort |
|---------|-------------|--------|
| eBay Browse Integration | Scanner listings actifs | 1 semaine |
| eBay Deal Finder | Trouver sous-evalues | 1-2 semaines |
| Poizon Price Compare | Arbitrage geo CN/US | 1 semaine |
| Trending Detector | Modeles en hausse | 1 semaine |
| RSS Deals | Slickdeals, Reddit feeds | 3 jours |

### Phase 3 - Expansion (Future)

| Feature | Description |
|---------|-------------|
| Quiz Initial | Strategie personnalisee |
| Assistant IA | Chat data-driven (si budget) |
| Sync Auto | Integration StockX/GOAT APIs |
| Multi-Category | Streetwear, Electronics |

---

## Flux Utilisateur

### Flux 1 : Modes d'Entree

```
┌─────────────────────────────────────────────────────────────────┐
│                    PAGE D'ACCUEIL                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ DECOUVERTE  │  │ RECHERCHE   │  │ SCAN URL    │             │
│  │ "Modeles a  │  │ "Je sais    │  │ "J'ai une   │             │
│  │  surveiller"│  │  ce que je  │  │  URL/SKU"   │             │
│  │             │  │  cherche"   │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flux 2 : Analyse d'un Sneaker

```
1. User entre SKU/nom/URL
2. App fetch prix via KicksDB (StockX, GOAT)
3. User selectionne taille (ou "toutes")
4. App affiche:
   - Prix par plateforme (ask/bid/last sale)
   - ROI estime selon prix d'achat
   - Recommandation: "Vends sur X"
   - Liquidite (volume ventes)
   - Temps de vente estime
5. User peut:
   - Ajouter a inventaire
   - Creer alerte prix
```

### Flux 3 : Gestion Inventaire

```
ACHAT                    STOCK                     VENTE
─────                    ─────                     ─────

User ajoute         User met a jour          Vente confirmee
achat         -->   localisation/status  --> sur plateforme
  |                       |                       |
  v                       v                       v
┌──────────┐         ┌──────────┐          ┌──────────┐
│ Saisie:  │         │ Suivi:   │          │ Cloture: │
│ - Prix   │         │ - @Home  │          │ - Prix   │
│ - Source │         │ - @3PL   │          │   vente  │
│ - Taille │         │ - Listed │          │ - Fees   │
│ - Photo  │         │ - Notes  │          │ - Profit │
└──────────┘         └──────────┘          └──────────┘
```

---

## Sources de Donnees

### MVP - Sources Confirmees

| Source | Usage | Cout | Fiabilite |
|--------|-------|------|-----------|
| KicksDB API | Prix StockX/GOAT temps reel | EUR 29-79/mois | Haute |
| eBay Browse API | Listings actifs (sourcing) | Gratuit | Haute |
| RSS Deals | Slickdeals, Reddit | Gratuit | Moyenne |
| Input Manuel | Deals trouves par user | N/A | User-dependent |

### Phase 2 - Sources Additionnelles

| Source | Usage | Cout | Fiabilite |
|--------|-------|------|-----------|
| Poizon API (OTCommerce) | Prix marche chinois | A determiner | Moyenne |
| eBay Marketplace Insights | Sold data historique | Acces restreint | Haute |
| SERP API | Trending detection | $50/mois | Moyenne |

### Ce que les APIs Fournissent

```
KicksDB Response Example:
{
  "sku": "DD1391-100",
  "name": "Nike Dunk Low Panda",
  "retail_price": 110,
  "stockx": {
    "lowest_ask": 128,
    "highest_bid": 115,
    "last_sale": 125,
    "sales_last_72h": 847
  },
  "goat": {
    "lowest_ask": 132,
    "highest_bid": 118,
    "last_sale": 127
  },
  "price_history": [...],
  "sizes_available": ["8", "8.5", "9", "9.5", "10", ...]
}
```

---

## Fees Calculator

### Structure des Fees par Plateforme

```python
PLATFORM_FEES = {
    "stockx": {
        "seller_fee_pct": Decimal("9.0"),      # 9% (peut descendre a 7%)
        "payment_processing_pct": Decimal("3.0"),
        "shipping_to_stockx": Decimal("0"),    # Prepaid label
    },
    "goat": {
        "commission_pct": Decimal("9.5"),      # 9.5% (12.4% pour Canada)
        "seller_fee": Decimal("5.0"),
        "cashout_fee_pct": Decimal("2.9"),
    },
    "ebay": {
        "final_value_fee_pct": Decimal("13.25"),
        "payment_processing_pct": Decimal("2.9"),
        "payment_processing_fixed": Decimal("0.30"),
    },
    "poizon": {
        "seller_fee_pct": Decimal("7.5"),
        "shipping_international": Decimal("25.0"),
    }
}

# Couts 3PL (KNETGROUP estimate)
THREEPL_FEES = {
    "handling_per_pair": Decimal("5.0"),
    "storage_per_month": Decimal("0"),          # Souvent gratuit
    "receiving": Decimal("0"),                   # Inclus dans handling
}
```

### Formule ROI

```python
def calculate_roi(
    purchase_price: Decimal,
    sale_price: Decimal,
    platform: str,
    use_3pl: bool = True
) -> dict:
    fees = PLATFORM_FEES[platform]

    # Platform fees
    platform_fee = sale_price * fees["seller_fee_pct"] / 100
    processing_fee = sale_price * fees.get("payment_processing_pct", 0) / 100

    # 3PL fees (si applicable)
    threepl_fee = THREEPL_FEES["handling_per_pair"] if use_3pl else 0

    # Shipping (estime)
    shipping_cost = Decimal("8.0")  # Shipping initial au 3PL

    total_fees = platform_fee + processing_fee + threepl_fee + shipping_cost
    net_received = sale_price - total_fees
    profit = net_received - purchase_price
    roi_pct = (profit / purchase_price) * 100

    return {
        "sale_price": sale_price,
        "total_fees": total_fees,
        "net_received": net_received,
        "profit": profit,
        "roi_percent": roi_pct,
        "fee_breakdown": {
            "platform": platform_fee,
            "processing": processing_fee,
            "3pl": threepl_fee,
            "shipping": shipping_cost
        }
    }
```

---

## Logistique

### Modele Recommande : 3PL + Vente Normale

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   ACHAT      │    │    3PL US    │    │  PLATEFORME  │
│  (Nike.com)  │───>│  (KNETGROUP) │───>│ (StockX/GOAT)│
│              │    │              │    │              │
│ Ship direct  │    │ Confirme     │    │ Auth + Ship  │
│ a l'adresse  │    │ reception    │    │ au buyer     │
│ 3PL          │    │ Tu listes    │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 3PL Recommande : KNETGROUP

| Aspect | Detail |
|--------|--------|
| Specialisation | 100% sneakers resale |
| Volume min | 10 unites/semaine (flexible) |
| Cout | ~$5/paire (handling + ship) |
| Plateformes | StockX, GOAT, eBay |
| Feature | Cross-listing auto, evite double-vente |
| Contact | knetgroup.com |

### Alternative : GOAT Consignment

**Note**: Probablement non accessible directement depuis le Canada.
> "Selling from outside of the United States is only available to select sellers at this time."

Workaround: Utiliser 3PL US comme intermediaire.

---

## Strategie de Pricing

### Deux Modes

| Mode | Quand | Comment | Resultat |
|------|-------|---------|----------|
| Rotation Rapide | Debut, capital limite | Vendre au Highest Bid | -$ par paire, +rotation |
| Maximiser | Capital ok, pas presse | Lister entre Bid et Ask | +$ par paire, -rotation |

### Regle Hybride Recommandee

```
SI modele tres liquide (500+ ventes/semaine):
    → Vendre au Bid (rotation rapide)

SI modele moins liquide:
    → Lister entre Bid et Ask
    → Attendre 5 jours
    → Si pas vendu: baisser au Bid
```

### Choix de Plateforme

| Critere | StockX | GOAT |
|---------|--------|------|
| Vente rapide | Meilleur (bid system) | Bon |
| Profit net | ~$174 sur $200 | ~$178 sur $200 |
| Used items | Non | Oui |
| Tiered fees | Oui (volume = moins cher) | Non |

**Recommandation App**: Dynamique - recommander la plateforme selon le modele specifique.

---

## Projections Financieres

### Phase Validation (Mois 1-3)

| Mois | Capital | Paires | ROI Moyen | Profit Net |
|------|---------|--------|-----------|------------|
| 1 | $1500 | 12 | 18% | +$20 |
| 2 | $1400 | 14 | 20% | +$180 |
| 3 | $1500 | 16 | 22% | +$280 |
| **Total** | | | | **+$480** |

### Side Hustle (Mois 4-12)

| Mois | Capital | Profit/Mois |
|------|---------|-------------|
| 6 | $2500 | +$900 - $1200 |
| 12 | $5000 | +$2000 - $2800 |

### Couts Fixes Mensuels

| Cout | Montant |
|------|---------|
| KicksDB API | $35-50 |
| 3PL (10-15 paires) | $50-75 |
| Infra (Render/Netlify) | $15-25 |
| **Total** | **~$100-150/mois** |

---

## Risques et Mitigation

### Risque 1: Contrefacons

| Risque | Mitigation |
|--------|------------|
| Acheter un faux | SEULEMENT retail officiel (Nike.com, etc.) |
| Fausse accusation | Garder tous recus + photos avant envoi |

### Risque 2: Echec Authentification

| Cause | Mitigation |
|-------|------------|
| Condition | Verifier box, yellowing avant listing |
| Erreur taille | Double-check avant de lister |
| Emballage | Box dans box, protection adequate |

### Risque 3: Prix Chute

| Cause | Mitigation |
|-------|------------|
| Restock Nike | Suivre release calendars |
| Oversupply | Focus modeles liquides, vendre vite |

### Risque 4: 3PL Problems

| Cause | Mitigation |
|-------|------------|
| Paire perdue | Assurance sur items >$200 |
| Delai | SLA ecrit (48h max) |
| Communication | 3PL avec confirmation photo |

### Risque 5: Suspension Compte

| Cause | Mitigation |
|-------|------------|
| Cancellations | Ne jamais lister sans avoir la paire |
| Multi-comptes | Un seul compte, toujours |

---

## Expansion Future

### Priorite d'Expansion

```
Phase 1: Sneakers seulement (MVP)
Phase 2: + eBay sourcing, + Poizon
Phase 3: + Streetwear (meme plateformes)
Phase 4: + Electronics (experience existante)
```

### Architecture Extensible

```python
class ProductType(str, Enum):
    SNEAKERS = "sneakers"      # MVP
    STREETWEAR = "streetwear"  # Phase 3
    ELECTRONICS = "electronics" # Phase 4
    COLLECTIBLES = "collectibles"  # Future

# Chaque type a son fee calculator et ses sources
```

---

## Decisions Techniques

### Confirme

| Decision | Justification |
|----------|---------------|
| Fork ArbitrageVault | 60-70% reutilisable, demarrage rapide |
| KicksDB comme source principale | API stable, prix raisonnable |
| eBay Browse API | Gratuit, permet sourcing |
| 3PL (KNETGROUP) | Specialise sneakers, small qty OK |
| Alertes par email | Simple, fiable |
| Conseiller rules-based | Pas d'IA = pas d'hallucinations |

### Reporte a Phase 2+

| Decision | Raison |
|----------|--------|
| Assistant IA conversationnel | Cout + risque hallucinations |
| eBay Marketplace Insights API | Acces restreint |
| Sync auto StockX/GOAT | APIs pas publiques |
| Poizon integration | Valider marche d'abord |

---

## Timeline Implementation

### Semaine 1-2: Core

- [ ] Fork ArbitrageVault, cleanup
- [ ] Setup nouveau Render + Netlify + Neon
- [ ] Integration KicksDB API
- [ ] Recherche sneaker (SKU, nom, URL)
- [ ] ROI Calculator multi-plateforme

### Semaine 2-3: Inventory

- [ ] CRUD inventaire
- [ ] Location tracking
- [ ] Photo upload
- [ ] P&L automatique

### Semaine 3-4: Dashboard + Conseiller

- [ ] Dashboard metriques
- [ ] Liste "modeles a surveiller"
- [ ] Conseiller contextuel
- [ ] Recommandation plateforme

### Semaine 5: Alertes + Polish

- [ ] Systeme alertes email
- [ ] Configuration seuils
- [ ] Tests E2E
- [ ] Deploy production

### Post-MVP (Phase 2)

- [ ] eBay Deal Finder
- [ ] Poizon integration
- [ ] Trending detector
- [ ] RSS deals

---

## Metriques de Succes

### Phase Validation (3 mois)

| Metrique | Target |
|----------|--------|
| Processus valide | Oui (sourcing -> vente -> profit) |
| ROI minimum | > 0% (pas de perte) |
| Paires vendues | 30+ |
| Profit net | > $0 |

### Side Hustle (12 mois)

| Metrique | Target |
|----------|--------|
| Profit mensuel | $1000-2000 |
| ROI moyen | 15-20% |
| Rotation capital | 2x/mois |
| Temps investi | < 10h/semaine |

---

## Prochaines Etapes

1. **Contacter KNETGROUP** pour pricing detaille
2. **S'inscrire KicksDB** et tester l'API
3. **Creer repo sneakervault** (fork)
4. **Commencer implementation** Phase 1

---

## Appendix: Sources et References

### APIs et Services

- [KicksDB - Sneaker Database API](https://kicks.dev/)
- [eBay Browse API](https://developer.ebay.com/api-docs/buy/browse/overview.html)
- [KNETGROUP - Sneaker 3PL](https://www.knetgroup.com/)
- [OTCommerce Poizon API](https://otcommerce.com/poizon-api/)

### Market Research

- [ShelfTrend - Sneaker Resale Margins 2025](https://www.shelftrend.com/fashion/sneaker-resale-profit-margins-2025-marketplace-analysis)
- [StockX Big Facts Report](https://stockx.com/about/stockx-rolls-out-latest-big-facts-report-revealing-top-resale-trends-in-2025/)

### Plateforme Documentation

- [GOAT Seller Fees](https://www.goat.com/fees)
- [GOAT Consignment](https://support.goat.com/hc/en-us/articles/38056343047693-25-Off-Commission-With-Consignment)
- [StockX Seller Guide](https://stockx.com/how-it-works)

---

**Document approuve pour implementation.**
