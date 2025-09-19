import { ArrowRight } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* KPI Stats avec Identité Couleur */}
      <div className="quick-stats">
        <div className="stat-item">
          <div className="stat-number color-blue">847</div>
          <div className="stat-label">Total Opportunités</div>
          <div className="text-xs color-blue mt-1">📦 Découvertes brutes</div>
        </div>
        <div className="stat-item">
          <div className="stat-number color-violet">42%</div>
          <div className="stat-label">ROI Moyen</div>
          <div className="text-xs color-violet mt-1">📊 Analyses calculées</div>
        </div>
        <div className="stat-item">
          <div className="stat-number color-green">15</div>
          <div className="stat-label">Niches Actives</div>
          <div className="text-xs color-green mt-1">✅ Résultats validés</div>
        </div>
      </div>

      {/* Stats Cards - Exact Mockup Match */}
      <div className="dashboard-cards-grid">
        {/* Card 1: Opportunités trouvées (Blue - Découvertes) */}
        <div className="dashboard-card-blue">
          <div>
            <div className="text-4xl mb-4">📦</div>
            <div className="typography-h2 text-white mb-2">Opportunités</div>
            <div className="text-2xl font-bold text-white mb-2">ASI1 B85NG</div>
            <div className="typography-body text-blue-100">Découvertes brutes</div>
          </div>
          <div className="typography-secondary text-blue-100 mt-auto">
            Scan: 00:06:02:05
          </div>
          <button className="card-arrow-button">
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Card 2: Opportunité du jour (Violet - Analyses) */}
        <div className="dashboard-card-purple">
          <div>
            <div className="text-4xl mb-4">📊</div>
            <div className="typography-h2 text-white mb-2">Opportunité du jour</div>
            <div className="typography-h3 text-purple-100 mb-4">
              Analyse manuelle<br />
              (CSV / ASIN)
            </div>
            <div className="typography-body text-purple-100">Analyses & scores</div>
          </div>
          <div className="typography-secondary text-purple-100 mt-auto">
            Dernière analyse: 00:06:02:05
          </div>
          <button className="card-arrow-button">
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Card 3: Score du jour (Vert - Validé) */}
        <div className="dashboard-card-green">
          <div>
            <div className="text-4xl mb-4">✅</div>
            <div className="typography-h2 text-white mb-2">108982 du jour</div>
            <div className="typography-h3 text-green-100 mb-4">
              Score d'opportunités<br />
              (CSV / ASIN)
            </div>
            <div className="typography-body text-green-100">Résultats validés</div>
          </div>
          <div className="typography-secondary text-green-100 mt-auto">
            Validation: 09:11m:56s
          </div>
          <button className="card-arrow-button">
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Profile Section */}
      <div className="flex items-center justify-between mb-6">
        <div className="typography-body">
          Profil actif : <span className="font-semibold color-violet">Conservative</span>
        </div>
        <div className="typography-secondary">
          Dernier scan : -24 jours / 10:12
        </div>
      </div>

      {/* Activité Récente - Full Width + Optimized */}
      <div className="card p-8">
        <h2 className="typography-h2 mb-6">Activité Récente</h2>
        <div className="space-y-1">
          {[
            { 
              action: "Analyse terminée", 
              details: "47 produits analysés - ROI moyen: 35%", 
              time: "Il y a 2h",
              color: "green",
              icon: "✅"
            },
            { 
              action: "Nouvelle niche découverte", 
              details: "Engineering & Transportation - Score: 89", 
              time: "Il y a 4h",
              color: "blue", 
              icon: "📦"
            },
            { 
              action: "AutoScheduler activé", 
              details: "Prochaine exécution: 15:00", 
              time: "Il y a 6h",
              color: "orange",
              icon: "⚙️"
            },
            { 
              action: "Opportunité à fort ROI", 
              details: "B08N5WRWNW - ROI estimé: 58%", 
              time: "Il y a 8h",
              color: "green",
              icon: "✅"
            },
            { 
              action: "Stock vérifié", 
              details: "15 produits - Disponibilité confirmée", 
              time: "Il y a 10h",
              color: "blue",
              icon: "📦"
            },
            { 
              action: "Niche bookmark ajoutée", 
              details: "Health & Personal Care sauvegardée", 
              time: "Il y a 12h",
              color: "violet",
              icon: "📊"
            }
          ].map((item, index) => (
            <div key={index}>
              <div className="flex items-start space-x-4 p-4 hover:bg-gray-50 rounded-xl transition-colors">
                <div className="text-lg mt-1">{item.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="typography-h3" style={{fontWeight: 600, color: '#111827'}}>{item.action}</h3>
                    <span className="typography-secondary">{item.time}</span>
                  </div>
                  <p className="typography-body mt-1">{item.details}</p>
                </div>
              </div>
              {index < 5 && <div className="border-t border-gray-100 ml-12"></div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}