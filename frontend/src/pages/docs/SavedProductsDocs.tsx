// Saved Products Documentation
import DocsLayout from './DocsLayout'

export default function SavedProductsDocs() {
  return (
    <DocsLayout
      title="Produits Sauvegardes"
      description="Gerez et suivez vos produits favoris"
    >
      <div className="space-y-8">
        {/* Purpose */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            A quoi ca sert
          </h2>
          <p className="text-vault-text-secondary">
            La section "Bookmarks" vous permet de sauvegarder les produits interessants
            pour les retrouver plus tard. C'est votre liste de surveillance personnelle.
          </p>
        </section>

        {/* How to Save */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Comment sauvegarder un produit
          </h2>
          <div className="space-y-4 text-vault-text-secondary">
            <ol className="list-decimal list-inside space-y-3">
              <li>
                <strong className="text-vault-text">Depuis les resultats de recherche:</strong>
                <p className="ml-6 mt-1">Cliquez sur l'icone "Bookmark" a cote du produit</p>
              </li>
              <li>
                <strong className="text-vault-text">Depuis la page detail:</strong>
                <p className="ml-6 mt-1">Cliquez sur "Ajouter aux favoris"</p>
              </li>
            </ol>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <p className="text-sm">
                <strong className="text-vault-text">Conseil:</strong> Sauvegardez les produits meme si vous
                n'achetez pas immediatement. Les prix et le BSR changent - une opportunite moyenne
                peut devenir excellente.
              </p>
            </div>
          </div>
        </section>

        {/* What You See */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Ce que vous verrez
          </h2>
          <div className="text-vault-text-secondary space-y-3">
            <p>Dans la page Bookmarks, pour chaque produit sauvegarde:</p>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Titre et image</strong> du produit</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Metriques actuelles</strong> (ROI, BSR, prix)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Date de sauvegarde</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Indicateurs de changement</strong> depuis la sauvegarde</span>
              </li>
            </ul>
          </div>
        </section>

        {/* Use Cases */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Cas d'utilisation
          </h2>
          <div className="space-y-4">
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Suivi de prix</h3>
              <p className="text-sm text-vault-text-secondary">
                Sauvegardez un produit dont le prix d'achat est trop eleve.
                Surveillez jusqu'a ce que le prix baisse pour atteindre un ROI acceptable.
              </p>
            </div>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Liste d'achat</h3>
              <p className="text-sm text-vault-text-secondary">
                Accumulez plusieurs opportunites puis achetez-les en lot
                pour optimiser vos frais de livraison.
              </p>
            </div>

            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Analyse de tendances</h3>
              <p className="text-sm text-vault-text-secondary">
                Suivez comment le BSR et le ROI evoluent dans le temps
                pour comprendre les patterns saisonniers.
              </p>
            </div>
          </div>
        </section>

        {/* Managing Bookmarks */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Gestion des favoris
          </h2>
          <div className="text-vault-text-secondary space-y-3">
            <h3 className="font-medium text-vault-text">Actions disponibles:</h3>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Trier:</strong> Par ROI, BSR, date de sauvegarde</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Filtrer:</strong> Par categorie, seuil de ROI</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Supprimer:</strong> Retirez les produits qui ne vous interessent plus</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-vault-accent font-bold">-</span>
                <span><strong className="text-vault-text">Exporter:</strong> Telechargez votre liste en CSV</span>
              </li>
            </ul>
          </div>
        </section>

        {/* Tips */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-4">
            Conseils pratiques
          </h2>
          <ul className="space-y-3 text-vault-text-secondary">
            <li className="flex items-start gap-2">
              <span className="text-vault-accent font-bold">1.</span>
              <span>
                <strong className="text-vault-text">Nettoyez regulierement:</strong> Supprimez les produits
                dont le ROI est devenu negatif ou le BSR trop eleve.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-vault-accent font-bold">2.</span>
              <span>
                <strong className="text-vault-text">Limitez-vous:</strong> Trop de favoris devient ingerable.
                Visez 20-50 produits maximum en surveillance active.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-vault-accent font-bold">3.</span>
              <span>
                <strong className="text-vault-text">Agissez vite:</strong> Une bonne opportunite ne dure pas.
                Si tous les indicateurs sont verts, achetez.
              </span>
            </li>
          </ul>
        </section>
      </div>
    </DocsLayout>
  )
}
