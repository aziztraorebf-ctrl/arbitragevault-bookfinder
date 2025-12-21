/**
 * Auto-Discovery Hero Section
 * Strategic buttons for Textbook Standard and Textbook Patience
 * Phase 8: Dual Template Strategy
 */

import type { NicheStrategy } from '../../services/nicheDiscoveryService'

interface AutoDiscoveryHeroProps {
  onExplore: (strategy: NicheStrategy) => void
  isLoading: boolean
  loadingStrategy?: NicheStrategy
  lastExploration?: Date
}

// Strategy button configurations
const STRATEGY_BUTTONS: Array<{
  strategy: NicheStrategy
  label: string
  subtitle: string
  icon: string
  gradient: string
  hoverGradient: string
  description: string
}> = [
  {
    strategy: 'textbooks_standard',
    label: 'Textbook Standard',
    subtitle: 'BSR 100K-250K',
    icon: 'BOOKS',
    gradient: 'from-green-500 to-emerald-600',
    hoverGradient: 'hover:from-green-600 hover:to-emerald-700',
    description: 'Rotation 2-4 semaines. Equilibre profit/velocite.',
  },
  {
    strategy: 'textbooks_patience',
    label: 'Textbook Patience',
    subtitle: 'BSR 250K-400K',
    icon: 'CLOCK',
    gradient: 'from-amber-500 to-orange-600',
    hoverGradient: 'hover:from-amber-600 hover:to-orange-700',
    description: 'Rotation 4-8 semaines. Profit plus eleve, capital immobilise.',
  },
]

export function AutoDiscoveryHero({
  onExplore,
  isLoading,
  loadingStrategy,
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
        <h2 className="text-3xl md:text-4xl font-bold mb-2 flex items-center gap-3">
          <span className="text-4xl md:text-5xl">BOOKS</span>
          <span>Strategie Textbook</span>
        </h2>

        {/* Subtitle */}
        <p className="text-white/90 text-lg mb-6 max-w-2xl">
          Choisissez votre strategie : <strong>Standard</strong> pour rotation moderee (2-4 sem)
          ou <strong>Patience</strong> pour profit eleve (4-8 semaines).
          Validee avec vraies donnees Keepa en temps reel.
        </p>

        {/* Strategy Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          {STRATEGY_BUTTONS.map((btn) => {
            const isThisLoading = isLoading && loadingStrategy === btn.strategy
            const isDisabled = isLoading

            return (
              <button
                key={btn.strategy}
                onClick={() => onExplore(btn.strategy)}
                disabled={isDisabled}
                className={`
                  flex-1 px-6 py-4 bg-gradient-to-r ${btn.gradient} ${btn.hoverGradient}
                  rounded-lg font-bold text-lg shadow-lg hover:shadow-xl
                  hover:scale-105 transition-all
                  disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
                  flex flex-col items-center gap-1 text-white
                `}
              >
                {isThisLoading ? (
                  <>
                    <svg
                      className="animate-spin h-6 w-6"
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
                    <span className="text-sm">Exploration...</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl">{btn.icon}</span>
                    <span>{btn.label}</span>
                    <span className="text-xs font-normal opacity-90">
                      {btn.subtitle}
                    </span>
                  </>
                )}
              </button>
            )
          })}
        </div>

        {/* Strategy descriptions */}
        <div className="mt-4 grid sm:grid-cols-2 gap-4 text-sm text-white/80">
          {STRATEGY_BUTTONS.map((btn) => (
            <div key={btn.strategy} className="flex items-start gap-2">
              <span className="text-white/60">*</span>
              <span>
                <strong>{btn.label}:</strong> {btn.description}
              </span>
            </div>
          ))}
        </div>

        {/* Last exploration timestamp */}
        {lastExploration && !isLoading && (
          <p className="text-white/70 text-sm mt-4">
            Derniere exploration :{' '}
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
