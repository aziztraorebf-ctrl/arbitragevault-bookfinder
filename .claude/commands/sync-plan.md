---
description: Valide la cohérence entre compact_master.md et compact_current.md
---

Je vais vérifier que tes fichiers contexte sont cohérents et à jour.

## ✅ Vérification 1: Structure des Fichiers

Je vais vérifier:
- ✅ `.claude/compact_master.md` existe
- ✅ `.claude/compact_current.md` existe
- ✅ `.claude/commands/` dossier avec 5 commands existe
- ✅ Tailles des fichiers (master > current, logique)

**Résultat**: Si un fichier manque, je te le signale.

## 🔄 Vérification 2: Cohérence de Contenu

Je vais vérifier:
- ✅ Phase listée dans current matches master histoire
- ✅ QUICK REFERENCE dans current utilise données cohérentes avec master
- ✅ Commits récents dans current sont dans git log
- ✅ Keepa balance dans current est plausible

**Résultat**: Je signale toute incohérence (ex: phase current = Phase 6, mais master parle de Phase 5).

## 📋 Vérification 3: CHANGELOG Alignment

Je vais vérifier:
- ✅ Dernière entrée CHANGELOG dans current a un timestamp récent
- ✅ Entrées CHANGELOG ne sont pas dupliquées
- ✅ Ordre chronologique correct (newest first)

**Résultat**: Je te montre les entrées CHANGELOG et vérifie qu'elles ont du sens.

## 🎯 Vérification 4: Status vs Réalité

Je vais vérifier:
- ✅ Status "Phase 5 READY" corresponds à réalité (backend live, frontend à faire, etc.)
- ✅ "Bloqueurs Actuels" matches git status (si aucun bloqueur, pas de fichiers en attente)
- ✅ "Prochaine Action" est cohérente avec COMPLETION CHECKLIST (tâches complétées = prochaine action existe)

**Résultat**: Si status ne correspond pas à réalité, je te l'indique.

## 📊 Vérification 5: Git Alignment

Je vais vérifier:
- ✅ Tous les commits mentionnés dans CHANGELOG existent dans `git log`
- ✅ Pas de commits manquants depuis dernière mise à jour
- ✅ Branch est `main` et à jour

**Résultat**: Récapitulatif des commits vérifiés.

## 🔐 Résumé Final

Je vais te présenter:
```
Sync Status:
✅ Fichiers: OK (3 fichiers détectés)
✅ Contenu: COHÉRENT (phase 5 = cohérent)
✅ CHANGELOG: À JOUR (dernière entrée XX min ago)
✅ Status vs Réalité: ALIGNÉ
✅ Git: SYNCHRONISÉ (N commits vérifiés)

Résultat: 🟢 ALL SYSTEMS GREEN - Aucun problème détecté
```

Ou si problème:
```
⚠️ Sync Issues Détectées:
- Issue 1: Description
- Issue 2: Description

Actions Recommandées:
1. Corriger issue 1
2. Corriger issue 2
3. Re-run /sync-plan après corrections
```

## Procédons

Je vais faire les 5 vérifications maintenant.
