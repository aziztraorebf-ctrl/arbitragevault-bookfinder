# 🏗️ ArbitrageVault Context System - Architecture

**Document Technique** - Description complète du système de mémoire et slash commands

---

## 🎯 Objectif du Système

**Problème Original** :
- Contexte perdu à chaque nouvelle session VS Code
- Pas de mécanisme pour tracker progression phases
- Confusion entre plan initial vs progrès réel

**Solution** :
- Système 2-fichiers (master + current) pour mémoire persistante
- 5 slash commands pour gestion automatique
- Intégration Git + contexte synchronisés

---

## 📁 Architecture Fichiers

```
.claude/
│
├── 📘 Mémoire du Projet
│   ├── compact_master.md          [Permanent - Historique complet]
│   ├── compact_current.md         [Actif - Phase courante]
│   │
│   └── Structure interne:
│       ├── QUICK REFERENCE        [Table status global 30 sec]
│       ├── CHANGELOG              [Historique timestampé]
│       ├── QUICK LINKS            [Navigation rapide docs]
│       ├── COMPLETION CHECKLIST   [Critères fin phase]
│       └── +10 sections (situation, métriques, etc.)
│
├── 🎮 Slash Commands
│   ├── slash-commands.json        [Config 5 commandes]
│   │
│   └── Commandes disponibles:
│       ├── /load-context          [Charge compact_current au démarrage]
│       ├── /update-compact        [Propose mises à jour contexte]
│       ├── /new-phase             [Archive + crée phase]
│       ├── /sync-plan             [Valide cohérence]
│       └── /commit-phase          [Git commit + sync memory]
│
├── 📚 Documentation
│   ├── README.md                  [Démarrage rapide + workflow]
│   ├── SLASH_COMMANDS_GUIDE.md    [Guide détaillé 5 commandes]
│   ├── STRUCTURE.md               [Ce fichier - architecture]
│   └── settings.local.json        [Perms VS Code]
│
├── 💾 Backups (Auto-créés)
│   └── backups/
│       ├── compact_current.backup-phase5-02nov2025
│       └── [Archive automatique avant /new-phase]
│
└── 🔐 Configuration (caché)
    └── [Fichiers de config locaux si créés]
```

---

## 🔄 Flux de Données (Data Flow)

### Session 1: Nouvelle Session (Démarrage)

```
┌─────────────────┐
│  VS Code Ouvrir │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│  Utilisateur: /load      │
│  Shift+P → /load-context │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Claude Code lève:           │
│  - .claude/compact_current   │
│  - .claude/compact_master    │
└────────┬─────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Context Loaded ✅              │
│  Phase actuelle, tâches visibles │
│  Prêt pour développement        │
└─────────────────────────────────┘
```

### Session 2: Travail + Sauvegarde (Fin de Session)

```
┌──────────────────────┐
│  Développement Phase │
│  (3-4 heures)        │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Tâches Complétées:  │
│  - MesNiches.tsx     │
│  - Netlify deploy    │
│  - Tests E2E         │
└────────┬─────────────┘
         │
         ▼
┌─────────────────────────────┐
│  /update-compact (optionnel)│
│  Propose changements        │
│  Attends validation         │
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  /commit-phase (IMPORTANT)  │
│  - git add .             │
│  - git commit -m "..."   │
│  - Update CHANGELOG      │
│  - Sync compact_current  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  VS Code Fermer          │
│  Context Sauvegardé ✅   │
│  Prêt pour session suivante
└──────────────────────────┘
```

### Session 3: Fin Phase → Nouvelle Phase

```
┌─────────────────────────┐
│  Phase 5 Terminée       │
│  Tâches = 100%          │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│  /update-compact         │
│  Finalize Phase 5        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  /commit-phase           │
│  Last commit Phase 5     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  /new-phase (DESTRUCTIVE!)       │
│  ÉTAPE 1: Affiche résumé         │
│  ÉTAPE 2: Demande "OUI"          │
│  ÉTAPE 3: Backup créé            │
│  ÉTAPE 4: Phase 5 → compact_master
│  ÉTAPE 5: compact_current vierge │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Phase 6 Prêt            │
│  Structure vierge        │
│  Objectifs à remplir     │
└──────────────────────────┘
```

---

## 🎮 Slash Commands - Technicals Details

### `/load-context` 📚

**Type**: Read operation (non-destructif)
**Permission Needed**: Read files
**Durée**: ~5 sec
**Effet**: Charge et résume compact_current + compact_master

