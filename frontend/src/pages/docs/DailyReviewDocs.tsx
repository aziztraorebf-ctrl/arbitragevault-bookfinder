// Daily Review Documentation
import DocsLayout from './DocsLayout'

export default function DailyReviewDocs() {
  return (
    <DocsLayout
      title="Daily Review"
      description="Votre rapport quotidien d'opportunites classifiees"
      badge="Actif"
    >
      <div className="space-y-8">
        {/* Coming Soon Banner */}
        <section className="bg-vault-accent/10 border border-vault-accent/30 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-vault-accent/20 flex items-center justify-center">
              <span className="text-vault-accent text-xl">!</span>
            </div>
            <h2 className="text-xl font-semibold text-vault-text">
              Fonctionnalite en cours de developpement
            </h2>
          </div>
          <p className="text-vault-text-secondary">
            Le Daily Review Engine est actuellement en phase de prototype.
            Cette page decrit les fonctionnalites prevues.
          </p>
        </section>

        {/* What is it */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Qu'est-ce que le Daily Review?
          </h2>
          <p className="text-vault-text-secondary mb-4">
            Le Daily Review est un <strong className="text-vault-text">rapport automatique quotidien</strong> qui
            analyse toutes les opportunites trouvees et vous presente un resume actionnable.
          </p>
          <p className="text-vault-text-secondary">
            Au lieu de parcourir des dizaines de produits, vous recevez chaque matin
            une synthese claire avec des recommandations explicites.
          </p>
        </section>

        {/* Classifications */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Classifications des produits
          </h2>
          <p className="text-vault-text-secondary mb-4">
            Chaque produit sera classe dans une de ces categories:
          </p>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 bg-green-500/10 rounded-lg border border-green-500/20">
              <div className="px-3 py-1 rounded-full bg-green-500 text-white text-sm font-bold">
                STABLE
              </div>
              <div>
                <p className="text-vault-text font-medium">Opportunite fiable</p>
                <p className="text-sm text-vault-text-secondary mt-1">
                  Produit vu plusieurs fois avec metriques coherentes. Recommande pour achat.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
              <div className="px-3 py-1 rounded-full bg-yellow-500 text-white text-sm font-bold">
                JACKPOT
              </div>
              <div>
                <p className="text-vault-text font-medium">ROI exceptionnel</p>
                <p className="text-sm text-vault-text-secondary mt-1">
                  ROI &gt; 80%. Opportunite rare mais necessite verification manuelle.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <div className="px-3 py-1 rounded-full bg-blue-500 text-white text-sm font-bold">
                REVENANT
              </div>
              <div>
                <p className="text-vault-text font-medium">Produit de retour</p>
                <p className="text-sm text-vault-text-secondary mt-1">
                  Produit qui revient apres une absence de 24h+. Peut indiquer un pattern.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-gray-500/10 rounded-lg border border-gray-500/20">
              <div className="px-3 py-1 rounded-full bg-gray-500 text-white text-sm font-bold">
                FLUKE
              </div>
              <div>
                <p className="text-vault-text font-medium">Donnees suspectes</p>
                <p className="text-sm text-vault-text-secondary mt-1">
                  Vu une fois puis disparu, ou donnees incoherentes. A ignorer.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
              <div className="px-3 py-1 rounded-full bg-red-500 text-white text-sm font-bold">
                REJECT
              </div>
              <div>
                <p className="text-vault-text font-medium">A eviter</p>
                <p className="text-sm text-vault-text-secondary mt-1">
                  Amazon vendeur, ROI negatif, ou autre raison bloquante.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* What you'll receive */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Ce que vous recevrez
          </h2>
          <div className="bg-vault-bg rounded-xl border border-vault-border overflow-hidden">
            <div className="p-4 border-b border-vault-border bg-vault-card">
              <h3 className="font-medium text-vault-text">Exemple de Daily Review</h3>
            </div>
            <div className="p-4 space-y-4 text-sm">
              <div className="p-3 bg-vault-card rounded-lg">
                <p className="font-medium text-vault-text">Resume du jour</p>
                <p className="text-vault-text-secondary mt-1">
                  "5 achats recommandes (ROI moy. 45%). 2 jackpots a verifier.
                  Focus recommande: Textbooks."
                </p>
              </div>
              <div className="p-3 bg-vault-card rounded-lg">
                <p className="font-medium text-vault-text">Top 3 opportunites</p>
                <ul className="text-vault-text-secondary mt-1 space-y-1">
                  <li>- ASIN B08XXX - ROI 52% - STABLE - Achat recommande</li>
                  <li>- ASIN B09XXX - ROI 95% - JACKPOT - A verifier</li>
                  <li>- ASIN B07XXX - ROI 38% - STABLE - Achat recommande</li>
                </ul>
              </div>
              <div className="p-3 bg-vault-card rounded-lg">
                <p className="font-medium text-vault-text">Alertes</p>
                <p className="text-vault-text-secondary mt-1">
                  "2 produits rejetes: Amazon vendeur sur ASIN B04XXX, ROI negatif sur ASIN B03XXX"
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Timeline */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-4">
            Roadmap
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <div>
                <p className="font-medium text-vault-text">Phase 1: Prototype</p>
                <p className="text-sm text-vault-text-secondary">Classification et justifications - Complete</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <div>
                <p className="font-medium text-vault-text">Phase 2: Integration Backend</p>
                <p className="text-sm text-vault-text-secondary">API endpoint + classification engine - Complete</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-gray-300"></div>
              <div>
                <p className="font-medium text-vault-text">Phase 3: Automatisation N8N</p>
                <p className="text-sm text-vault-text-secondary">Envoi automatique par email - A venir</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <div>
                <p className="font-medium text-vault-text">Phase 4: Dashboard Card</p>
                <p className="text-sm text-vault-text-secondary">DailyReviewCard sur le dashboard - Complete</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
