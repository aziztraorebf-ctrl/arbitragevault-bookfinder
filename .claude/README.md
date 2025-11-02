# 🎯 ArbitrageVault BookFinder - Context Management System

Bienvenue dans le système de gestion de contexte automatique pour ArbitrageVault BookFinder.

---

## 📁 Structure `.claude/` Folder

```
.claude/
├── README.md                          ← Vous êtes ici
├── compact_master.md                  ← Mémoire permanente globale du projet
├── compact_current.md                 ← Mémoire active de la phase courante
├── slash-commands.json                ← Configuration 5 commandes slash
├── SLASH_COMMANDS_GUIDE.md            ← Guide complet des commandes
├── settings.local.json                ← Permissions VS Code Claude Code
└── backups/                           ← Sauvegardes automatiques des phases
    └── compact_current.backup-phase5-02nov2025
```

---

## 🚀 Démarrage Rapide

### Session 1 (Première Utilisation)

1. **Ouvrir VS Code** avec le projet ArbitrageVault

2. **Charger le contexte**:
   ```
   Shift+P → /load-context
   ```

   Résultat: Contexte du projet chargé (Phase 5, tâches, blockers)

3. **Commencer à travailler** sur les tâches listées

### Session N (Sessions Suivantes)

1. **Nouveau démarrage** → Contexte vierge (par défaut VS Code)

2. **Charger contexte** (important!):
   ```
   Shift+P → /load-context
   ```

3. **Travailler** normalement

4. **Avant de quitter** → Sauvegarder:
   ```
   Shift+P → /commit-phase
   ```

---

## 🎯 5 Commandes Slash Disponibles

| Commande | Usage | Fréquence |
|----------|-------|-----------|
| **`/load-context`** | Charge contexte du projet | À chaque session |
| **`/update-compact`** | Propose mises à jour contexte | Après tâches |
| **`/new-phase`** | Archive phase + crée nouvelle | Fin de phase |
| **`/sync-plan`** | Valide cohérence fichiers | Hebdomadaire |
| **`/commit-phase`** | Git commit + sync memory | Fin de session |

**Guide détaillé** : Voir [SLASH_COMMANDS_GUIDE.md](./SLASH_COMMANDS_GUIDE.md)

---

## 📚 Fichiers Mémoire

### 1️⃣ `compact_master.md` (Permanent)

**Contient** : Historique complet du projet (phases 1-6, décisions, leçons)

**Quand éditer** :
- Rarement (automatiquement via `/new-phase`)
- À la fin de chaque phase majeure pour archivage

**Backup** : Pas de backup (historique permanent)

### 2️⃣ `compact_current.md` (Actif)

**Contient** : État actuel de la phase en cours (Phase 5 maintenant)

**Quand éditer** :
- Fréquemment (via `/update-compact`)
- Après chaque session importante

**Backup** : Automatique avant `/new-phase`

---

## 🔄 Workflow Recommandé

### Début de Phase

```
1. /load-context           (restaure état)
2. Lire QUICK REFERENCE    (comprendre phase actuelle)
3. Consulter 🚀 Prochaines étapes
4. Commencer travail
```

### Pendant la Phase

```
- Développer, tester normalement
- Si gros changement → /update-compact (optionnel)
- Continuer travail
```

### Fin de Session

```
1. /update-compact         (propose changements)
2. Valider changements
3. /commit-phase           (sauvegarde Git + memory)
4. Quitter
```

### Fin de Phase

```
1. /update-compact         (finalize phase)
2. /commit-phase           (commit final)
3. /new-phase              (archive + crée nouvelle)
4. /sync-plan              (valide cohérence)
5. Commencer Phase X+1
```

---

## 📋 Sections de `compact_current.md`

Quand tu ouvres `compact_current.md`, tu trouveras:

| Section | Usage |
|---------|-------|
| **QUICK REFERENCE** | Vue globale (30 sec à lire) |
| **Pages À Mettre À Jour** | Checklist UI pour Phase 5 |
| **Endpoints À Tester** | API production à valider |
| **CHANGELOG** | Historique du jour |
| **QUICK LINKS** | Docs pertinentes |
| **Situation Actuelle** | État système complet |
| **COMPLETION CHECKLIST** | Critères fin de phase |

