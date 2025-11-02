# 🚀 ArbitrageVault Slash Commands Guide

**Version**: 1.0
**Created**: 2 Novembre 2025
**Status**: Active for Phase 5-6

---

## 📚 Overview

5 slash commands sont maintenant disponibles pour gérer automatiquement le système de mémoire du projet ArbitrageVault et maintenir la synchronisation entre code et contexte.

**Configuration** :
- Fichier de configuration : `.claude/slash-commands.json`
- Fichier guide : `.claude/SLASH_COMMANDS_GUIDE.md` (ce fichier)
- Fichiers mémoire : `.claude/compact_master.md` + `.claude/compact_current.md`

---

## 🎯 Commandes Disponibles

### 1️⃣ `/load-context` 📚

**Priorité**: HIGH
**Fréquence**: À chaque nouveau démarrage de session

**Description**: Charge les fichiers contexte depuis `.claude/` pour restaurer l'état du projet

**Utilisation**:
```
Shift+P → /load-context
```

**Résultat attendu**:
- ✅ Fichiers `.claude/compact_current.md` et `.claude/compact_master.md` chargés
- ✅ Résumé 3 points : phase actuelle, tâches en cours, bloqueurs
- ✅ Contexte établi pour la conversation

**Exemple de résultat**:
```
✅ Context chargé:
1. Phase actuelle: Phase 5 - Frontend MVP (MesNiches update + Netlify deploy)
2. Tâches en cours: Pages UI mises à jour, tests E2E production
3. Bloqueurs: Aucun (backend prêt, tokens disponibles)
```

---

### 2️⃣ `/update-compact` 📝

**Priorité**: HIGH
**Fréquence**: À la fin des sessions importantes

**Description**: Propose des mises à jour pour `compact_current.md` basé sur la conversation actuelle

**Utilisation**:
```
Shift+P → /update-compact
```

**Processus**:
1. Je t'affiche 3-5 changements proposés avec format:
   ```
   ### Changement 1
   Fichier: .claude/compact_current.md
   Section: ✅ Fait
   Avant: [texte actuel]
   Après: [texte proposé]
   Raison: Tâche complétée ce jour
   ```

2. Tu valides chaque changement avec "OK" ou proposes des modifications

3. Une fois validé, je mets à jour le fichier

**Exemple**:
```
Changement 1:
- Fichier: .claude/compact_current.md
- Section: 🔧 En cours
- Avant: [ ] MesNiches.tsx - Intégration /api/v1/niches/discover
- Après: [x] MesNiches.tsx - Intégration /api/v1/niches/discover (COMPLÉTÉ)
- Raison: Feature développée et testée

OK? → OUI
```

---

### 3️⃣ `/new-phase` 🎯

**Priorité**: CRITICAL
**Fréquence**: À la fin d'une phase majeure (Phase 5, Phase 6, etc.)

**Description**: Archive la phase actuelle et crée une nouvelle phase vierge

⚠️ **ATTENTION**: Commande destructive - confirmation requise

**Utilisation**:
```
Shift+P → /new-phase
```

**Processus de sécurité** (4 étapes) :

**Étape 1 - VÉRIFICATION**:
```
ARCHIVER Phase 5 (updated 2 Nov 2025, 25 items)?
✅ Fait: 12 items
🔧 En cours: 8 items
🧪 À tester: 3 items
🚀 Prochaines étapes: 2 items
```

**Étape 2 - CONFIRMATION REQUISE**:
```
Confirmer: OUI / NON
→ Attends réponse "OUI" (MAJUSCULES)
```

**Étape 3 - BACKUP + ARCHIVE** (si OUI) :
```
✅ Backup créé: .claude/compact_current.backup-phase5-02nov2025
✅ Phase 5 archivée dans: .claude/compact_master.md
✅ Nouvelle Phase 6 créée
```

**Étape 4 - RÉSULTAT**:
```
✅ Phase 5 archivée, Phase 6 créée
📄 compact_current.md réinitialisé avec structure:
   - 🎯 Objectifs [vierge]
   - ✅ Fait [vierge]
   - 🔧 En cours [vierge]
   - 🧪 À tester [vierge]
   - 🚀 Prochaines étapes [vierge]
```

---

### 4️⃣ `/sync-plan` 🔄

**Priorité**: MEDIUM
**Fréquence**: Hebdomadairement

**Description**: Valide cohérence entre `compact_master.md` et `compact_current.md`

**Utilisation**:
```
Shift+P → /sync-plan
```

**Validations effectuées**:

✓ **Phase Completes** - Toutes phases 1-6 documentées?
✓ **Cohérence Phase Actuelle** - current = master?
✓ **Chronologie** - Pas de dates en désordre?
✓ **Intégrité Données** - Pas de TODO orphelins?
✓ **Structure** - QUICK REFERENCE à jour? CHANGELOG synchronisé?

**Résultat si OK**:
```
✅ Compact files synchronisés
   - 6/6 phases présentes
   - Phase 5 actuelle cohérente
   - Dates : 1 Nov → 2 Nov ✓
   - Pas de TODO orphelins
   - QUICK REFERENCE à jour
   - CHANGELOG synchronisé
```

**Résultat si problème**:
```
⚠️ Divergence détectée:
   Problème: Phase 5 dans current, Phase 4 archivée dans master (date: 30 Oct)
   Cause: Oubli archivage automatique
   Solution proposée: Archiver Phase 5 maintenant avec /new-phase
```

---

