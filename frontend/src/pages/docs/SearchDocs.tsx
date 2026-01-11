// Search Documentation - Module Recherche
import DocsLayout from './DocsLayout'

export default function SearchDocs() {
  return (
    <DocsLayout
      title="Module Recherche"
      description="Trouver des produits Amazon par ASIN ou mot-cle"
    >
      <div className="space-y-8">
        {/* Purpose */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            A quoi ca sert
          </h2>
          <p className="text-vault-text-secondary">
            Le module de recherche vous permet de trouver et analyser des produits Amazon.
            Vous pouvez rechercher par ASIN specifique ou par mot-cle pour decouvrir
            de nouvelles opportunites d'arbitrage.
          </p>
        </section>

        {/* How to Use */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Comment l'utiliser
          </h2>
          <div className="space-y-4">
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Recherche par ASIN</h3>
              <ol className="list-decimal list-inside space-y-2 text-vault-text-secondary">
                <li>Allez dans <strong className="text-vault-text">Analytics</strong></li>
                <li>Entrez un ASIN Amazon (format: B0XXXXXXXXX)</li>
                <li>Cliquez sur <strong className="text-vault-text">Analyser</strong></li>
                <li>Attendez 30-60 secondes pour les resultats</li>
              </ol>
            </div>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Recherche par mot-cle</h3>
              <ol className="list-decimal list-inside space-y-2 text-vault-text-secondary">
                <li>Allez dans <strong className="text-vault-text">Discovery</strong></li>
                <li>Entrez un mot-cle (ex: "organic chemistry textbook")</li>
                <li>Configurez vos filtres (categorie, prix, BSR)</li>
                <li>Lancez la recherche</li>
              </ol>
            </div>
          </div>
        </section>

        {/* What You Should See */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Ce que vous devriez voir
          </h2>
          <div className="text-vault-text-secondary space-y-3">
            <p>Apres une recherche reussie, vous verrez:</p>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Titre du produit</strong> avec lien Amazon</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Prix d'achat et de vente</strong> estimes</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">ROI</strong> calcule automatiquement</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">BSR</strong> actuel et historique</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Nombre de vendeurs FBA</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Indicateur Amazon</strong> (si Amazon vend directement)</span>
              </li>
            </ul>
          </div>
        </section>

        {/* Troubleshooting */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Si ca ne marche pas
          </h2>
          <div className="space-y-4">
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Aucun resultat</h3>
              <ul className="space-y-1 text-sm text-vault-text-secondary">
                <li>- Verifiez que l'ASIN est correct (10 caracteres, commence par B)</li>
                <li>- Verifiez que le produit existe sur Amazon US</li>
                <li>- Essayez un autre ASIN pour confirmer que le systeme fonctionne</li>
              </ul>
            </div>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Erreur timeout</h3>
              <ul className="space-y-1 text-sm text-vault-text-secondary">
                <li>- Attendez 1-2 minutes et reessayez</li>
                <li>- L'API Keepa peut etre temporairement surchargee</li>
                <li>- Verifiez votre connexion internet</li>
              </ul>
            </div>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Donnees incompletes</h3>
              <ul className="space-y-1 text-sm text-vault-text-secondary">
                <li>- Certains produits n'ont pas d'historique Keepa</li>
                <li>- Les nouveaux produits peuvent avoir des donnees limitees</li>
                <li>- BSR "N/A" signifie que le produit n'est pas classe</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Example */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-3">
            Exemple concret
          </h2>
          <div className="text-vault-text-secondary space-y-3">
            <p>
              <strong className="text-vault-text">Scenario:</strong> Vous cherchez un livre de chimie organique
            </p>
            <ol className="list-decimal list-inside space-y-2">
              <li>Entrez l'ASIN: <code className="bg-vault-bg px-2 py-0.5 rounded text-sm">B08N5WRWNW</code></li>
              <li>Attendez l'analyse (30 sec)</li>
              <li>Resultats: ROI 45%, BSR 35,000, 2 vendeurs FBA</li>
              <li>Interpretation: Bonne opportunite - ROI solide et peu de competition</li>
            </ol>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