---

## 💡 Bonnes Pratiques

✅ **À FAIRE**:
- Utiliser `/load-context` au démarrage de chaque session
- Utiliser `/update-compact` quand tu finis une tâche importante
- Utiliser `/commit-phase` avant de quitter
- Lire QUICK REFERENCE pour comprendre l'état (1 min max)

❌ **À NE PAS FAIRE**:
- Éditer directement `compact_master.md` (archive seulement)
- Éditer `compact_current.md` manuellement (utiliser `/update-compact`)
- Oublier `/load-context` au démarrage
- Quitter sans `/commit-phase` si travail important

---

## 🔍 Fichiers de Configuration

### `slash-commands.json`

**Contient** : Définition des 5 slash commands avec prompts détaillés

**Format** :
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
    "validation_required": ["new-phase"],
    ...
  }
}
```

**À modifier** : Rarement (sauf pour ajouter nouvelles commandes)

### `settings.local.json`

**Contient** : Permissions VS Code pour Claude Code

**À modifier** : Si tu veux ajouter permissions supplémentaires (git, bash, etc.)

---

## 📊 Tailles Fichiers (Référence)

| Fichier | Taille | Lignes |
|---------|--------|--------|
| `compact_master.md` | ~150 KB | 1500+ |
| `compact_current.md` | ~20 KB | 450+ |
| `slash-commands.json` | ~8 KB | 200+ |
| `SLASH_COMMANDS_GUIDE.md` | ~35 KB | 500+ |
| **Total** | ~213 KB | 2650+ |

---

## ❓ Questions Fréquentes

### Q: Je dois charger le contexte manuellement?
**R**: Oui, avec `/load-context` au démarrage. C'est un peu plus rapide que d'être automatique.

### Q: Que faire si je perds le contexte?
**R**: Ne t'inquiète pas - `/load-context` le recharge. Pas de données perdues.

### Q: Puis-je éditer `compact_current.md` manuellement?
**R**: Techniquement oui, mais préfère `/update-compact` pour cohérence.

### Q: Où sont les backups des phases?
**R**: `.claude/backups/` - Créés automatiquement avant `/new-phase`.

### Q: Que se passe si je fais `/new-phase` par erreur?
**R**: Pas de souci! Backup créé automatiquement avant suppression. Tu peux restaurer.

---

## 🎓 Guides Détaillés

- **Utilisation slash commands** : [SLASH_COMMANDS_GUIDE.md](./SLASH_COMMANDS_GUIDE.md)
- **Historique projet complet** : [compact_master.md](./compact_master.md)
- **État phase actuelle** : [compact_current.md](./compact_current.md)

---

## 📞 Support

Si quelque chose ne marche pas:

1. **Vérifier fichiers existent** : `.claude/compact_current.md` + `.claude/compact_master.md`
2. **Relancer `/load-context`**
3. **Consulter SLASH_COMMANDS_GUIDE.md** section Troubleshooting
4. **Demander aide** en expliquant le problème

---

## ✅ Checklist Installation

- [x] `.claude/` folder créé
- [x] `compact_master.md` créé (1500+ lignes, historique complet)
- [x] `compact_current.md` créé (450+ lignes, phase active)
- [x] `slash-commands.json` créé (5 commandes)
- [x] `SLASH_COMMANDS_GUIDE.md` créé (guide complet)
- [x] `settings.local.json` configuré
- [x] `README.md` créé (vous êtes ici)
- [ ] Première utilisation: `/load-context`

---

## 📈 Évolution Système

**Phase 5** (Actuellement):
- 5 slash commands
- 2 fichiers mémoire
- Backups automatiques avant archivage

**Phase 6** (Futur):
- Possibilité d'ajouter +2 commandes si besoin
- Intégration monitoring dashboard (optionnel)

---

**Créé**: 2 Novembre 2025
**Dernière mise à jour**: 2 Novembre 2025 23:50
**Status**: ✅ Production-Ready

🚀 **Prêt pour Phase 5 - Frontend MVP!**
