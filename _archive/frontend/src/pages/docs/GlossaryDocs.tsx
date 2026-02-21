// Glossary Documentation
import DocsLayout from './DocsLayout'

interface Term {
  term: string
  definition: string
  example?: string
}

const terms: Term[] = [
  {
    term: 'ASIN',
    definition: "Amazon Standard Identification Number. Identifiant unique de 10 caracteres pour chaque produit Amazon.",
    example: 'B08N5WRWNW'
  },
  {
    term: 'BSR (Best Seller Rank)',
    definition: 'Classement de vente dans une categorie. Plus le chiffre est bas, mieux le produit se vend.',
    example: 'BSR 25,000 = produit populaire'
  },
  {
    term: 'ROI (Return on Investment)',
    definition: 'Pourcentage de profit par rapport au prix d\'achat. Calcule apres deduction des frais Amazon.',
    example: 'Achat $20, Vente $35, Frais $5 = ROI 50%'
  },
  {
    term: 'FBA (Fulfillment by Amazon)',
    definition: 'Service ou Amazon stocke, emballe et expedie vos produits. Inclut le service client.',
  },
  {
    term: 'FBM (Fulfillment by Merchant)',
    definition: 'Vous gerez vous-meme le stockage et l\'expedition. Moins de frais mais plus de travail.',
  },
  {
    term: 'Velocity Score',
    definition: 'Score composite (0-100) estimant la vitesse de vente probable d\'un produit.',
    example: 'Score 85 = vente tres rapide estimee'
  },
  {
    term: 'Confidence Score',
    definition: 'Score indiquant la fiabilite des donnees. Base sur la quantite et la fraicheur des donnees Keepa.',
    example: 'Score 90% = donnees tres fiables'
  },
  {
    term: 'Keepa',
    definition: 'Service tiers qui collecte et fournit l\'historique des prix et BSR Amazon.',
  },
  {
    term: 'Arbitrage',
    definition: 'Strategie d\'achat a bas prix sur une source pour revendre plus cher sur Amazon.',
  },
  {
    term: 'Amazon on Listing',
    definition: 'Indicateur si Amazon vend directement le produit. Si oui, difficile de concurrencer.',
  },
  {
    term: 'Buy Box',
    definition: 'La "boite d\'achat" sur une fiche produit Amazon. Le vendeur qui l\'a obtient la majorite des ventes.',
  },
  {
    term: 'STABLE',
    definition: 'Classification Daily Review. Opportunite fiable vue plusieurs fois avec metriques coherentes.',
  },
  {
    term: 'JACKPOT',
    definition: 'Classification Daily Review. ROI exceptionnel (>80%) necessitant verification manuelle.',
  },
  {
    term: 'FLUKE',
    definition: 'Classification Daily Review. Produit vu une fois puis disparu, ou donnees suspectes.',
  },
  {
    term: 'REVENANT',
    definition: 'Classification Daily Review. Produit qui revient apres une absence de 24h+.',
  },
  {
    term: 'Daily Review',
    definition: 'Rapport quotidien automatise listant les meilleures opportunites du jour avec recommandations.',
  },
  {
    term: 'Niche',
    definition: 'Categorie ou segment de marche specifique pour concentrer vos recherches.',
    example: 'Textbooks, Medical, Test Prep'
  },
  {
    term: 'Sourcing',
    definition: 'Processus de recherche et selection de produits a acheter pour revente.',
  },
  {
    term: 'Tokens Keepa',
    definition: 'Credits consommes par les appels API Keepa. Chaque recherche utilise des tokens.',
  },
]

export default function GlossaryDocs() {
  return (
    <DocsLayout
      title="Glossaire"
      description="Definitions des termes techniques utilises dans ArbitrageVault"
    >
      <div className="space-y-8">
        {/* Intro */}
        <section>
          <p className="text-vault-text-secondary">
            Ce glossaire definit les termes techniques que vous rencontrerez dans ArbitrageVault
            et dans le monde de l'arbitrage Amazon en general.
          </p>
        </section>

        {/* Terms List */}
        <section>
          <div className="space-y-4">
            {terms.map((item) => (
              <div
                key={item.term}
                className="bg-vault-bg rounded-lg p-4 border border-vault-border"
              >
                <h3 className="font-semibold text-vault-text mb-2">
                  {item.term}
                </h3>
                <p className="text-vault-text-secondary text-sm">
                  {item.definition}
                </p>
                {item.example && (
                  <p className="text-sm text-vault-accent mt-2">
                    Exemple: {item.example}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Additional Resources */}
        <section className="bg-vault-accent-light/30 rounded-xl p-6 border border-vault-accent/20">
          <h2 className="text-lg font-semibold text-vault-text mb-3">
            Ressources supplementaires
          </h2>
          <ul className="space-y-2 text-vault-text-secondary text-sm">
            <li className="flex items-start gap-2">
              <span className="text-vault-accent font-bold">-</span>
              <span>Amazon Seller Central Help pour les definitions officielles</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-vault-accent font-bold">-</span>
              <span>Keepa Documentation pour comprendre les graphiques</span>
            </li>
          </ul>
        </section>
      </div>
    </DocsLayout>
  )
}
