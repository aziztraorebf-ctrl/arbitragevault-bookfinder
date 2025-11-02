---
description: Charge le contexte Phase 5 depuis les fichiers mémoire
---

Tu viens de démarrer une nouvelle session VS Code. Je vais charger ton contexte Phase 5 automatiquement.

## 📚 Étape 1: Charger la mémoire active

Je vais lire `.claude/compact_current.md` pour obtenir:
- Status actuel de Phase 5
- Pages à mettre à jour
- Endpoints à tester
- Bloqueurs actuels
- Prochaines actions

## 🔄 Étape 2: Charger l'historique du projet

Je vais aussi consulter `.claude/compact_master.md` pour:
- Architecture complète du projet
- Historique des phases 1-4 (décisions, bugs, solutions)
- Configuration production Render/Netlify
- Leçons apprises

## ✅ Étape 3: Résumer le contexte

Je vais te fournir:

**QUICK REFERENCE** (30 secondes):
- Phase actuelle
- Status backend/frontend/database
- Keepa API balance
- Bloqueurs (s'il y en a)
- Prochaine action

**Pages à Mettre À Jour** (Phase 5):
- Lister les fichiers UI qui ont besoin de modifications
- Endpoints à intégrer

**Endpoints Production À Tester**:
- URLs Swagger des endpoints clés
- Health check status

**Décisions Récentes**:
- Pourquoi ProactorEventLoop est documenté comme limitation
- Stratégie de testing (Netlify vs local)
- Priorités Phase 5

**Situation Actuelle**:
- Commits récents
- Fichiers modifiés/staged
- Database status
- Keepa tokens restants

Procédons maintenant. Je vais lire tes fichiers contexte.
