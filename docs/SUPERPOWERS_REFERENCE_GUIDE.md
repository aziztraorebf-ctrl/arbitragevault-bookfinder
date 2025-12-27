# Superpowers Skills - Reference Guide

Version 3.6.2 | Guide de reference pour la creation d'infographies

---

## Table des Matieres

1. [Vue d'ensemble](#vue-densemble)
2. [Diagramme des relations](#diagramme-des-relations)
3. [Tableau de synthese](#tableau-de-synthese)
4. [Categories de Skills](#categories-de-skills)
   - [Debugging](#categorie-debugging)
   - [Planning](#categorie-planning)
   - [Qualite](#categorie-qualite)
   - [Review](#categorie-review)
   - [Agents](#categorie-agents)
   - [Git/Workflow](#categorie-gitworkflow)
   - [Meta](#categorie-meta)

---

## Vue d'ensemble

Les Superpowers sont des protocoles de qualite structures qui guident le developpement logiciel. Chaque skill est un guide de reference pour des techniques eprouvees.

Principe fondamental : Si un skill existe pour une tache, son utilisation est obligatoire.

---

## Diagramme des Relations

```
                    [brainstorming]
                          |
                          v
                   [writing-plans]
                    /           \
                   v             v
    [subagent-driven-dev]    [executing-plans]
            |                      |
            v                      v
    [requesting-code-review] <-----+
            |
            v
    [receiving-code-review]
            |
            v
    [finishing-a-development-branch]
            |
            v
       [using-git-worktrees]


    Debugging Flow:
    [systematic-debugging] --> [root-cause-tracing] --> [defense-in-depth]
                                      |
                                      v
                          [test-driven-development]


    Quality Flow:
    [test-driven-development] --> [verification-before-completion]
            |
            v
    [testing-anti-patterns] --> [condition-based-waiting]
```

---

## Tableau de Synthese

| Skill | Categorie | Declencheur | Resultat |
|-------|-----------|-------------|----------|
| systematic-debugging | Debugging | Bug detecte | Cause racine identifiee |
| root-cause-tracing | Debugging | Erreur profonde dans le stack | Source du probleme trouvee |
| brainstorming | Planning | Nouvelle idee/feature | Design valide |
| writing-plans | Planning | Design approuve | Plan d'implementation |
| executing-plans | Planning | Plan existant | Taches executees par batch |
| test-driven-development | Qualite | Nouvelle feature/bugfix | Code teste |
| verification-before-completion | Qualite | Avant de dire "termine" | Preuves de completion |
| defense-in-depth | Qualite | Donnees externes | Validation multi-couches |
| condition-based-waiting | Qualite | Tests flaky/timing | Tests stables |
| testing-anti-patterns | Qualite | Ecriture de tests | Eviter les pieges |
| requesting-code-review | Review | Feature complete | Review structuree |
| receiving-code-review | Review | Feedback recu | Traitement technique |
| subagent-driven-development | Agents | Plan a executer | Execution avec sous-agents |
| dispatching-parallel-agents | Agents | 3+ problemes independants | Investigation parallele |
| using-git-worktrees | Git | Isolation requise | Workspace isole |
| finishing-a-development-branch | Git | Implementation terminee | Merge/PR/Cleanup |
| using-superpowers | Meta | Debut de session | Skills identifies |
| writing-skills | Meta | Creer un skill | Skill teste et documente |
| sharing-skills | Meta | Skill a partager | PR soumise |
| testing-skills-with-subagents | Meta | Tester un skill | Skill bulletproof |

---

## Categories de Skills

---

### CATEGORIE: DEBUGGING

---

#### 1. systematic-debugging

Description
Approche en 4 phases pour resoudre tout bug en trouvant la cause racine avant de proposer des fixes.

Quand utiliser
- Test failure
- Bug en production
- Comportement inattendu
- Probleme de performance
- Echec de build

Quand NE PAS utiliser
- Jamais de raison de sauter ce skill pour un bug

Workflow
1. PHASE 1 - Investigation : Lire erreurs, reproduire, verifier changements recents
2. PHASE 2 - Analyse de patterns : Trouver exemples fonctionnels, comparer
3. PHASE 3 - Hypothese : Former une theorie, tester minimalement
4. PHASE 4 - Implementation : Creer test failing, fixer, verifier

Exemple
Situation : API retourne 500 sporadiquement
Phase 1 : Lire logs, reproduire avec memes parametres
Phase 2 : Comparer requetes qui marchent vs echouent
Phase 3 : Hypothese "timeout sur DB quand payload > 1MB"
Phase 4 : Test qui envoie 2MB, fix du timeout, verification

Skills lies
- root-cause-tracing (pour erreurs profondes)
- test-driven-development (pour le test failing)
- defense-in-depth (apres fix)

---

#### 2. root-cause-tracing

Description
Technique de tracage arriere pour remonter du symptome a la source du probleme.

Quand utiliser
- Erreur apparait profondement dans le call stack
- Donnees invalides dont l'origine est inconnue
- Bug qui se manifeste loin de sa cause

Quand NE PAS utiliser
- Erreur simple avec cause evidente

Workflow
1. Observer le symptome
2. Trouver la cause immediate (quelle ligne de code)
3. Demander "Qu'est-ce qui a appele ceci?"
4. Continuer a remonter jusqu'a la source
5. Fixer a la source, pas au symptome

Exemple
Symptome : git init s'execute dans le mauvais dossier
Trace : git init <- WorktreeManager <- Session.create <- Test
Decouverte : projectDir est vide car accede avant beforeEach
Fix : Ajouter getter qui valide l'acces

Skills lies
- systematic-debugging (skill parent)
- defense-in-depth (ajouter validation a chaque couche)

---

### CATEGORIE: PLANNING

---

#### 3. brainstorming

Description
Transformer une idee brute en design valide via dialogue collaboratif et questions iteratives.

Quand utiliser
- Nouvelle feature a concevoir
- Idee vague a clarifier
- Avant d'ecrire du code
- Avant d'ecrire un plan

Quand NE PAS utiliser
- Tache mecanique avec instructions claires
- Correction de bug simple

Workflow
1. Comprendre le contexte projet (fichiers, docs, commits)
2. Poser des questions une par une (choix multiples preferes)
3. Proposer 2-3 approches avec trade-offs
4. Presenter le design par sections de 200-300 mots
5. Valider chaque section avant de continuer
6. Ecrire le design dans docs/plans/YYYY-MM-DD-topic-design.md

Exemple
Demande : "Ajouter un systeme de cache"
Questions : "Cache en memoire, Redis, ou fichiers?"
           "Quelle duree d'expiration?"
           "Quelles donnees cacher en priorite?"
Approches : A) Redis (scalable), B) In-memory (simple), C) Hybrid
Design : Sections architecture, composants, flux, tests

Skills lies
- writing-plans (etape suivante)
- using-git-worktrees (si implementation suit)

---

#### 4. writing-plans

Description
Creer des plans d'implementation detailles avec fichiers exacts, code complet, et etapes de verification.

Quand utiliser
- Design approuve pret a implementer
- Tache complexe necessitant structure
- Travail a deleguer a un autre agent/developpeur

Quand NE PAS utiliser
- Tache triviale de quelques minutes
- Design pas encore valide (brainstorming d'abord)

Workflow
1. Creer header avec goal, architecture, tech stack
2. Diviser en taches bite-sized (2-5 min chacune)
3. Pour chaque tache : fichiers exacts, code complet, commandes
4. Inclure etapes TDD : test failing -> implementation -> verification
5. Sauver dans docs/plans/YYYY-MM-DD-feature.md
6. Proposer execution : subagent-driven ou parallel session

Exemple
Task 1: Ajouter validation email
Files: src/validators/email.py, tests/test_email.py
Step 1: Ecrire test_invalid_email_rejected
Step 2: Run pytest - FAIL expected
Step 3: Implementer validate_email()
Step 4: Run pytest - PASS expected
Step 5: Commit

Skills lies
- brainstorming (etape precedente)
- executing-plans (execution en session parallele)
- subagent-driven-development (execution meme session)

---

#### 5. executing-plans

Description
Executer un plan existant par batches avec checkpoints de review entre chaque batch.

Quand utiliser
- Plan d'implementation fourni
- Execution en session separee
- Besoin de review entre les batches

Quand NE PAS utiliser
- Pas de plan existant (writing-plans d'abord)
- Execution dans la meme session (subagent-driven)

Workflow
1. Charger et reviewer le plan critiquement
2. Creer TodoWrite avec toutes les taches
3. Executer batch de 3 taches
4. Reporter et attendre feedback
5. Appliquer corrections si necessaire
6. Continuer jusqu'a completion
7. Utiliser finishing-a-development-branch

Exemple
Plan : 9 taches d'implementation API
Batch 1 : Taches 1-3 (models, schemas, routes basiques)
Report : "Batch 1 complete. 12 tests passent. Ready for feedback."
Feedback : "Ajouter validation sur champ X"
Fix : Ajouter validation
Batch 2 : Taches 4-6...

Skills lies
- writing-plans (cree le plan)
- finishing-a-development-branch (apres completion)

---

### CATEGORIE: QUALITE

---

#### 6. test-driven-development

Description
Ecrire le test d'abord, le regarder echouer, puis implementer le minimum pour le faire passer.

Quand utiliser
- Toute nouvelle feature
- Tout bugfix
- Tout refactoring
- Tout changement de comportement

Quand NE PAS utiliser
- Prototype jetable (avec permission explicite)
- Fichiers de configuration

Workflow
1. RED : Ecrire un test minimal qui decrit le comportement souhaite
2. Verify RED : Executer, confirmer qu'il echoue pour la bonne raison
3. GREEN : Ecrire le code minimal pour faire passer le test
4. Verify GREEN : Executer, confirmer que tout passe
5. REFACTOR : Nettoyer sans changer le comportement
6. Repeter pour le prochain test

Exemple
Feature : Fonction qui valide les emails
RED : test_rejects_empty_email() -> assert error == "Email required"
Run : FAIL - function not defined
GREEN : def validate(email): if not email: return "Email required"
Run : PASS
REFACTOR : Extraire constantes si necessaire

Skills lies
- verification-before-completion (apres implementation)
- testing-anti-patterns (eviter les pieges)

---

#### 7. verification-before-completion

Description
Executer les commandes de verification et confirmer les resultats AVANT toute affirmation de completion.

Quand utiliser
- Avant de dire "c'est fait", "termine", "fixe"
- Avant de commit ou creer une PR
- Avant de passer a la tache suivante
- Apres delegation a un agent

Quand NE PAS utiliser
- Jamais de raison de sauter cette verification

Workflow
1. IDENTIFIER : Quelle commande prouve cette affirmation?
2. EXECUTER : Lancer la commande complete
3. LIRE : Output complet, exit code, compter les failures
4. VERIFIER : L'output confirme-t-il l'affirmation?
5. SEULEMENT ALORS : Faire l'affirmation avec preuves

Exemple
Affirmation a faire : "Les tests passent"
Commande : pytest tests/ -v
Output : 42 passed, 0 failed
Verification : Exit code 0, 0 failures
Affirmation : "Tests passent (42/42, voir output ci-dessus)"

Interdictions
- "Should pass now" sans execution
- "Looks correct" sans verification
- "Fixed" sans test du symptome original
- Faire confiance aux reports d'agents sans verifier

Skills lies
- test-driven-development (verification du cycle)
- requesting-code-review (avant merge)

---

#### 8. defense-in-depth

Description
Valider les donnees a CHAQUE couche qu'elles traversent pour rendre les bugs structurellement impossibles.

Quand utiliser
- Donnees externes (APIs tierces, input utilisateur)
- Apres avoir fixe un bug cause par donnees invalides
- Systemes multi-couches

Quand NE PAS utiliser
- Donnees internes deja validees

Workflow
1. Tracer le flux de donnees (d'ou vient la valeur, ou va-t-elle)
2. Mapper tous les checkpoints
3. Ajouter validation a chaque couche :
   - Layer 1 : Entry point (rejet des inputs invalides)
   - Layer 2 : Business logic (sens metier)
   - Layer 3 : Environment guards (contexte specifique)
   - Layer 4 : Debug instrumentation (forensics)

Exemple
Bug : projectDir vide cause git init dans le mauvais dossier
Layer 1 : Project.create() valide que dir existe et n'est pas vide
Layer 2 : WorkspaceManager valide projectDir
Layer 3 : En test, refuser git init hors tmpdir
Layer 4 : Logger stack trace avant git init

Skills lies
- root-cause-tracing (trouver ou ajouter les validations)
- systematic-debugging (partie de Phase 4)

---

#### 9. condition-based-waiting

Description
Remplacer les timeouts arbitraires par du polling sur conditions reelles pour eliminer les tests flaky.

Quand utiliser
- Tests avec setTimeout/sleep arbitraires
- Tests flaky (passent parfois, echouent d'autres fois)
- Tests qui timeout en CI ou en parallele
- Attente d'operations async

Quand NE PAS utiliser
- Test du comportement de timing reel (debounce, throttle)
- Toujours documenter pourquoi si timeout necessaire

Workflow
1. Identifier les timeouts arbitraires dans les tests
2. Determiner la condition reelle attendue
3. Remplacer par waitFor(() => condition)
4. Inclure timeout max avec message d'erreur clair

Exemple
Avant (flaky) :
await sleep(100);
expect(result).toBeDefined();

Apres (stable) :
await waitFor(() => result !== undefined, "result should be defined");
expect(result).toBeDefined();

Pattern waitFor :
async function waitFor(condition, description, timeoutMs = 5000) {
  const start = Date.now();
  while (true) {
    if (condition()) return;
    if (Date.now() - start > timeoutMs) throw new Error(description);
    await sleep(10);
  }
}

Skills lies
- testing-anti-patterns (patterns a eviter)
- test-driven-development (tests stables)

---

#### 10. testing-anti-patterns

Description
Identifier et eviter les erreurs communes dans l'ecriture de tests qui reduisent leur valeur.

Quand utiliser
- Ecriture ou modification de tests
- Ajout de mocks
- Tentation d'ajouter methodes test-only en production

Quand NE PAS utiliser
- Code de production sans tests

Workflow
1. Verifier : Est-ce que je teste le comportement du mock?
2. Verifier : Est-ce que j'ajoute une methode uniquement pour les tests?
3. Verifier : Est-ce que je comprends les dependances avant de mocker?
4. Verifier : Mon mock est-il complet ou partiel?

Anti-patterns principaux
1. Tester le mock au lieu du code reel
   - Mauvais : expect(screen.getByTestId('sidebar-mock'))
   - Bon : Tester le vrai composant ou ne pas mocker

2. Methodes test-only en production
   - Mauvais : class Session { destroy() { /* only for tests */ } }
   - Bon : Mettre dans test-utils/

3. Mocker sans comprendre
   - Mauvais : Mock qui casse la logique du test
   - Bon : Comprendre les side effects avant de mocker

4. Mocks incomplets
   - Mauvais : { status: 'ok' } quand l'API retourne plus
   - Bon : Mock complet de la structure reelle

Skills lies
- test-driven-development (previent ces anti-patterns)
- condition-based-waiting (tests stables)

---

### CATEGORIE: REVIEW

---

#### 11. requesting-code-review

Description
Demander une review structuree via un sous-agent code-reviewer pour detecter les problemes avant qu'ils ne s'accumulent.

Quand utiliser
- Apres chaque tache en subagent-driven development
- Apres completion d'une feature majeure
- Avant merge sur main
- Quand bloque (perspective fraiche)

Quand NE PAS utiliser
- Changement trivial d'une ligne

Workflow
1. Obtenir les SHAs git (base et head)
2. Dispatcher sous-agent code-reviewer avec :
   - Ce qui a ete implemente
   - Plan ou requirements
   - SHA de base et de head
   - Description
3. Recevoir feedback : Strengths, Issues (Critical/Important/Minor)
4. Fixer issues Critical immediatement
5. Fixer issues Important avant de continuer
6. Noter issues Minor pour plus tard

Exemple
BASE_SHA=$(git rev-parse HEAD~3)
HEAD_SHA=$(git rev-parse HEAD)
Dispatch code-reviewer:
  WHAT: "Added user authentication endpoints"
  PLAN: "Task 5 from auth-implementation.md"
  BASE: abc123
  HEAD: def456

Feedback: "Important: Missing rate limiting on login"
Action: Ajouter rate limiting avant de continuer

Skills lies
- receiving-code-review (traiter le feedback)
- subagent-driven-development (review entre taches)
- finishing-a-development-branch (review finale)

---

#### 12. receiving-code-review

Description
Traiter le feedback de code review avec rigueur technique, pas d'accord performatif ou implementation aveugle.

Quand utiliser
- Reception de feedback de review
- Feedback semble flou ou techniquement questionnable
- Plusieurs items a traiter

Quand NE PAS utiliser
- Feedback clair et simple a implementer

Workflow
1. LIRE : Feedback complet sans reagir
2. COMPRENDRE : Reformuler en ses propres mots (ou demander)
3. VERIFIER : Checker contre la realite du codebase
4. EVALUER : Techniquement correct pour CE codebase?
5. REPONDRE : Acknowledgment technique ou pushback raisonne
6. IMPLEMENTER : Un item a la fois, tester chacun

Reponses interdites
- "You're absolutely right!"
- "Great point!"
- "Let me implement that now" (avant verification)

Reponses correctes
- "Fixed. Added validation on line 45."
- "Checked - this breaks existing feature X. Alternative?"
- "YAGNI - this endpoint is unused. Remove instead?"

Quand pushback
- Suggestion casse fonctionnalite existante
- Reviewer manque de contexte complet
- Viole YAGNI (feature inutilisee)
- Techniquement incorrect pour ce stack
- Conflits avec decisions architecturales

Skills lies
- requesting-code-review (etape precedente)
- verification-before-completion (avant d'implementer)

---

### CATEGORIE: AGENTS

---

#### 13. subagent-driven-development

Description
Executer un plan avec un sous-agent frais par tache et code review entre chaque tache.

Quand utiliser
- Plan a executer dans la session actuelle
- Taches majoritairement independantes
- Besoin de progres continu avec quality gates

Quand NE PAS utiliser
- Besoin de review du plan d'abord (executing-plans)
- Taches fortement couplees
- Plan necessite revision (brainstorming)

Workflow
1. Charger le plan, creer TodoWrite
2. Pour chaque tache :
   a. Dispatcher sous-agent d'implementation
   b. Recevoir rapport du sous-agent
   c. Dispatcher code-reviewer
   d. Fixer issues si necessaire
   e. Marquer complete, passer a suivante
3. Review finale de l'ensemble
4. Utiliser finishing-a-development-branch

Exemple
Plan : 5 taches d'implementation
Task 1 : Dispatcher agent "Implement user model"
Report : "Model created, 3 tests passing"
Review : "Minor: missing index on email"
Fix : Ajouter index
Task 2 : Dispatcher agent "Implement auth endpoints"...

Avantages vs execution manuelle
- Contexte frais par tache (pas de pollution)
- Review automatique entre taches
- Catch issues early

Skills lies
- writing-plans (cree le plan)
- requesting-code-review (review entre taches)
- finishing-a-development-branch (completion)

---

#### 14. dispatching-parallel-agents

Description
Lancer plusieurs agents en parallele pour investiguer des problemes independants simultanement.

Quand utiliser
- 3+ failures dans differents fichiers/subsystemes
- Problemes sans dependances entre eux
- Chaque probleme comprehensible sans contexte des autres
- Pas d'etat partage entre investigations

Quand NE PAS utiliser
- Failures potentiellement lies (fixer un pourrait fixer les autres)
- Besoin de comprendre l'etat complet du systeme
- Agents interferaient entre eux (memes fichiers)
- Debugging exploratoire (pas encore clair ce qui est casse)

Workflow
1. Identifier les domaines independants
2. Creer prompt focalise pour chaque agent :
   - Scope specifique (un fichier/subsysteme)
   - Goal clair (faire passer ces tests)
   - Contraintes (ne pas toucher autre code)
   - Output attendu (resume de ce qui est trouve/fixe)
3. Dispatcher en parallele
4. Quand agents retournent :
   - Lire chaque resume
   - Verifier pas de conflits
   - Lancer suite complete
   - Integrer

Exemple
6 test failures dans 3 fichiers apres refactoring
Dispatch parallele :
- Agent 1 : Fix agent-tool-abort.test.ts (3 failures timing)
- Agent 2 : Fix batch-completion.test.ts (2 failures execution)
- Agent 3 : Fix race-conditions.test.ts (1 failure count)

Resultats :
- Agent 1 : Remplace timeouts par event-based waiting
- Agent 2 : Fix structure evenement (threadId mal place)
- Agent 3 : Ajoute attente completion async

Integration : Pas de conflits, suite complete verte

Skills lies
- systematic-debugging (pour chaque agent)
- condition-based-waiting (fix commun pour timing)

---

### CATEGORIE: GIT/WORKFLOW

---

#### 15. using-git-worktrees

Description
Creer des workspaces git isoles pour travailler sur plusieurs branches simultanement.

Quand utiliser
- Feature necessitant isolation du workspace actuel
- Avant execution d'un plan d'implementation
- Travail parallele sur plusieurs branches

Quand NE PAS utiliser
- Modification simple sur branche actuelle
- Pas besoin d'isolation

Workflow
1. Verifier repertoires existants (.worktrees ou worktrees)
2. Si aucun : checker CLAUDE.md ou demander preference
3. Verifier .gitignore inclut le repertoire
4. Creer worktree : git worktree add path -b branch-name
5. Installer dependances (npm install, pip install, etc.)
6. Verifier baseline (tests passent)
7. Reporter location et statut

Exemple
Situation : Implementer feature auth sans polluer main
Check : .worktrees/ existe, dans .gitignore
Create : git worktree add .worktrees/auth -b feature/auth
Setup : cd .worktrees/auth && npm install
Verify : npm test -> 47 passing
Report : "Worktree ready at .worktrees/auth, tests green"

Skills lies
- brainstorming (peut creer worktree apres design)
- finishing-a-development-branch (cleanup du worktree)

---

#### 16. finishing-a-development-branch

Description
Guider la completion du travail de developpement avec options structurees pour merge, PR, ou cleanup.

Quand utiliser
- Implementation terminee
- Tous les tests passent
- Pret a integrer ou finaliser

Quand NE PAS utiliser
- Tests encore en echec
- Implementation incomplete

Workflow
1. Verifier que tests passent (bloquer si non)
2. Determiner branche de base (main/master)
3. Presenter 4 options :
   - Option 1 : Merge local vers base
   - Option 2 : Push et creer PR
   - Option 3 : Garder branche as-is
   - Option 4 : Discard le travail
4. Executer le choix
5. Cleanup worktree si applicable

Options detaillees
Option 1 - Merge local :
git checkout main && git merge feature && git branch -d feature

Option 2 - PR :
git push -u origin feature && gh pr create

Option 3 - Keep :
Reporter "Branch preserved at path"

Option 4 - Discard :
Confirmation requise, puis git branch -D feature

Skills lies
- subagent-driven-development (appele apres completion)
- executing-plans (appele apres completion)
- using-git-worktrees (cleanup du worktree)

---

### CATEGORIE: META

---

#### 17. using-superpowers

Description
Etablir les workflows obligatoires pour trouver et utiliser les skills au debut de chaque conversation.

Quand utiliser
- Debut de toute conversation
- Avant toute tache
- Toujours

Quand NE PAS utiliser
- Jamais de raison de sauter

Workflow
1. Lister les skills disponibles mentalement
2. Demander : "Un skill correspond-il a cette demande?"
3. Si oui : Utiliser le Skill tool pour lire et executer
4. Annoncer quel skill est utilise
5. Suivre le skill exactement

Rationalisations interdites
- "C'est juste une question simple" -> Les questions sont des taches
- "Je peux checker rapidement" -> Les skills disent COMMENT checker
- "Laisse-moi d'abord collecter des infos" -> Les skills guident la collecte
- "Ce skill est overkill" -> Les skills existent car le simple devient complexe
- "Je me souviens de ce skill" -> Les skills evoluent, lire la version actuelle

Regle pour checklists
Si un skill a une checklist, creer des todos TodoWrite pour CHAQUE item.

Skills lies
- Tous les autres skills (ce skill les coordonne)

---

#### 18. writing-skills

Description
Appliquer TDD a la documentation de processus : tester avec sous-agents avant d'ecrire, iterer jusqu'a bulletproof.

Quand utiliser
- Creer un nouveau skill
- Editer un skill existant
- Verifier qu'un skill fonctionne avant deploiement

Quand NE PAS utiliser
- Solutions one-off
- Pratiques standards deja documentees ailleurs
- Conventions projet-specifiques (mettre dans CLAUDE.md)

Workflow
1. RED : Creer scenarios de pression, tester SANS skill, documenter echecs
2. GREEN : Ecrire skill adressant les echecs specifiques
3. REFACTOR : Identifier nouvelles rationalisations, ajouter contre-mesures
4. Re-tester jusqu'a compliance sous pression maximale

Structure SKILL.md
- Frontmatter YAML (name, description)
- Overview avec principe core
- When to Use / When NOT to Use
- Core Pattern ou Workflow
- Quick Reference
- Common Mistakes
- Real-World Impact (optionnel)

Optimisation CSO (Claude Search Optimization)
- Description commence par "Use when..."
- Inclure symptomes et declencheurs concrets
- Mots-cles : messages d'erreur, symptomes, outils
- Noms actifs : creating-skills pas skill-creation

Skills lies
- testing-skills-with-subagents (methodologie de test)
- sharing-skills (contribuer upstream)

---

#### 19. sharing-skills

Description
Contribuer un skill au repository upstream via pull request.

Quand utiliser
- Skill applicable largement (pas projet-specifique)
- Bien teste et documente
- Pattern utile pour d'autres

Quand NE PAS utiliser
- Skill projet-specifique ou organisation-specifique
- Experimental ou instable
- Contient informations sensibles

Workflow
1. Sync avec upstream : git checkout main && git pull upstream main
2. Creer branche : git checkout -b add-skillname-skill
3. Creer/editer le skill
4. Commit avec description
5. Push vers fork : git push -u origin branch
6. Creer PR : gh pr create --repo upstream/repo

Apres merge
1. Sync local : git pull upstream main
2. Supprimer branche : git branch -d add-skillname-skill

Regle importante
Ne PAS batches plusieurs skills dans une PR. Une PR par skill.

Skills lies
- writing-skills (skill doit etre teste avant)
- testing-skills-with-subagents (verification)

---

#### 20. testing-skills-with-subagents

Description
Tester les skills avec des scenarios de pression pour verifier qu'ils resistent a la rationalisation.

Quand utiliser
- Creer ou editer un skill
- Avant deploiement d'un skill
- Skill qui enforce une discipline

Quand NE PAS utiliser
- Skills reference pure (docs API)
- Skills sans regles a violer
- Skills sans incitation a contourner

Workflow TDD pour skills
1. RED : Scenario sans skill, documenter comportement de base
2. Verify RED : Capturer rationalisations exactes
3. GREEN : Ecrire skill adressant ces echecs
4. Verify GREEN : Re-tester, agent doit maintenant se conformer
5. REFACTOR : Trouver nouvelles rationalisations, ajouter contre-mesures
6. Stay GREEN : Re-verifier apres chaque changement

Types de pression
- Time : Urgence, deadline, fenetre de deploy
- Sunk cost : Heures de travail, "gaspillage" de supprimer
- Authority : Senior dit de sauter, manager override
- Economic : Job, promotion, survie de l'entreprise
- Exhaustion : Fin de journee, fatigue, envie de rentrer
- Social : Paraitre dogmatique, inflexible
- Pragmatic : "Etre pragmatique pas dogmatique"

Meilleurs tests : combiner 3+ pressions

Exemple scenario
"Tu as passe 4h sur une feature. Ca marche parfaitement.
Tu as teste manuellement tous les edge cases. Il est 18h, diner a 18h30.
Code review demain 9h. Tu realises que tu n'as pas ecrit de tests.

Options :
A) Supprimer le code, recommencer avec TDD demain
B) Commit maintenant, tests demain
C) Ecrire tests maintenant (30 min de retard)

Choisis A, B, ou C."

Skills lies
- writing-skills (processus complet de creation)
- test-driven-development (meme cycle applique aux docs)

---

## Annexe : Quick Reference par Situation

| Situation | Skill a utiliser |
|-----------|------------------|
| Bug detecte | systematic-debugging |
| Erreur profonde | root-cause-tracing |
| Nouvelle feature | brainstorming -> writing-plans |
| Plan a executer (meme session) | subagent-driven-development |
| Plan a executer (session separee) | executing-plans |
| Ecrire du code | test-driven-development |
| Avant de dire "termine" | verification-before-completion |
| Donnees externes | defense-in-depth |
| Tests flaky | condition-based-waiting |
| Ecrire des tests | testing-anti-patterns |
| Feature complete | requesting-code-review |
| Feedback recu | receiving-code-review |
| 3+ bugs independants | dispatching-parallel-agents |
| Isolation requise | using-git-worktrees |
| Pret a merge/PR | finishing-a-development-branch |
| Debut de session | using-superpowers |
| Creer un skill | writing-skills |
| Partager un skill | sharing-skills |
| Tester un skill | testing-skills-with-subagents |

---

## Notes de version

Document genere le 2025-12-14
Base sur Superpowers v3.6.2
20 skills documentes

Ce document est concu pour servir de base a la creation d'infographies.
Chaque section peut etre convertie en card/bloc visuel independant.
