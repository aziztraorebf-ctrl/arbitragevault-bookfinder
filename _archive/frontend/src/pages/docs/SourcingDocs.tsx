// Sourcing Documentation
import DocsLayout from './DocsLayout'

export default function SourcingDocs() {
  return (
    <DocsLayout
      title="Auto-Sourcing"
      description="Laissez le systeme trouver les meilleures opportunites pour vous"
    >
      <div className="space-y-8">
        {/* Purpose */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            A quoi ca sert
          </h2>
          <p className="text-vault-text-secondary">
            L'Auto-Sourcing est le <strong className="text-vault-text">niveau superieur d'automatisation</strong>.
            Au lieu de definir des recherches specifiques, vous configurez des criteres
            et le systeme trouve automatiquement les produits qui correspondent.
          </p>
          <div className="mt-4 p-4 bg-vault-bg rounded-lg border border-vault-border">
            <p className="text-sm text-vault-text-secondary">
              <strong className="text-vault-text">Difference avec le Scheduler:</strong><br />
              - <strong>Scheduler</strong> = Vous definissez QUOI chercher (ASINs, mots-cles)<br />
              - <strong>Auto-Sourcing</strong> = Vous definissez des CRITERES, le systeme cherche pour vous
            </p>
          </div>
        </section>

        {/* How it Works */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Comment ca fonctionne
          </h2>
          <div className="relative">
            {/* Flow diagram */}
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-vault-accent flex items-center justify-center text-white font-bold">
                  1
                </div>
                <div className="flex-1 p-4 bg-vault-bg rounded-lg border border-vault-border">
                  <h3 className="font-medium text-vault-text">Configuration des criteres</h3>
                  <p className="text-sm text-vault-text-secondary mt-1">
                    Vous definissez ROI minimum, BSR max, categories preferees, etc.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-vault-accent flex items-center justify-center text-white font-bold">
                  2
                </div>
                <div className="flex-1 p-4 bg-vault-bg rounded-lg border border-vault-border">
                  <h3 className="font-medium text-vault-text">Scan automatique</h3>
                  <p className="text-sm text-vault-text-secondary mt-1">
                    Le systeme analyse des milliers de produits selon vos criteres.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-vault-accent flex items-center justify-center text-white font-bold">
                  3
                </div>
                <div className="flex-1 p-4 bg-vault-bg rounded-lg border border-vault-border">
                  <h3 className="font-medium text-vault-text">Filtrage intelligent</h3>
                  <p className="text-sm text-vault-text-secondary mt-1">
                    Seuls les produits correspondant a TOUS vos criteres sont retenus.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center text-white font-bold">
                  4
                </div>
                <div className="flex-1 p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                  <h3 className="font-medium text-vault-text">Resultats livres</h3>
                  <p className="text-sm text-vault-text-secondary mt-1">
                    Vous recevez une liste d'opportunites verifiees, prete a l'achat.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Configuration */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Criteres configurables
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-vault-border">
                  <th className="text-left py-3 px-4 text-vault-text">Critere</th>
                  <th className="text-left py-3 px-4 text-vault-text">Description</th>
                  <th className="text-left py-3 px-4 text-vault-text">Valeur recommandee</th>
                </tr>
              </thead>
              <tbody className="text-vault-text-secondary">
                <tr className="border-b border-vault-border/50">
                  <td className="py-3 px-4 font-medium text-vault-text">ROI minimum</td>
                  <td className="py-3 px-4">Pourcentage de profit minimum</td>
                  <td className="py-3 px-4">30% ou plus</td>
                </tr>
                <tr className="border-b border-vault-border/50">
                  <td className="py-3 px-4 font-medium text-vault-text">BSR maximum</td>
                  <td className="py-3 px-4">Classement de vente maximum</td>
                  <td className="py-3 px-4">100,000 ou moins</td>
                </tr>
                <tr className="border-b border-vault-border/50">
                  <td className="py-3 px-4 font-medium text-vault-text">Prix d'achat max</td>
                  <td className="py-3 px-4">Budget maximum par produit</td>
                  <td className="py-3 px-4">Selon votre budget</td>
                </tr>
                <tr className="border-b border-vault-border/50">
                  <td className="py-3 px-4 font-medium text-vault-text">Vendeurs FBA max</td>
                  <td className="py-3 px-4">Limite de competition</td>
                  <td className="py-3 px-4">3-5 maximum</td>
                </tr>
                <tr className="border-b border-vault-border/50">
                  <td className="py-3 px-4 font-medium text-vault-text">Exclure Amazon</td>
                  <td className="py-3 px-4">Ignorer si Amazon vend</td>
                  <td className="py-3 px-4">Oui (recommande)</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium text-vault-text">Categories</td>
                  <td className="py-3 px-4">Categories a surveiller</td>
                  <td className="py-3 px-4">2-3 categories max</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Tips for Beginners */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Conseils pour debutants
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-vault-bg rounded-lg border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-xs font-bold">1</span>
                Commencez prudemment
              </h3>
              <p className="text-sm text-vault-text-secondary">
                Utilisez des criteres stricts au debut (ROI &gt; 40%, BSR &lt; 50k).
                Elargissez progressivement.
              </p>
            </div>
            <div className="p-4 bg-vault-bg rounded-lg border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-xs font-bold">2</span>
                Focalisez-vous
              </h3>
              <p className="text-sm text-vault-text-secondary">
                Choisissez 1-2 categories que vous connaissez. Mieux vaut etre expert
                dans un domaine.
              </p>
            </div>
            <div className="p-4 bg-vault-bg rounded-lg border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-xs font-bold">3</span>
                Verifiez toujours
              </h3>
              <p className="text-sm text-vault-text-secondary">
                Meme avec l'auto-sourcing, verifiez manuellement avant d'acheter.
                Le systeme peut se tromper.
              </p>
            </div>
            <div className="p-4 bg-vault-bg rounded-lg border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-xs font-bold">4</span>
                Surveillez les tokens
              </h3>
              <p className="text-sm text-vault-text-secondary">
                L'auto-sourcing consomme plus de tokens. Gardez un oeil sur votre
                quota Keepa.
              </p>
            </div>
          </div>
        </section>

        {/* Advanced */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-4">
            Fonctionnalites avancees
          </h2>
          <div className="space-y-4 text-sm text-vault-text-secondary">
            <div>
              <p className="font-medium text-vault-text">Niches personnalisees</p>
              <p className="mt-1">
                Creez des profils de recherche pour differentes niches avec des criteres specifiques.
              </p>
            </div>
            <div>
              <p className="font-medium text-vault-text">Alertes</p>
              <p className="mt-1">
                Recevez une notification quand une opportunite exceptionnelle est trouvee.
              </p>
            </div>
            <div>
              <p className="font-medium text-vault-text">Historique</p>
              <p className="mt-1">
                Consultez l'historique des produits trouves pour identifier des patterns.
              </p>
            </div>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