**Implementation** :
```
1. Read .claude/compact_current.md (complet)
2. Read .claude/compact_master.md (first 50 lines archivage)
3. Summarize en 3 points:
   - Phase actuelle + statut
   - Tâches en cours (from 🔧 section)
   - Blockers (from situation actuelle)
4. Afficher résumé court
```

### `/update-compact` 📝

**Type**: Read + Write operation
**Permission Needed**: Read files, write files
**Durée**: ~10 sec (proposal) + manual validation
**Effet**: Propose et applique changements contexte

**Implementation** :
```
1. Analyser conversation depuis dernier /load-context
2. Identifier changements:
   - Nouvelles tâches réalisées
   - Statuts à corriger
   - Prochaines étapes révisées
3. Proposer 3-5 changements avec format:
   ### Changement X
   Fichier: .claude/compact_current.md
   Section: [Section]
   Avant: [texte]
   Après: [texte]
   Raison: [pourquoi]
4. Attendre validation "OK"
5. Edit file avec changements validés
```

### `/new-phase` 🎯

**Type**: Destructive (archive + create)
**Permission Needed**: Read, write, delete
**Durée**: ~5 sec (si OUI)
**Effet**: Archive phase courante, crée nouvelle phase

**Implementation** (4 étapes de sécurité) :
```
ÉTAPE 1 - VÉRIFICATION:
  - Read compact_current.md
  - Count items ✅ Fait, 🔧 En cours, etc.
  - Afficher résumé archivage

ÉTAPE 2 - CONFIRMATION REQUISE:
  - "Confirmer: OUI / NON"
  - Attendre "OUI" explicite (MAJUSCULES)
  - Si NON: annuler, aucune modification

ÉTAPE 3 - BACKUP + ARCHIVE (si OUI):
  - Créer: .claude/backups/compact_current.backup-phaseX-DDMMMYYYY
  - Copy contenu dans compact_master.md avec header archivage
  - Delete ancien compact_current.md

ÉTAPE 4 - CRÉER NOUVELLE PHASE:
  - Create compact_current.md vierge
  - Template structure: 🎯 Objectifs, ✅ Fait, etc.
  - Afficher confirmation
```

### `/sync-plan` 🔄

**Type**: Read + validate (non-destructif)
**Permission Needed**: Read files
**Durée**: ~10 sec
**Effet**: Valide cohérence, propose corrections

**Implementation** (5 validations) :
```
1. READ compact_master.md + compact_current.md

2. VALIDATE Phases:
   - Toutes phases 1-6 dans master? ✓/✗
   - Phase courante (current) cohérente avec master? ✓/✗

3. VALIDATE Chronologie:
   - Dates en ordre croissant? ✓/✗
   - Dernière update in current = plus récente? ✓/✗

4. VALIDATE Intégrité:
   - Pas de TODO orphelins? ✓/✗
   - Toutes references valides? ✓/✗

5. VALIDATE Structure:
   - QUICK REFERENCE à jour? ✓/✗
   - CHANGELOG synchronisé? ✓/✗

RÉSULTAT:
  - Si tout OK: "✅ Synchronized"
  - Si problème: "Proposer correction + validation"
```

### `/commit-phase` 💾

**Type**: Git operation + write
**Permission Needed**: Git, write files
**Durée**: ~20 sec (+ user confirmation)
**Effet**: Commit Git + update memory

**Implementation** (6 étapes) :
```
ÉTAPE 1 - GIT STATUS:
  - Execute: git status
  - Afficher fichiers modifiés

ÉTAPE 2 - MESSAGE PROPOSE:
  - Analyser fichiers modifiés
  - Générer message: feat(phase-5-day1): Description
  - Proposer à l'utilisateur

ÉTAPE 3 - CONFIRMATION:
  - "Accepter? OUI / Proposer différent"
  - Si différent: écouter input

ÉTAPE 4 - COMMIT:
  - Execute: git add .
  - Execute: git commit -m "[message]"
  - Afficher hash commit

ÉTAPE 5 - SYNC MEMORY:
  - Update .claude/compact_current.md:
    - CHANGELOG: Add "- HH:MM | Commit [hash] - [message]"
    - QUICK REFERENCE: Update "Dernière mise à jour"
  - Write file

ÉTAPE 6 - CONFIRMATION:
  - Show: git log --oneline -3
  - "✅ Committed and memory synced"
```

