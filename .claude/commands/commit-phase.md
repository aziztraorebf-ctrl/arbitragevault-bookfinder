---
description: Crée un Git commit et synchronise automatiquement les fichiers mémoire
---

Je vais finalisier ta session en créant un commit Git cohérent et en mettant à jour la mémoire automatiquement.

## 📋 Étape 1: Analyser le Travail Session

Je vais:
- Lire `git status` pour voir les fichiers modifiés
- Lire `git diff --cached` pour les changements staged
- Lire `git diff` pour les changements unstaged
- Identifier les catégories de changement (feat, fix, docs, etc.)

## 💬 Étape 2: Proposer le Message Commit

Basé sur l'analyse, je vais proposer un message:

```
feat(phase5): [Description brève de ce qui a été fait]

- Détail 1 du changement
- Détail 2 du changement
- Détail 3 du changement

Si besoin:
- Fixes issue #XXX
- Closes #YYY

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Je vais te demander**: Approuves-tu ce message ou veux-tu le modifier?

## ✅ Étape 3: Étapes de Commit

Une fois approuvé, je vais:
```bash
git add .                    # Stage tous les changements
git commit -m "[message approuvé]"
git log -1 --oneline        # Montrer le commit créé
```

## 📝 Étape 4: Synchroniser la Mémoire

Automatiquement après commit réussi, je vais:
- Lire le commit hash (ex: `a1b2c3d`)
- Ajouter une entrée CHANGELOG dans `compact_current.md`:
  ```
  ### [Date]
  - HH:MM | ✅ [Commit hash] - [Description du commit]
  ```
- Mettre à jour QUICK REFERENCE si nécessaire (status changes)
- Ajouter les commits au fichier mémoire

## 🔄 Étape 5: Finaliser la Synchronisation

Je vais:
- Lire la dernière entrée CHANGELOG (celle que je viens d'ajouter)
- Afficher un résumé de ce qui a été fait
- Montrer l'heure de fin de session

## 📊 Résumé Final

Je vais te montrer:
```
Session Summary:
- Commits créés: 1
- Fichiers modifiés: X
- Lignes changées: +XXX -XXX
- Durée session: X minutes
- Prochaine action: [suggérée]

Memory Sync:
✅ CHANGELOG updated
✅ Commit hash recorded
✅ compact_current.md synchronized

À la prochaine session:
1. Fais /load-context pour charger le contexte
2. Tu verras ce commit enregistré dans CHANGELOG
3. Continue depuis la prochaine action suggérée
```

## 🚀 Procédons

Analysons d'abord ce que tu as changé dans cette session.
