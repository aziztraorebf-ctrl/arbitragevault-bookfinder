# Solution Problème MCP Claude Code → FastAPI-MCP

## 🔴 Problème Identifié

**Claude Code ne peut pas appeler les outils MCP exposés par FastAPI-MCP**, même si :
- ✅ Le serveur FastAPI-MCP fonctionne parfaitement
- ✅ MCP Inspector peut appeler les mêmes outils avec succès
- ✅ Les paramètres JSON sont identiques

**Erreur systématique** : `MCP error -32602: Invalid request parameters`

## 🟢 Cause Racine

Incompatibilité entre le SDK MCP de Claude Code et FastAPI-MCP au niveau de la sérialisation des paramètres.

**Différence critique** dans le protocole JSON-RPC :
- MCP Inspector envoie : `"arguments": { ... }` avec `_meta.progressToken`
- Claude Code semble avoir un problème de sérialisation/encoding

## ✅ Solutions Disponibles

### Solution 1: Appel Direct HTTP (Recommandé)

Contourner MCP en appelant directement l'API REST :

```bash
# Via curl
curl -X POST https://arbitragevault-backend-v2.onrender.com/api/v1/keepa/ingest \
  -H "Content-Type: application/json" \
  -d '{"identifiers":["ASIN_HERE"],"config_profile":"default","force_refresh":false}'

# Via Python script helper
python test_keepa_direct.py 0316769487 [--force-refresh]
```

### Solution 2: Utiliser MCP Inspector

Pour debugger et tester :
1. Lancer : `npx @modelcontextprotocol/inspector`
2. Connecter à : `https://arbitragevault-backend-v2.onrender.com/sse`
3. Transport : STDIO avec `npx -y mcp-remote [URL]`
4. Utiliser l'interface graphique pour tester

## 🔍 Problème Sous-jacent Découvert

Les données Keepa retournées ont **tous les scores à 50 (défaut)** car :
- `"Insufficient data: 0 points"` → Pas d'historique de prix
- `"Complete: 0.00"` → Données incomplètes
- BSR présent (24,377) mais historique manquant

**Prochaine étape** : Investiguer pourquoi les données historiques Keepa sont vides

## 📊 Résumé des Tests

| Méthode | Résultat | Notes |
|---------|----------|-------|
| Claude Code MCP | ❌ Échec | Erreur -32602 systématique |
| MCP Inspector | ✅ Succès | Fonctionne parfaitement |
| API REST Direct | ✅ Succès | Contournement efficace |
| Script Python | ✅ Succès | Helper pour tests répétés |

## 🚀 Recommandations

1. **Court terme** : Utiliser l'API REST directement via curl ou le script Python
2. **Moyen terme** : Reporter le bug à FastAPI-MCP ou Claude Code SDK
3. **Investigation** : Pourquoi les données historiques Keepa sont vides ?

---

*Dernière mise à jour : 2025-10-22*
*Problème confirmé avec Claude Code v2.0.24 et FastAPI-MCP*