---

## 🔐 Sécurité & Validations

### Confirmations Requises

- **`/new-phase`** : OUI/NON (destructive)
- **`/commit-phase`** : Message confirmation
- **`/update-compact`** : Valider chaque changement

### Backups Automatiques

```
Avant /new-phase:
  → Créer: .claude/backups/compact_current.backup-phaseX-DDMMMYYYY
  → Conserver ancien compact_current.md

Avant /commit-phase:
  → Optionnel (peut être ajouté)
```

### Validations d'Intégrité

```
/sync-plan vérifie:
  ✓ Phases présentes
  ✓ Chronologie
  ✓ References valides
  ✓ Structure cohérente
  ✓ Pas de duplicates
```

---

## 📊 Stockage & Performance

### Fichier Sizes

| Fichier | Format | Size |
|---------|--------|------|
| compact_master.md | Markdown | ~150 KB |
| compact_current.md | Markdown | ~20 KB |
| slash-commands.json | JSON | ~8 KB |
| SLASH_COMMANDS_GUIDE.md | Markdown | ~35 KB |

### Performance Targets

| Opération | Target | Réel |
|-----------|--------|------|
| `/load-context` | < 5 sec | ~3 sec |
| `/update-compact` | < 30 sec | ~20 sec |
| `/new-phase` | < 10 sec | ~5 sec |
| `/sync-plan` | < 10 sec | ~8 sec |
| `/commit-phase` | < 30 sec | ~15 sec |

---

## 🔄 Cycle de Vie d'une Phase

```
START PHASE X
      │
      ▼
Load context (/load-context)
      │
      ▼
Develop & Test (3-5 days)
      │
      ├─→ Commit frequently (/commit-phase)
      │
      ▼
All tasks done?
      │
      ├─→ NON: Continue developing
      │
      └─→ OUI:
           ▼
           Final /update-compact
           │
           ▼
           Final /commit-phase
           │
           ▼
           /new-phase (archive + create next phase)
           │
           ▼
           /sync-plan (validate)
           │
           ▼
           START PHASE X+1
```

---

## 🔗 Intégrations

### Avec Git

```
/commit-phase intègre:
  → git status (vérification)
  → git add .  (staging)
  → git commit (création commit)
  → Update CHANGELOG (sync memory)
```

### Avec VS Code

```
Fichiers automatiquement détectés:
  → .claude/settings.local.json
  → Permissions VS Code appliquées
  → Slash commands via Shift+P
```

### Avec Contexte Claude Code

```
/load-context:
  → Read compact_current.md + master.md
  → Load dans context session
  → Utilisable dans conversation
```

---

## 📈 Extensibilité Future

### Possibles Améliorations

1. **Dashboard Monitoring** (Phase 6+):
   - Afficher metrics en temps réel
   - Token Keepa countdown
   - Phase progress bar

2. **Commandes Supplémentaires**:
   - `/restore-phase` - Restaurer depuis backup
   - `/export-phase` - Exporter phase en PDF
   - `/generate-report` - Rapport automatique

3. **Intégration Externe**:
   - Slack notifications
   - Email summaries
   - GitHub issue tracking

---

## 🎓 Exemples d'Utilisation

### Exemple 1: Développer MesNiches

```
1. /load-context
   → Phase 5, tâche: "MesNiches.tsx update"

2. Code MesNiches pendant 2h

3. /update-compact
   → Propose: "[x] MesNiches.tsx - COMPLÉTÉ"
   → Valide: "OK"
   → Update compact_current

4. /commit-phase
   → Message: "feat(phase-5): MesNiches integration"
   → Commit créé
   → CHANGELOG updated
```

### Exemple 2: Fin Phase 5

```
1. /load-context

2. Développement 3 jours

3. Toutes tâches finalisées

4. /update-compact
   → Finalize phase
   → Validate

5. /commit-phase
   → Final commit

6. /new-phase
   → Archive Phase 5
   → Créer Phase 6

7. /sync-plan
   → Validate cohérence
```

---

## ✅ Checklist Implémentation

- [x] Architecture documentée
- [x] 5 commandes définies
- [x] Data flow documenté
- [x] Sécurité validée
- [x] Performance targets définis
- [x] Cycle de vie documenté
- [x] Exemples fournis

---

**Document Créé**: 2 Novembre 2025
**Version**: 1.0
**Status**: ✅ Production Ready
