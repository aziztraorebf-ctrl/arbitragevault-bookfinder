// Getting Started - Premier Lancement
import DocsLayout from './DocsLayout'

export default function GettingStarted() {
  return (
    <DocsLayout
      title="Premier Lancement"
      description="Tout ce dont vous avez besoin pour commencer"
    >
      <div className="space-y-8">
        {/* Intro */}
        <section>
          <p className="text-vault-text-secondary text-lg">
            Ce guide vous accompagne dans vos premiers pas avec ArbitrageVault.
            En 5 minutes, vous serez pret a trouver vos premieres opportunites.
          </p>
        </section>

        {/* Step 1 */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">
              1
            </span>
            Connexion
          </h2>
          <div className="pl-10 space-y-3 text-vault-text-secondary">
            <p>
              Connectez-vous avec votre compte email. Si vous n'avez pas de compte,
              creez-en un en cliquant sur "S'inscrire".
            </p>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <p className="text-sm">
                <strong className="text-vault-text">Conseil:</strong> Utilisez une adresse email
                que vous consultez regulierement pour recevoir les notifications.
              </p>
            </div>
          </div>
        </section>

        {/* Step 2 */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">
              2
            </span>
            Premiere Recherche
          </h2>
          <div className="pl-10 space-y-3 text-vault-text-secondary">
            <p>
              Allez dans <strong className="text-vault-text">Analytics</strong> depuis le menu lateral.
            </p>
            <ol className="list-decimal list-inside space-y-2">
              <li>Entrez un ASIN Amazon (ex: B08N5WRWNW) ou un mot-cle</li>
              <li>Cliquez sur <strong className="text-vault-text">Analyser</strong></li>
              <li>Attendez 30-60 secondes pour les resultats</li>
            </ol>
          </div>
        </section>

        {/* Step 3 */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">
              3
            </span>
            Comprendre les Resultats
          </h2>
          <div className="pl-10 space-y-3 text-vault-text-secondary">
            <p>
              Chaque produit affiche des metriques cles:
            </p>
            <ul className="space-y-2">
              <li>
                <strong className="text-vault-text">ROI (Return on Investment):</strong>{' '}
                Pourcentage de profit potentiel. Plus de 30% = interessant.
              </li>
              <li>
                <strong className="text-vault-text">BSR (Best Seller Rank):</strong>{' '}
                Classement de vente. Moins de 50,000 = vente rapide.
              </li>
              <li>
                <strong className="text-vault-text">Velocity Score:</strong>{' '}
                Vitesse de vente estimee. Plus de 70 = excellent.
              </li>
            </ul>
          </div>
        </section>

        {/* Step 4 */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-vault-accent text-white flex items-center justify-center text-sm font-bold">
              4
            </span>
            Sauvegarder un Produit
          </h2>
          <div className="pl-10 space-y-3 text-vault-text-secondary">
            <p>
              Quand vous trouvez un produit interessant:
            </p>
            <ol className="list-decimal list-inside space-y-2">
              <li>Cliquez sur l'icone <strong className="text-vault-text">Bookmark</strong></li>
              <li>Le produit est ajoute a vos favoris</li>
              <li>Retrouvez-le dans <strong className="text-vault-text">Bookmarks</strong></li>
            </ol>
          </div>
        </section>

        {/* What's Next */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-3">
            Et maintenant?
          </h2>
          <ul className="space-y-2 text-vault-text-secondary">
            <li>
              - Explorez le <strong className="text-vault-text">Dashboard</strong> pour voir un resume de votre activite
            </li>
            <li>
              - Configurez vos criteres dans <strong className="text-vault-text">Settings</strong>
            </li>
            <li>
              - Consultez le <strong className="text-vault-text">Glossaire</strong> pour comprendre tous les termes
            </li>
          </ul>
        </section>
      </div>
    </DocsLayout>
  )
}
