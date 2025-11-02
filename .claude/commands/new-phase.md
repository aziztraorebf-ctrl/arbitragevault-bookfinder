---
description: Archive la phase actuelle et crée une nouvelle phase avec confirmation et backup
---

⚠️ **ATTENTION: Ceci est une opération DESTRUCTIVE.** Une fois exécutée, tu ne peux pas revenir en arrière.

## ✅ Prérequis

Avant de continuer, vérifie:
1. ✅ Phase 5 est complétée (toutes les tâches faites)
2. ✅ Tous les changements ont été committés (`git status` clean)
3. ✅ `compact_current.md` a été mis à jour avec les résultats finaux
4. ✅ Tu as validé le PHASE COMPLETION CHECKLIST

## 🔐 Étape 1: Validation de Sécurité

Je vais:
- Vérifier que `git status` est CLEAN (pas de fichiers modifiés)
- Vérifier que `compact_current.md` existe et est à jour
- Vérifier que `compact_master.md` existe

**Si une validation échoue, je m'arrête et te demande de corriger.**

## 💾 Étape 2: Backup Automatique

Je vais:
- Créer une copie de sauvegarde: `.claude/backups/compact_current_phase5_DATE.md`
- Créer une copie du master: `.claude/backups/compact_master_backup_DATE.md`
- Ces backups sont conservés pour l'historique

## 📝 Étape 3: Archivage de Phase 5

Je vais:
- Lire `compact_current.md` complet
- Créer une section "## 📦 Phase 5 Archive" dans `compact_master.md`
- Ajouter tous les détails Phase 5 à l'archive (CHANGELOG, COMPLETION CHECKLIST, etc.)

## 🆕 Étape 4: Créer Phase 6 Vierge

Je vais:
- Créer un nouveau `compact_current.md` pour Phase 6
- Pré-remplir les sections standards (QUICK REFERENCE, HOW TO USE, Slash Commands list)
- Laisser vierge: Pages à mettre à jour, Endpoints, Prochaines actions

## 🔄 Étape 5: Validation Utilisateur

Je vais afficher:
```
Phase 5 Archive Summary:
- Durée: X jours
- Tâches complétées: X/X
- Commits: X
- Dernière action: [timestamp]

Phase 6 Initialized:
- Status: Ready for new work
- Date création: [timestamp]
```

**Je te demande**: Approuves-tu l'archivage? (oui/non)

## 💾 Étape 6: Git Commit

Si tu approuves:
- Git commit de l'archivage + nouveau Phase 6
- Message: `feat(phase6): Archive Phase 5 completion, initialize Phase 6`
- Push to main

## ⚠️ CONFIRMATION REQUISE

Avant je procède, tu DOIS confirmer:
```
/new-phase
[Confirmation required: Do you want to archive Phase 5 and start Phase 6? (yes/no)]
```

Je ne passe à l'étape suivante que si tu dis "yes" explicitement.
