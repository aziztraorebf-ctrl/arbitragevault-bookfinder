# ArbitrageVault BookFinder - Context Management System

Systeme de gestion de contexte automatique pour ArbitrageVault BookFinder.

---

## Structure `.claude/` Folder

```
.claude/
├── README.md                          <- Vous etes ici
├── compact_master.md                  <- Memoire permanente globale du projet
├── compact_current.md                 <- Memoire active de la phase courante
├── SLASH_COMMANDS_GUIDE.md            <- Guide complet des commandes
├── STRUCTURE.md                       <- Architecture du systeme
├── SYSTEM_SUMMARY.md                  <- Resume du systeme
├── CODE_STYLE_RULES.md                <- Regles de style de code
├── commands/                          <- Slash commands definitions
│   ├── load-context.md
│   ├── update-compact.md
│   ├── new-phase.md
│   ├── sync-plan.md
│   └── commit-phase.md
├── memory/                            <- Fichiers memoire additionnels
├── archives/                          <- Archives des phases completees
├── skills/                            <- Skills (Playwright, etc.)
└── settings.local.json                <- Permissions VS Code Claude Code
```

---

## Statut Projet - Decembre 2025

### Phases Completees
- Phase 1-4: Foundation, Database, Keepa, Business Logic
- Phase 5: Token Control Safeguards
- Phase 6: Frontend E2E Tests
- Phase 7: AutoSourcing Production

### Production URLs
- **Backend**: https://arbitragevault-backend-v2.onrender.com
- **Frontend**: https://arbitragevault.netlify.app

### Tests
- 483 tests passants (349+ unit + 56 E2E)

---

## 5 Commandes Slash Disponibles

| Commande | Usage | Frequence |
|----------|-------|-----------|
| `/load-context` | Charge contexte du projet | A chaque session |
| `/update-compact` | Propose mises a jour contexte | Apres taches |
| `/new-phase` | Archive phase + cree nouvelle | Fin de phase |
| `/sync-plan` | Valide coherence fichiers | Hebdomadaire |
| `/commit-phase` | Git commit + sync memory | Fin de session |

**Guide detaille**: Voir [SLASH_COMMANDS_GUIDE.md](./SLASH_COMMANDS_GUIDE.md)

---

## Workflow Recommande

### Debut de Session
```
1. /load-context           (restaure etat)
2. Lire QUICK REFERENCE    (comprendre phase actuelle)
3. Commencer travail
```

### Fin de Session
```
1. /update-compact         (propose changements)
2. /commit-phase           (sauvegarde Git + memory)
```

### Fin de Phase
```
1. /update-compact         (finalize phase)
2. /commit-phase           (commit final)
3. /new-phase              (archive + cree nouvelle)
```

---

## Fichiers Memoire

### `compact_master.md` (Permanent)
- Historique complet du projet (phases 1-7, decisions, lecons)
- Edite automatiquement via `/new-phase`

### `compact_current.md` (Actif)
- Etat actuel de la phase en cours
- Edite via `/update-compact` ou manuellement

---

## Documentation

- [SLASH_COMMANDS_GUIDE.md](./SLASH_COMMANDS_GUIDE.md) - Guide des commandes
- [STRUCTURE.md](./STRUCTURE.md) - Architecture technique
- [CODE_STYLE_RULES.md](./CODE_STYLE_RULES.md) - Regles de code

---

**Derniere mise a jour**: Decembre 2025
**Status**: Production Ready - Phases 1-7 Completes
