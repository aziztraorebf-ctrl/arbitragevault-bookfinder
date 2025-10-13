export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* KPI 1: Analyses ce mois */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">📈</span>
            <span className="text-gray-500 text-sm">Analyses ce mois</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">1 247</div>
          <div className="text-sm text-gray-500 mt-1">produits</div>
        </div>

        {/* KPI 2: Niches découvertes */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">🔍</span>
            <span className="text-gray-500 text-sm">Niches découvertes</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">89</div>
          <div className="text-sm text-gray-500 mt-1">niches actives</div>
        </div>

        {/* KPI 3: ROI moyen */}
        <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-start justify-center">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-xl">💰</span>
            <span className="text-gray-500 text-sm">ROI moyen</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">43,2 %</div>
        </div>
      </div>

      {/* Row 2: Section Title */}
      <div>
        <h2 className="text-xl font-semibold text-gray-700">Actions Rapides</h2>
      </div>

      {/* Row 3: Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Analyser Manuellement */}
        <div className="h-56 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200">
          <div className="text-4xl">📄</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Analyser<br />Manuellement
            </h3>
            <p className="text-sm text-white/80">
              (CSV/ASINs)
            </p>
          </div>
        </div>

        {/* Card 2: Découvrir */}
        <div className="h-56 bg-gradient-to-br from-purple-500 to-purple-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200">
          <div className="text-4xl">🔍</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Découvrir
            </h3>
            <p className="text-sm text-white/80">
              Nouvelles Niches
            </p>
          </div>
        </div>

        {/* Card 3: Mes Niches */}
        <div className="h-56 bg-gradient-to-br from-green-500 to-green-600 rounded-3xl text-white p-8 flex flex-col justify-between cursor-pointer hover:shadow-xl transition-shadow duration-200">
          <div className="text-4xl">📚</div>
          <div>
            <h3 className="text-xl font-bold mb-2">
              Mes Niches
            </h3>
            <p className="text-sm text-white/80">
              Sauvegardées<br />
              (23)
            </p>
          </div>
        </div>
      </div>

      {/* Row 4: Footer Stats */}
      <div className="mt-12 pt-4 border-t border-gray-100 text-center">
        <div className="flex items-center justify-center gap-8 text-gray-500 text-sm py-4">
          <div>
            <span className="font-medium">AutoScheduler:</span> <span className="text-green-600 font-semibold">ACTIF</span>
          </div>
          <div className="text-gray-300">•</div>
          <div>
            <span className="font-medium">Stock validé:</span> 892 produits
          </div>
        </div>
      </div>
    </div>
  )
}