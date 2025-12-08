# ArbitrageVault Context System - Architecture

Technical documentation for the context management system.

---

## System Purpose

**Problem Solved**:
- Context lost between VS Code sessions
- No mechanism to track phase progression
- Confusion between initial plan vs actual progress

**Solution**:
- 2-file system (master + current) for persistent memory
- 5 slash commands for automatic management
- Git + context synchronization

---

## File Architecture

```
.claude/
│
├── Memory Files
│   ├── compact_master.md          [Permanent - Complete history]
│   └── compact_current.md         [Active - Current phase]
│
├── Slash Commands
│   ├── commands/load-context.md
│   ├── commands/update-compact.md
│   ├── commands/new-phase.md
│   ├── commands/sync-plan.md
│   └── commands/commit-phase.md
│
├── Documentation
│   ├── README.md                  [Quick start + workflow]
│   ├── SLASH_COMMANDS_GUIDE.md    [Detailed commands guide]
│   ├── STRUCTURE.md               [This file - architecture]
│   ├── SYSTEM_SUMMARY.md          [System overview]
│   └── CODE_STYLE_RULES.md        [Code style rules]
│
├── Archives
│   └── archives/                  [Completed phases]
│
├── Skills
│   └── skills/playwright-skill/   [Playwright automation]
│
└── Config
    └── settings.local.json        [VS Code permissions]
```

---

## Data Flow

### Session Start
```
VS Code Open
      |
      v
User: /load-context
      |
      v
Claude Code reads:
  - .claude/compact_current.md
  - .claude/compact_master.md
      |
      v
Context Loaded - Ready to work
```

### Session End
```
Development Complete
      |
      v
/update-compact (optional)
  -> Proposes changes
  -> User validates
      |
      v
/commit-phase
  -> git add .
  -> git commit
  -> Update CHANGELOG
      |
      v
Context Saved
```

### Phase Transition
```
Phase X Complete
      |
      v
/update-compact -> Finalize
      |
      v
/commit-phase -> Final commit
      |
      v
/new-phase
  -> Backup created
  -> Phase X -> compact_master
  -> New compact_current
      |
      v
Phase X+1 Ready
```

---

## Slash Commands Details

### `/load-context`
- **Type**: Read-only
- **Duration**: ~3-5 sec
- **Effect**: Loads compact_current + compact_master

### `/update-compact`
- **Type**: Read + Write
- **Duration**: ~10 sec + validation
- **Effect**: Proposes and applies context updates

### `/new-phase`
- **Type**: Destructive (archive + create)
- **Duration**: ~5 sec
- **Effect**: Archives current phase, creates new one
- **Safety**: Backup auto-created, confirmation required

### `/sync-plan`
- **Type**: Read-only validation
- **Duration**: ~8-10 sec
- **Effect**: Validates coherence between files

### `/commit-phase`
- **Type**: Git + Write
- **Duration**: ~15-20 sec
- **Effect**: Git commit + memory sync

---

## Security & Validations

### Required Confirmations
- `/new-phase`: YES/NO (destructive)
- `/commit-phase`: Message confirmation
- `/update-compact`: Validate each change

### Automatic Backups
- Before `/new-phase`: Creates backup in `.claude/archives/`

---

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| `/load-context` | < 5 sec | ~3 sec |
| `/update-compact` | < 30 sec | ~20 sec |
| `/new-phase` | < 10 sec | ~5 sec |
| `/sync-plan` | < 10 sec | ~8 sec |
| `/commit-phase` | < 30 sec | ~15 sec |

---

## Project Status

### Completed Phases
- Phase 1-4: Foundation, Database, Keepa, Business Logic
- Phase 5: Token Control Safeguards
- Phase 6: Frontend E2E Tests
- Phase 7: AutoSourcing Production

### Production
- Backend: https://arbitragevault-backend-v2.onrender.com
- Frontend: https://arbitragevault.netlify.app
- Tests: 483 passing (349+ unit + 56 E2E)

---

**Version**: 2.0
**Last Updated**: December 2025
**Status**: Production Ready
