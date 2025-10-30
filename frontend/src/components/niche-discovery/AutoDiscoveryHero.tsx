/**
 * Auto-Discovery Hero Section
 * Big "Surprise Me!" button for one-click niche discovery
 */

interface AutoDiscoveryHeroProps {
  onExplore: () => void
  isLoading: boolean
  lastExploration?: Date
}

export function AutoDiscoveryHero({
  onExplore,
  isLoading,
  lastExploration,
}: AutoDiscoveryHeroProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 p-8 text-white shadow-2xl">
      {/* Animated background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent)]"></div>
      </div>

      <div className="relative z-10">
        {/* Title */}
        <h2 className="text-4xl font-bold mb-2 flex items-center gap-3">
          <span className="text-5xl">🚀</span>
          <span>Explorer les niches du moment</span>
        </h2>

        {/* Subtitle */}
        <p className="text-white/90 text-lg mb-6 max-w-2xl">
          Découvrez <strong>3 niches rentables</strong> validées avec vraies données
          Keepa en temps réel. Chaque niche contient des produits avec ROI ≥30% et
          vélocité ≥60.
        </p>

        {/* CTA Button */}
        <button
          onClick={onExplore}
          disabled={isLoading}
          className="px-8 py-4 bg-white text-purple-600 rounded-lg font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-3"
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <span>Exploration en cours...</span>
            </>
          ) : (
            <>
              <span className="text-2xl">🎲</span>
              <span>Surprise Me!</span>
            </>
          )}
        </button>

        {/* Last exploration timestamp */}
        {lastExploration && !isLoading && (
          <p className="text-white/70 text-sm mt-3">
            Dernière exploration :{' '}
            {lastExploration.toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
    </div>
  )
}
