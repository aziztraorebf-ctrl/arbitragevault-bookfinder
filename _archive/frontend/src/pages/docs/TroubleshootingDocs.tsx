// Troubleshooting Documentation
import DocsLayout from './DocsLayout'

interface Problem {
  title: string
  symptoms: string[]
  solutions: string[]
}

const problems: Problem[] = [
  {
    title: 'La recherche ne retourne aucun resultat',
    symptoms: [
      'Message "Aucun produit trouve"',
      'La page reste vide apres la recherche',
    ],
    solutions: [
      'Verifiez que l\'ASIN est correct (10 caracteres, commence par B)',
      'Verifiez que le produit existe sur Amazon US (pas .ca, .fr, etc.)',
      'Essayez un autre ASIN pour confirmer que le systeme fonctionne',
      'Attendez 2-3 minutes et reessayez (l\'API peut etre surchargee)',
    ],
  },
  {
    title: 'Erreur "Timeout" ou "Request failed"',
    symptoms: [
      'Message d\'erreur rouge',
      'Chargement qui n\'aboutit pas',
    ],
    solutions: [
      'Verifiez votre connexion internet',
      'Attendez 1-2 minutes et reessayez',
      'L\'API Keepa peut etre temporairement indisponible',
      'Verifiez que vous n\'avez pas depasse votre quota de tokens Keepa',
    ],
  },
  {
    title: 'Les donnees semblent incorrectes',
    symptoms: [
      'ROI anormalement eleve (>200%)',
      'Prix qui ne correspondent pas a Amazon',
      'BSR affiche comme "N/A"',
    ],
    solutions: [
      'Verifiez manuellement sur Amazon pour confirmer',
      'Le produit peut etre nouveau avec peu d\'historique',
      'Les prix peuvent avoir change depuis la derniere mise a jour Keepa',
      'Certains produits ont des donnees Keepa incompletes',
    ],
  },
  {
    title: 'Je ne peux pas me connecter',
    symptoms: [
      'Page de connexion qui boucle',
      'Message "Invalid credentials"',
    ],
    solutions: [
      'Verifiez votre email et mot de passe',
      'Utilisez "Mot de passe oublie" pour reinitialiser',
      'Videz le cache de votre navigateur',
      'Essayez un autre navigateur',
    ],
  },
  {
    title: 'La page est blanche ou ne charge pas',
    symptoms: [
      'Ecran blanc apres connexion',
      'Erreur "Something went wrong"',
    ],
    solutions: [
      'Rafraichissez la page (F5 ou Ctrl+R)',
      'Videz le cache du navigateur',
      'Verifiez que JavaScript est active',
      'Essayez un autre navigateur (Chrome recommande)',
    ],
  },
  {
    title: 'Les bookmarks ne se sauvegardent pas',
    symptoms: [
      'Le produit n\'apparait pas dans Bookmarks',
      'Message d\'erreur lors de la sauvegarde',
    ],
    solutions: [
      'Verifiez que vous etes bien connecte',
      'Rafraichissez la page et reessayez',
      'Le produit est peut-etre deja sauvegarde',
      'Verifiez votre connexion internet',
    ],
  },
  {
    title: 'L\'application est lente',
    symptoms: [
      'Chargement long entre les pages',
      'Recherches qui prennent plus d\'une minute',
    ],
    solutions: [
      'Une recherche normale prend 30-60 secondes (c\'est normal)',
      'Verifiez votre connexion internet',
      'Fermez les autres onglets consommateurs de memoire',
      'L\'API Keepa peut etre surchargee aux heures de pointe',
    ],
  },
]

export default function TroubleshootingDocs() {
  return (
    <DocsLayout
      title="Troubleshooting"
      description="Solutions aux problemes courants"
    >
      <div className="space-y-8">
        {/* Intro */}
        <section>
          <p className="text-vault-text-secondary">
            Cette page liste les problemes les plus frequents et leurs solutions.
            Si votre probleme n'est pas liste ici, contactez le support.
          </p>
        </section>

        {/* Problems List */}
        <section className="space-y-6">
          {problems.map((problem, index) => (
            <div
              key={index}
              className="bg-vault-bg rounded-xl border border-vault-border overflow-hidden"
            >
              <div className="bg-vault-card px-4 py-3 border-b border-vault-border">
                <h3 className="font-semibold text-vault-text">
                  {problem.title}
                </h3>
              </div>
              <div className="p-4 space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-vault-text-secondary mb-2">
                    Symptomes:
                  </h4>
                  <ul className="space-y-1">
                    {problem.symptoms.map((symptom, i) => (
                      <li key={i} className="text-sm text-vault-text-secondary flex items-start gap-2">
                        <span className="text-red-400">-</span>
                        {symptom}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-vault-text-secondary mb-2">
                    Solutions:
                  </h4>
                  <ol className="space-y-1">
                    {problem.solutions.map((solution, i) => (
                      <li key={i} className="text-sm text-vault-text-secondary flex items-start gap-2">
                        <span className="text-green-400 font-medium">{i + 1}.</span>
                        {solution}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </div>
          ))}
        </section>

        {/* Still Need Help */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-3">
            Toujours besoin d'aide?
          </h2>
          <div className="text-vault-text-secondary space-y-3">
            <p>
              Si votre probleme persiste apres avoir essaye les solutions ci-dessus:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Notez le message d'erreur exact (capture d'ecran si possible)</li>
              <li>Notez les etapes qui ont mene au probleme</li>
              <li>Notez votre navigateur et systeme d'exploitation</li>
              <li>Contactez le support avec ces informations</li>
            </ol>
          </div>
        </section>

        {/* Quick Checks */}
        <section>
          <h2 className="text-xl font-semibold text-vault-text mb-4">
            Verifications rapides
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Navigateur</h3>
              <p className="text-sm text-vault-text-secondary">
                Chrome ou Firefox derniere version recommandes.
                Safari et Edge supportes mais moins testes.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">JavaScript</h3>
              <p className="text-sm text-vault-text-secondary">
                JavaScript doit etre active.
                Les bloqueurs de pub peuvent interferer.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Cache</h3>
              <p className="text-sm text-vault-text-secondary">
                Ctrl+Shift+R pour forcer le rafraichissement
                sans cache si la page semble buguee.
              </p>
            </div>
            <div className="bg-vault-bg rounded-lg p-4 border border-vault-border">
              <h3 className="font-medium text-vault-text mb-2">Connexion</h3>
              <p className="text-sm text-vault-text-secondary">
                Une connexion stable est necessaire.
                Evitez les VPN si possible.
              </p>
            </div>
          </div>
        </section>
      </div>
    </DocsLayout>
  )
}
