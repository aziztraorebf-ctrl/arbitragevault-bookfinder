// Analysis Documentation - Comprendre les Scores
import DocsLayout from './DocsLayout'

export default function AnalysisDocs() {
  return (
    <DocsLayout
      title="Comprendre les Scores"
      description="ROI, BSR, Velocity - tout ce que vous devez savoir"
    >
      <div className="space-y-8">
        {/* Intro */}
        <section>
          <p className="text-vault-text-secondary text-lg">
            ArbitrageVault utilise plusieurs metriques pour evaluer les opportunites.
            Comprendre ces scores est essentiel pour prendre de bonnes decisions d'achat.
          </p>
        </section>

        {/* ROI */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            ROI (Return on Investment)
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <p>
              Le ROI mesure le <strong className="text-vault-text">pourcentage de profit</strong> potentiel
              sur un produit.
            </p>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <p className="text-sm mb-3">
                <strong className="text-vault-text">Formule:</strong>{' '}
                ROI = ((Prix de vente - Prix d'achat - Frais) / Prix d'achat) x 100
              </p>
            </div>

            <h3 className="font-medium text-vault-text mt-4">Interpretation</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-500">&lt; 20%</div>
                <div className="text-sm">A eviter</div>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-yellow-500">20-40%</div>
                <div className="text-sm">Acceptable</div>
              </div>
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-500">&gt; 40%</div>
                <div className="text-sm">Excellent</div>
              </div>
            </div>

            <div className="bg-vault-accent-light/30 rounded-lg p-4 border border-vault-accent/20 mt-4">
              <p className="text-sm">
                <strong className="text-vault-text">Attention:</strong> Un ROI tres eleve (&gt;100%)
                peut indiquer des donnees erronees. Verifiez toujours manuellement sur Amazon.
              </p>
            </div>
          </div>
        </section>

        {/* BSR */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            BSR (Best Seller Rank)
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <p>
              Le BSR indique le <strong className="text-vault-text">classement de vente</strong> d'un
              produit dans sa categorie. Plus le chiffre est bas, plus le produit se vend.
            </p>

            <h3 className="font-medium text-vault-text mt-4">Interpretation</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-vault-border">
                    <th className="text-left py-2 px-3 text-vault-text">BSR</th>
                    <th className="text-left py-2 px-3 text-vault-text">Vitesse de vente</th>
                    <th className="text-left py-2 px-3 text-vault-text">Temps estime</th>
                  </tr>
                </thead>
                <tbody className="text-vault-text-secondary">
                  <tr className="border-b border-vault-border/50">
                    <td className="py-2 px-3">&lt; 10,000</td>
                    <td className="py-2 px-3">Tres rapide</td>
                    <td className="py-2 px-3">1-7 jours</td>
                  </tr>
                  <tr className="border-b border-vault-border/50">
                    <td className="py-2 px-3">10,000 - 50,000</td>
                    <td className="py-2 px-3">Rapide</td>
                    <td className="py-2 px-3">1-2 semaines</td>
                  </tr>
                  <tr className="border-b border-vault-border/50">
                    <td className="py-2 px-3">50,000 - 150,000</td>
                    <td className="py-2 px-3">Moderee</td>
                    <td className="py-2 px-3">2-4 semaines</td>
                  </tr>
                  <tr className="border-b border-vault-border/50">
                    <td className="py-2 px-3">150,000 - 500,000</td>
                    <td className="py-2 px-3">Lente</td>
                    <td className="py-2 px-3">1-2 mois</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3">&gt; 500,000</td>
                    <td className="py-2 px-3">Tres lente</td>
                    <td className="py-2 px-3">Plusieurs mois</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="bg-vault-accent-light/30 rounded-lg p-4 border border-vault-accent/20 mt-4">
              <p className="text-sm">
                <strong className="text-vault-text">Note:</strong> Le BSR varie par categorie.
                Un BSR de 50,000 en "Books" est different de 50,000 en "Electronics".
              </p>
            </div>
          </div>
        </section>

        {/* Velocity Score */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Velocity Score
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <p>
              Le Velocity Score est un <strong className="text-vault-text">score composite</strong> (0-100)
              qui combine plusieurs facteurs pour estimer la vitesse de vente probable.
            </p>

            <h3 className="font-medium text-vault-text mt-4">Facteurs pris en compte</h3>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span>BSR actuel et tendance</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span>Nombre de vendeurs FBA</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span>Historique de prix</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span>Saisonnalite du produit</span>
              </li>
            </ul>

            <h3 className="font-medium text-vault-text mt-4">Interpretation</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-500">&lt; 50</div>
                <div className="text-sm">Prudence</div>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-yellow-500">50-70</div>
                <div className="text-sm">Correct</div>
              </div>
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-500">&gt; 70</div>
                <div className="text-sm">Excellent</div>
              </div>
            </div>
          </div>
        </section>

        {/* Confidence Score */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Confidence Score
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <p>
              Le Confidence Score indique la <strong className="text-vault-text">fiabilite des donnees</strong>.
              Plus le score est eleve, plus vous pouvez faire confiance aux metriques affichees.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-500">&lt; 60%</div>
                <div className="text-sm">Verifier manuellement</div>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-yellow-500">60-80%</div>
                <div className="text-sm">Fiable</div>
              </div>
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-500">&gt; 80%</div>
                <div className="text-sm">Tres fiable</div>
              </div>
            </div>
          </div>
        </section>

        {/* Decision Matrix */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-4">
            Matrice de Decision
          </h2>
          <div className="text-vault-text-secondary">
            <p className="mb-4">
              Pour une bonne opportunite d'achat, recherchez:
            </p>
            <ul className="space-y-2">
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">OK</span>
                <span>ROI &gt; 30%</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">OK</span>
                <span>BSR &lt; 100,000</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">OK</span>
                <span>Velocity &gt; 60</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">OK</span>
                <span>Confidence &gt; 70%</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">OK</span>
                <span>Amazon n'est PAS vendeur</span>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
