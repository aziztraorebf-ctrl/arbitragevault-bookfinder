import { TrendingUp, BookOpen, Target, Activity } from 'lucide-react'

const stats = [
  {
    title: "Opportunités trouvées",
    value: "847",
    change: "+12%",
    changeType: "positive",
    icon: BookOpen,
    gradient: "from-primary-500 to-primary-600"
  },
  {
    title: "Opportunité du jour",
    value: "ROI 42%",
    subtitle: "Analyse manuelle (CSV / ASIN)",
    change: "00:06:02:05",
    changeType: "neutral",
    icon: Target,
    gradient: "from-primary-400 to-accent-500"
  },
  {
    title: "Score moyen",
    value: "108982",
    subtitle: "Score d'opportunités (CSV / ASIN)",
    change: "09:11m:56s",
    changeType: "positive",
    icon: TrendingUp,
    gradient: "from-success-500 to-success-600"
  }
]

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="gradient-bg rounded-2xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Bienvenue sur ArbitrageVault</h2>
        <p className="text-blue-100 text-lg">
          Découvrez des opportunités d'arbitrage rentables avec notre plateforme d'analyse automatisée
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="card p-6 hover:shadow-xl transition-shadow duration-200">
              <div className={`w-16 h-16 bg-gradient-to-br ${stat.gradient} rounded-2xl flex items-center justify-center mb-4`}>
                <Icon className="w-8 h-8 text-white" />
              </div>
              
              <h3 className="text-gray-600 text-sm font-medium mb-1">{stat.title}</h3>
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-2xl font-bold text-gray-900">{stat.value}</span>
                <button className="p-2 hover:bg-gray-50 rounded-full transition-colors">
                  <Activity className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              
              {stat.subtitle && (
                <p className="text-sm text-gray-500 mb-2">{stat.subtitle}</p>
              )}
              
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${
                  stat.changeType === 'positive' ? 'text-success-600' : 
                  stat.changeType === 'negative' ? 'text-red-600' : 
                  'text-gray-500'
                }`}>
                  {stat.change}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Analyse Manuelle Card */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Analyse manuelle</h3>
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-primary-600" />
            </div>
          </div>
          <p className="text-gray-600 mb-4">
            Analysez vos produits en uploadant un fichier CSV ou en saisissant des ASINs manuellement.
          </p>
          <button className="btn-primary w-full">
            Commencer l'analyse
          </button>
        </div>

        {/* AutoSourcing Card */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">AutoSourcing</h3>
            <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
              <Target className="w-5 h-5 text-success-600" />
            </div>
          </div>
          <p className="text-gray-600 mb-4">
            Découvrez automatiquement de nouvelles opportunités basées sur vos critères.
          </p>
          <button className="btn-success w-full">
            Lancer une recherche
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Activité récente</h3>
        <div className="space-y-4">
          {[
            { action: "Analyse terminée", details: "47 produits analysés - ROI moyen: 35%", time: "Il y a 2h" },
            { action: "Nouvelle niche découverte", details: "Engineering & Transportation - Score: 89", time: "Il y a 4h" },
            { action: "AutoScheduler activé", details: "Prochaine exécution: 15:00", time: "Il y a 6h" }
          ].map((item, index) => (
            <div key={index} className="flex items-start space-x-4 p-3 hover:bg-gray-50 rounded-lg">
              <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{item.action}</p>
                <p className="text-sm text-gray-600">{item.details}</p>
              </div>
              <span className="text-xs text-gray-500">{item.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}