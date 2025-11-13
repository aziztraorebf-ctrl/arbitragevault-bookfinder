# Rapport de Nettoyage des Scripts de Debug

**Date**: 2025-10-24T10:02:33.451368
**Scripts analysés**: 126
**Scripts conservés**: 17
**Scripts archivés**: 109
**Lignes économisées**: 19,143
**Espace libéré**: 702.0 KB

## 📌 Scripts Conservés (Top 10 + Essentiels)

| Script | Score | Lignes | Raisons |
|--------|-------|--------|---------|
| test_keepa_endpoints_smoke.py | 65 | 270 | Imports production, Logique business, Tests pytest |
| test_keepa_endpoints.py | 65 | 366 | Imports production, Logique business, Tests pytest |
| test_phase1_unified_parser.py | 65 | 145 | Récent (5j), Imports production, Logique business |
| test_phase2_pricing_metrics.py | 65 | 204 | Récent (5j), Imports production, Logique business |
| test_phase3_unified_builder.py | 65 | 234 | Récent (5j), Imports production, Logique business |
| test_phase4_endpoint_integration.py | 65 | 172 | Récent (5j), Imports production, Logique business |
| test_phase5_offers_validation.py | 65 | 333 | Récent (5j), Imports production, Logique business |
| test_core_services.py | 60 | 706 | Imports production, Logique business, Tests pytest |
| analyze_bsr_history.py | 60 | 168 | Récent (1j), Logique business, Bien documenté |
| test_parser_local.py | 60 | 64 | Récent (1j), Imports production, Logique business |
| validate_velocity_fix.py | 60 | 221 | Récent (1j), Logique business, Bien documenté |
| test_autosourcing_structure.py | 55 | 169 | Imports production, Logique business, Tests pytest |
| test_business_config_smoke.py | 55 | 199 | Imports production, Logique business, Tests pytest |
| test_components_direct.py | 55 | 240 | Imports production, Logique business, Tests pytest |
| test_concurrent.py | 55 | 133 | Imports production, Logique business, Bien documenté |
| test_keepa_direct.py | 55 | 88 | Récent (2j), Logique business, Bien documenté |
| test_keepa_direct.py | 30 | 138 | Logique business, Bien documenté, Taille optimale |

## 📦 Scripts Archivés (Top 20)

| Script | Score | Lignes | Raisons |
|--------|-------|--------|---------|
| test_config_integration_smoke.py | 55 | 287 | Imports production, Logique business, Tests pytest |
| test_e2e_bsr_pipeline.py | 55 | 265 | Imports production, Logique business, Tests pytest |
| test_parser_v2_simple.py | 55 | 207 | Imports production, Logique business, Tests pytest |
| test_stock_estimate.py | 55 | 162 | Imports production, Logique business, Tests pytest |
| test_stock_integration.py | 55 | 176 | Imports production, Logique business, Tests pytest |
| test_bookmark_service.py | 55 | 272 | Imports production, Logique business, Tests pytest |
| test_analysis_repository.py | 55 | 489 | Imports production, Logique business, Tests pytest |
| test_base_repository_concurrent.py | 55 | 277 | Imports production, Logique business, Tests pytest |
| test_base_repository_integration.py | 55 | 357 | Imports production, Logique business, Tests pytest |
| test_base_repository_performance.py | 55 | 179 | Imports production, Logique business, Tests pytest |
| test_base_repository_scale.py | 55 | 254 | Imports production, Logique business, Tests pytest |
| test_base_repository_simple.py | 55 | 147 | Imports production, Logique business, Tests pytest |
| test_basic_models.py | 55 | 109 | Imports production, Logique business, Tests pytest |
| test_keepa_parser_v2.py | 55 | 328 | Imports production, Logique business, Tests pytest |
| test_models_extended.py | 55 | 420 | Imports production, Logique business, Tests pytest |
| test_models_simple.py | 55 | 252 | Imports production, Logique business, Tests pytest |
| test_niche_discovery.py | 55 | 331 | Imports production, Logique business, Tests pytest |
| test_pagination_sorting.py | 55 | 389 | Imports production, Logique business, Tests pytest |
| concurrency_test.py | 55 | 304 | Imports production, Logique business, Bien documenté |
| test_amazon_check_service.py | 55 | 350 | Imports production, Logique business, Tests pytest |

*... et 89 autres scripts*

## 💡 Recommandations

1. **Scripts conservés** : Réviser et intégrer dans la suite de tests officielle
2. **Scripts archivés** : Disponibles dans `_archive_debug/` si besoin
3. **Prochaine étape** : Créer une vraie suite pytest dans `tests/`
4. **Documentation** : Documenter les scripts conservés