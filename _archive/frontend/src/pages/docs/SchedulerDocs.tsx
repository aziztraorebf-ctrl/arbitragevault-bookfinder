// Scheduler Documentation
import DocsLayout from './DocsLayout'

export default function SchedulerDocs() {
  return (
    <DocsLayout
      title="Scheduler (Planificateur)"
      description="Automatisez vos recherches avec le planificateur"
    >
      <div className="space-y-8">
        {/* Purpose */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            A quoi ca sert
          </h2>
          <p className="text-vault-text-secondary">
            Le Scheduler vous permet de <strong className="text-vault-text">planifier des recherches automatiques</strong>.
            Au lieu de lancer manuellement des recherches chaque jour, configurez-les une fois
            et laissez le systeme travailler pour vous.
          </p>
        </section>

        {/* Benefits */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Pourquoi l'utiliser
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                  <span className="text-green-500 text-lg">1</span>
                </div>
                <h3 className="font-medium text-vault-text">Gain de temps</h3>
              </div>
              <p className="text-sm text-vault-text-secondary">
                Plus besoin de lancer les memes recherches chaque jour.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <span className="text-blue-500 text-lg">2</span>
                </div>
                <h3 className="font-medium text-vault-text">Regularite</h3>
              </div>
              <p className="text-sm text-vault-text-secondary">
                Les recherches sont executees a heure fixe, meme si vous oubliez.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <span className="text-purple-500 text-lg">3</span>
                </div>
                <h3 className="font-medium text-vault-text">Opportunites</h3>
              </div>
              <p className="text-sm text-vault-text-secondary">
                Ne ratez jamais une bonne affaire - le systeme surveille pour vous.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <span className="text-orange-500 text-lg">4</span>
                </div>
                <h3 className="font-medium text-vault-text">Historique</h3>
              </div>
              <p className="text-sm text-vault-text-secondary">
                Suivez l'evolution des prix et BSR sur plusieurs jours.
              </p>
            </div>
          </div>
        </section>

        {/* How to Configure */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Comment configurer
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <ol className="space-y-4">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">1</span>
                <div>
                  <strong className="text-vault-text">Accedez au Scheduler</strong>
                  <p className="text-sm mt-1">Cliquez sur "Scheduler" dans la navigation laterale.</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">2</span>
                <div>
                  <strong className="text-vault-text">Creez une nouvelle tache</strong>
                  <p className="text-sm mt-1">Cliquez sur "Nouvelle tache" ou "Add Schedule".</p>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">3</span>
                <div>
                  <strong className="text-vault-text">Definissez les parametres</strong>
                  <ul className="text-sm mt-1 space-y-1 ml-4 list-disc">
                    <li>Nom de la tache (ex: "Textbooks quotidien")</li>
                    <li>Type de recherche (ASIN, mot-cle, categorie)</li>
                    <li>Frequence (quotidien, hebdomadaire)</li>
                    <li>Heure d'execution</li>
                  </ul>
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">4</span>
                <div>
                  <strong className="text-vault-text">Activez la tache</strong>
                  <p className="text-sm mt-1">Basculez le switch pour activer. La tache s'executera automatiquement.</p>
                </div>
              </li>
            </ol>
          </div>
        </section>

        {/* Best Practices */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Bonnes pratiques
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-vault-bg rounded-lg border border-vault-border">
              <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-green-500 text-xs">OK</span>
              </div>
              <div className="text-sm text-vault-text-secondary">
                <strong className="text-vault-text">Planifiez tot le matin</strong> (6h-8h) pour avoir les resultats
                avant de commencer votre journee.
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-vault-bg rounded-lg border border-vault-border">
              <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-green-500 text-xs">OK</span>
              </div>
              <div className="text-sm text-vault-text-secondary">
                <strong className="text-vault-text">Limitez le nombre de taches</strong> pour ne pas epuiser
                vos tokens Keepa trop rapidement.
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-vault-bg rounded-lg border border-vault-border">
              <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-green-500 text-xs">OK</span>
              </div>
              <div className="text-sm text-vault-text-secondary">
                <strong className="text-vault-text">Variez les categories</strong> pour diversifier
                vos opportunites.
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-vault-bg rounded-lg border border-vault-border">
              <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-red-500 text-xs">X</span>
              </div>
              <div className="text-sm text-vault-text-secondary">
                <strong className="text-vault-text">Evitez trop de taches simultanees</strong> -
                espacez les heures d'execution de 10-15 minutes.
              </div>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-4">
            Problemes courants
          </h2>
          <div className="space-y-4 text-sm">
            <div>
              <p className="font-medium text-vault-text">La tache ne s'execute pas</p>
              <p className="text-vault-text-secondary mt-1">
                Verifiez que la tache est activee (switch vert). Verifiez aussi que vous avez
                suffisamment de tokens Keepa.
              </p>
            </div>
            <div>
              <p className="font-medium text-vault-text">Resultats vides</p>
              <p className="text-vault-text-secondary mt-1">
                La recherche peut ne rien retourner si les criteres sont trop restrictifs.
                Elargissez les filtres BSR ou ROI.
              </p>
            </div>
            <div>
              <p className="font-medium text-vault-text">Trop de tokens consommes</p>
              <p className="text-vault-text-secondary mt-1">
                Reduisez le nombre de taches ou leur frequence. Privilegiez les recherches
                ciblees plutot que larges.
              </p>
            </div>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