### 5️⃣ `/commit-phase` 💾

**Priorité**: HIGH
**Fréquence**: À la fin de chaque session importante

**Description**: Crée commit Git et synchronise `compact_current.md` avec message

**Utilisation**:
```
Shift+P → /commit-phase
```

**Processus** (6 étapes) :

**Étape 1 - GIT STATUS**:
```
Modified files:
  - frontend/src/pages/MesNiches.tsx
  - frontend/src/pages/NicheDiscovery.tsx
  - backend/app/api/v1/routers/products.py

3 files modified, 0 files added
```

**Étape 2 - PROPOSITION MESSAGE**:
```
Message proposé:
  "feat(phase-5-day1): MesNiches UI + Netlify deploy integration"

  - Updated MesNiches page with /api/v1/niches/discover integration
  - Configured Netlify deployment pipeline
  - Updated NicheDiscovery with real API calls
```

**Étape 3 - CONFIRMATION**:
```
Accepter ce message? OUI / Proposer différent
→ OUI
```

**Étape 4 - COMMIT CRÉÉ**:
```
✅ Commit a1b2c3d créé
   "feat(phase-5-day1): MesNiches UI + Netlify deploy"
```

**Étape 5 - SYNC MEMORY**:
```
✅ compact_current.md mis à jour:
   - CHANGELOG: "- 14:35 | Commit a1b2c3d - feat(phase-5-day1)"
   - QUICK REFERENCE: Dernière update = "2 Nov 2025 14:35"
```

**Étape 6 - CONFIRMATION FINALE**:
```
Recent commits:
  a1b2c3d - feat(phase-5-day1): MesNiches UI + Netlify deploy
  093692e - fix(phase4): Windows compatibility + niche discovery
  35258d8 - feat(budget): Phase 4.5 - Keepa API Budget Protection

✅ Memory synchronisée, commit prêt pour push
```

---

## ⌨️ Raccourcis Clavier (Optionnel)

Si tu veux utiliser des raccourcis plus courts :

```
lc  → /load-context
uc  → /update-compact
np  → /new-phase
sp  → /sync-plan
cp  → /commit-phase
```

**Utilisation**:
```
Shift+P → lc
[Charge context 10 sec plus tard]
```

---

## 🔄 Workflow Recommandé (Phase 5-6)

### Démarrage de Session

```
1. Shift+P → /load-context
   (restaure état du projet en 10 sec)

2. Commence travail sur Phase 5
```

### Pendant la Session

```
- /update-compact chaque 2-3h si gros changements
- Développe et teste normalement
```

### Fin de Session

```
1. /update-compact
   (propose mises à jour contexte)

2. /commit-phase
   (sauvegarde Git + sync mémoire)

3. Fin session
   (contexte prêt pour session suivante)
```

### Changement de Phase

```
1. /update-compact
   (finalize Phase 5 context)

2. /commit-phase
   (commit final Phase 5)

3. /new-phase
   (archive Phase 5, crée Phase 6)

4. /sync-plan
   (valide cohérence)

5. Début Phase 6
```

---

## 🔍 Configuration (`.claude/slash-commands.json`)

Le fichier `.claude/slash-commands.json` contient :

```json
{
  "version": "1.0",
  "commands": [
    {
      "name": "load-context",
      "description": "...",
      "priority": "high",
      "prompt": "..."
    },
    ...
  ],
  "config": {
    "backup_enabled": true,
    "backup_location": ".claude/backups/",
    "validation_required": ["new-phase"],
    "require_confirmation": ["new-phase", "commit-phase"],
    "max_retries": 3
  }
}
```

---

## 📋 Fichiers Créés

| Fichier | Purpose |
|---------|---------|
| `.claude/slash-commands.json` | Configuration des 5 commandes |
| `.claude/SLASH_COMMANDS_GUIDE.md` | Ce guide (référence) |
| `.claude/compact_master.md` | Mémoire permanente du projet |
| `.claude/compact_current.md` | Mémoire phase active |
| `.claude/backups/` | Backups automatiques (si création) |

---

## ✅ Checklist Installation

- [x] `.claude/slash-commands.json` créé
- [x] 5 commandes configurées
- [x] Guide complet écrit
- [ ] Première utilisation : `/load-context`
- [ ] Validation workflow par utilisateur

---

## 🆘 Troubleshooting

### Problème: `/load-context` ne trouve pas le fichier

**Solution**:
```
1. Vérifier : .claude/compact_current.md existe?
2. Vérifier chemin: .claude/ au root du projet
3. Réessayer: Shift+P → /load-context
```

### Problème: `/new-phase` demande 2x confirmation

**Expected behavior** :
- Étape 1: Affiche résumé
- Étape 2: Demande "Confirmer: OUI / NON"
- Tu dois répondre "OUI" (majuscules)
- C'est normal, c'est le mécanisme de sécurité

### Problème: `/update-compact` propose changements bizarres

**Solution**:
```
1. Rejette le changement ("NON")
2. Dis-moi manuellement quoi updater
3. Je proposerai de nouveau
```

---

## 📞 Questions?

- **Comment utiliser une commande?** → Voir section correspondante
- **Erreur lors de commande?** → Voir Troubleshooting
- **Suggestion nouvelle commande?** → Dis-moi, on ajoute à `.claude/slash-commands.json`

---

**Dernière mise à jour**: 2 Novembre 2025 23:45
**Créé par**: Claude Code + Aziz
**Status**: ✅ Production-Ready
