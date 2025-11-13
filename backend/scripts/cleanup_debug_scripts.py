#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage et archivage des scripts de debug
Phase 1 Jour 1 - Plan Turbo Optimisé

Ce script :
1. Identifie tous les scripts de debug/test
2. Sélectionne les 10 plus utiles à conserver
3. Archive les autres dans _archive_debug/
4. Génère un rapport de nettoyage
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json
import re
from typing import List, Dict, Tuple
import sys
import io

# Forcer UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class DebugScriptCleaner:
    def __init__(self):
        self.base_path = Path.cwd()
        # Si on est déjà dans backend, utiliser le dossier courant
        if self.base_path.name == "backend":
            self.backend_path = self.base_path
            self.project_root = self.base_path.parent
        else:
            self.backend_path = self.base_path / "backend"
            self.project_root = self.base_path
        self.archive_dir = self.backend_path / "_archive_debug"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Patterns pour identifier les scripts de debug
        self.debug_patterns = [
            r"test_.*\.py$",
            r"debug_.*\.py$",
            r".*_test\.py$",
            r".*_debug\.py$",
            r"check_.*\.py$",
            r"validate_.*\.py$",
            r"verify_.*\.py$",
            r"analyze_.*\.py$",
            r"fix_.*\.py$",
            r"temp_.*\.py$",
            r"old_.*\.py$",
            r"backup_.*\.py$",
            r".*_old\.py$",
            r".*_backup\.py$",
            r".*_temp\.py$"
        ]

        # Scripts essentiels à TOUJOURS conserver
        self.essential_scripts = [
            "audit_api.py",
            "audit_frontend.py",
            "cleanup_debug_scripts.py",  # Ce script lui-même
            "api_helper.py",  # Helper API utile
            "test_keepa_direct.py",  # Test Keepa principal
        ]

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "scripts_found": [],
            "scripts_to_keep": [],
            "scripts_to_archive": [],
            "stats": {
                "total_found": 0,
                "kept": 0,
                "archived": 0,
                "lines_saved": 0,
                "size_saved_kb": 0
            }
        }

    def is_debug_script(self, filename: str) -> bool:
        """Vérifie si un fichier est un script de debug"""
        for pattern in self.debug_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        return False

    def analyze_script_importance(self, filepath: Path) -> Dict:
        """Analyse l'importance d'un script"""
        info = {
            "name": filepath.name,
            "path": str(filepath),
            "size": filepath.stat().st_size,
            "lines": 0,
            "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            "score": 0,
            "reasons": []
        }

        # Compter les lignes
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                info["lines"] = len(f.readlines())
                f.seek(0)
                content = f.read()
        except:
            return info

        # Scoring basé sur plusieurs critères

        # 1. Scripts récents (modifiés dans les 7 derniers jours) = +20 points
        days_old = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).days
        if days_old <= 7:
            info["score"] += 20
            info["reasons"].append(f"Récent ({days_old}j)")

        # 2. Scripts avec imports production = +15 points
        if "from app" in content or "from src" in content:
            info["score"] += 15
            info["reasons"].append("Imports production")

        # 3. Scripts avec vraie logique business = +15 points
        if "keepa" in content.lower() or "analysis" in content or "velocity" in content:
            info["score"] += 15
            info["reasons"].append("Logique business")

        # 4. Scripts avec tests pytest = +10 points
        if "pytest" in content or "assert" in content:
            info["score"] += 10
            info["reasons"].append("Tests pytest")

        # 5. Scripts documentés = +10 points
        if content.count('"""') >= 2 or content.count("'''") >= 2:
            info["score"] += 10
            info["reasons"].append("Bien documenté")

        # 6. Scripts avec API calls = +10 points
        if "requests" in content or "httpx" in content or "aiohttp" in content:
            info["score"] += 10
            info["reasons"].append("API calls")

        # 7. Taille raisonnable (100-500 lignes) = +5 points
        if 100 <= info["lines"] <= 500:
            info["score"] += 5
            info["reasons"].append("Taille optimale")

        # 8. Scripts dans le dossier scripts/ = +5 points
        if "scripts" in str(filepath.parent):
            info["score"] += 5
            info["reasons"].append("Dans scripts/")

        # Pénalités

        # Scripts trop petits (<50 lignes) = -10 points
        if info["lines"] < 50:
            info["score"] -= 10
            info["reasons"].append("Trop petit")

        # Scripts trop gros (>1000 lignes) = -5 points
        if info["lines"] > 1000:
            info["score"] -= 5
            info["reasons"].append("Trop gros")

        # Scripts avec "old" ou "backup" dans le nom = -15 points
        if "old" in filepath.name.lower() or "backup" in filepath.name.lower():
            info["score"] -= 15
            info["reasons"].append("Obsolète")

        # Scripts temporaires = -20 points
        if "temp" in filepath.name.lower() or "tmp" in filepath.name.lower():
            info["score"] -= 20
            info["reasons"].append("Temporaire")

        return info

    def find_all_debug_scripts(self) -> List[Dict]:
        """Trouve tous les scripts de debug dans le backend et la racine du projet"""
        scripts = []

        # 1. Chercher dans le backend
        for root, dirs, files in os.walk(self.backend_path):
            # Ignorer certains dossiers
            if "__pycache__" in root or ".git" in root or "_archive" in root or ".venv" in root:
                continue

            for file in files:
                if file.endswith(".py") and self.is_debug_script(file):
                    filepath = Path(root) / file
                    script_info = self.analyze_script_importance(filepath)
                    scripts.append(script_info)

        # 2. Chercher aussi dans la racine du projet
        for file in os.listdir(self.project_root):
            filepath = self.project_root / file
            if filepath.is_file() and filepath.suffix == ".py" and self.is_debug_script(file):
                script_info = self.analyze_script_importance(filepath)
                scripts.append(script_info)

        # Trier par score décroissant
        scripts.sort(key=lambda x: x["score"], reverse=True)

        return scripts

    def select_scripts_to_keep(self, scripts: List[Dict], max_keep: int = 10) -> Tuple[List[Dict], List[Dict]]:
        """Sélectionne les scripts à conserver"""
        to_keep = []
        to_archive = []

        for script in scripts:
            # Toujours garder les scripts essentiels
            if script["name"] in self.essential_scripts:
                to_keep.append(script)
            elif len(to_keep) < max_keep and script["score"] > 0:
                to_keep.append(script)
            else:
                to_archive.append(script)

        return to_keep, to_archive

    def archive_scripts(self, scripts: List[Dict], dry_run: bool = False) -> Dict:
        """Archive les scripts dans _archive_debug/"""
        # Créer le dossier d'archive
        archive_subdir = self.archive_dir / f"cleanup_{self.timestamp}"

        if not dry_run:
            self.archive_dir.mkdir(exist_ok=True)
            archive_subdir.mkdir(exist_ok=True)

        archived = []
        errors = []

        for script in scripts:
            src = Path(script["path"])
            if not src.exists():
                errors.append(f"Not found: {script['path']}")
                continue

            # Déterminer le chemin de destination en préservant la structure
            try:
                # Essayer de faire relatif au backend
                rel_path = src.relative_to(self.backend_path)
            except ValueError:
                # Si pas dans backend, essayer relatif au projet
                try:
                    rel_path = src.relative_to(self.project_root)
                except ValueError:
                    # Sinon utiliser juste le nom
                    rel_path = Path(src.name)

            dst = archive_subdir / rel_path if not dry_run else None

            if not dry_run:
                try:
                    # Créer les dossiers parents si nécessaire
                    dst.parent.mkdir(parents=True, exist_ok=True)

                    # Déplacer le fichier
                    shutil.move(str(src), str(dst))
                    archived.append({
                        "name": script["name"],
                        "from": str(src),
                        "to": str(dst),
                        "size": script["size"],
                        "lines": script["lines"]
                    })
                    print(f"   ✅ Archivé: {script['name']} ({script['lines']} lignes)")
                except Exception as e:
                    errors.append(f"Error archiving {script['name']}: {str(e)}")
                    print(f"   ❌ Erreur: {script['name']} - {str(e)}")
            else:
                archived.append({
                    "name": script["name"],
                    "from": str(src),
                    "to": f"[DRY RUN] {archive_subdir / rel_path}",
                    "size": script["size"],
                    "lines": script["lines"]
                })
                print(f"   [DRY RUN] À archiver: {script['name']} ({script['lines']} lignes)")

        return {"archived": archived, "errors": errors}

    def generate_report(self, output_file: str = "doc/cleanup_report.md"):
        """Génère un rapport Markdown du nettoyage"""
        report = []
        report.append("# Rapport de Nettoyage des Scripts de Debug")
        report.append(f"\n**Date**: {self.results['timestamp']}")
        report.append(f"**Scripts analysés**: {self.results['stats']['total_found']}")
        report.append(f"**Scripts conservés**: {self.results['stats']['kept']}")
        report.append(f"**Scripts archivés**: {self.results['stats']['archived']}")
        report.append(f"**Lignes économisées**: {self.results['stats']['lines_saved']:,}")
        report.append(f"**Espace libéré**: {self.results['stats']['size_saved_kb']:.1f} KB")

        # Scripts conservés
        report.append("\n## 📌 Scripts Conservés (Top 10 + Essentiels)")
        report.append("\n| Script | Score | Lignes | Raisons |")
        report.append("|--------|-------|--------|---------|")

        for script in self.results["scripts_to_keep"]:
            reasons = ", ".join(script["reasons"][:3])  # Top 3 raisons
            report.append(f"| {script['name']} | {script['score']} | {script['lines']} | {reasons} |")

        # Scripts archivés (top 20)
        report.append("\n## 📦 Scripts Archivés (Top 20)")
        report.append("\n| Script | Score | Lignes | Raisons |")
        report.append("|--------|-------|--------|---------|")

        for script in self.results["scripts_to_archive"][:20]:
            reasons = ", ".join(script["reasons"][:3])
            report.append(f"| {script['name']} | {script['score']} | {script['lines']} | {reasons} |")

        if len(self.results["scripts_to_archive"]) > 20:
            report.append(f"\n*... et {len(self.results['scripts_to_archive']) - 20} autres scripts*")

        # Recommandations
        report.append("\n## 💡 Recommandations")
        report.append("\n1. **Scripts conservés** : Réviser et intégrer dans la suite de tests officielle")
        report.append("2. **Scripts archivés** : Disponibles dans `_archive_debug/` si besoin")
        report.append("3. **Prochaine étape** : Créer une vraie suite pytest dans `tests/`")
        report.append("4. **Documentation** : Documenter les scripts conservés")

        # Sauvegarder le rapport
        # Utiliser un chemin relatif depuis le dossier courant
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True, parents=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        print(f"\n📝 Rapport sauvegardé dans: {output_path}")

        return "\n".join(report)

    def run(self, dry_run: bool = True):
        """Exécute le nettoyage complet"""
        print("\n" + "="*60)
        print("🧹 NETTOYAGE DES SCRIPTS DE DEBUG")
        print("="*60)

        if dry_run:
            print("⚠️  MODE DRY RUN - Aucun fichier ne sera déplacé")
        else:
            print("🔴 MODE RÉEL - Les fichiers seront archivés")

        # 1. Trouver tous les scripts de debug
        print("\n📌 Étape 1: Recherche des scripts de debug...")
        scripts = self.find_all_debug_scripts()
        print(f"   ✅ {len(scripts)} scripts trouvés")

        # 2. Sélectionner les scripts à conserver
        print("\n📌 Étape 2: Sélection des scripts à conserver...")
        to_keep, to_archive = self.select_scripts_to_keep(scripts, max_keep=15)  # 15 pour inclure les essentiels

        print(f"   ✅ {len(to_keep)} scripts à conserver")
        print(f"   📦 {len(to_archive)} scripts à archiver")

        # 3. Calculer les statistiques
        total_lines_archived = sum(s["lines"] for s in to_archive)
        total_size_archived = sum(s["size"] for s in to_archive)

        self.results["scripts_found"] = scripts
        self.results["scripts_to_keep"] = to_keep
        self.results["scripts_to_archive"] = to_archive
        self.results["stats"]["total_found"] = len(scripts)
        self.results["stats"]["kept"] = len(to_keep)
        self.results["stats"]["archived"] = len(to_archive)
        self.results["stats"]["lines_saved"] = total_lines_archived
        self.results["stats"]["size_saved_kb"] = total_size_archived / 1024

        print(f"\n📊 Impact du nettoyage:")
        print(f"   - Lignes de code à nettoyer: {total_lines_archived:,}")
        print(f"   - Espace à libérer: {total_size_archived / 1024:.1f} KB")

        # 4. Afficher les scripts à conserver
        print("\n✅ Scripts à CONSERVER:")
        for script in to_keep:
            print(f"   - {script['name']} (score: {script['score']}, {script['lines']} lignes)")

        # 5. Archiver les scripts (si pas en dry run)
        if len(to_archive) > 0:
            print(f"\n📦 Archivage de {len(to_archive)} scripts...")
            archive_result = self.archive_scripts(to_archive, dry_run=dry_run)

            if archive_result["errors"]:
                print(f"\n⚠️  {len(archive_result['errors'])} erreurs lors de l'archivage:")
                for error in archive_result["errors"][:5]:
                    print(f"   - {error}")

        # 6. Générer le rapport
        print("\n📝 Génération du rapport...")
        self.generate_report()

        # 7. Sauvegarder les résultats JSON
        results_file = Path("doc") / "cleanup_results.json"
        results_file.parent.mkdir(exist_ok=True, parents=True)
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"💾 Résultats sauvegardés dans: {results_file}")

        print("\n" + "="*60)
        if dry_run:
            print("✅ SIMULATION TERMINÉE - Exécuter avec dry_run=False pour appliquer")
        else:
            print("✅ NETTOYAGE TERMINÉ - Scripts archivés dans _archive_debug/")
        print("="*60)

        return self.results


if __name__ == "__main__":
    import sys

    # Par défaut en dry run pour sécurité
    dry_run = True

    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        dry_run = False
        print("⚠️  ATTENTION: Mode réel activé - les fichiers seront déplacés!")
        response = input("Confirmer? (yes/no): ")
        if response.lower() != "yes":
            print("Annulé.")
            sys.exit(0)

    cleaner = DebugScriptCleaner()
    results = cleaner.run(dry_run=dry_run)

    print(f"\n💡 Pour appliquer le nettoyage, exécuter:")
    print(f"   python scripts/cleanup_debug_scripts.py --apply")