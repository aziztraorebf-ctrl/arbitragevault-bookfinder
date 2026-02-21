/**
 * Auto-Discovery Hero Section
 * Strategic buttons for Textbook Standard and Textbook Patience
 * Phase 8: Dual Template Strategy - Vault Elegance Design
 */

import { BookOpen, Zap, Clock } from 'lucide-react'
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
  icon: 'zap' | 'clock'
  description: string
}> = [
  {
    strategy: 'textbooks_standard',
    label: 'Textbook Standard',
    subtitle: 'BSR 100K-250K',
    icon: 'zap',
    description: 'Rotation 2-4 semaines. Equilibre profit/velocite.',
  },
  {
    strategy: 'textbooks_patience',
    label: 'Textbook Patience',
    subtitle: 'BSR 250K-400K',
    icon: 'clock',
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
    <div className="bg-gradient-to-r from-vault-accent to-vault-accent-dark rounded-2xl p-6 md:p-8 shadow-vault-md border border-vault-accent/20">
      <div className="relative z-10">
        {/* Title */}
        <h2 className="text-2xl md:text-3xl font-display font-semibold text-white flex items-center gap-3">
          <BookOpen className="w-8 h-8" />
          <span>Strategie Textbook</span>
        </h2>

        {/* Subtitle */}
        <p className="text-white/90 text-sm md:text-base mt-3 max-w-2xl">
          Choisissez votre strategie : <strong>Standard</strong> pour rotation moderee (2-4 sem)
          ou <strong>Patience</strong> pour profit eleve (4-8 semaines).
          Validee avec vraies donnees Keepa en temps reel.
        </p>

        {/* Strategy Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mt-6">
          {STRATEGY_BUTTONS.map((btn) => {
            const isThisLoading = isLoading && loadingStrategy === btn.strategy
            const isDisabled = isLoading
            const isStandard = btn.strategy === 'textbooks_standard'
            const IconComponent = btn.icon === 'zap' ? Zap : Clock

            return (
              <button
                key={btn.strategy}
                onClick={() => onExplore(btn.strategy)}
                disabled={isDisabled}
                className={`
                  flex-1 px-6 py-4 rounded-xl font-semibold
                  ${isStandard
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-amber-600 hover:bg-amber-700'
                  }
                  text-white shadow-lg hover:shadow-xl
                  transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed
                  flex flex-col items-center gap-2
                `}
              >
                {isThisLoading ? (
                  <>
                    <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full" />
                    <span className="text-sm">Exploration...</span>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <IconComponent className="w-5 h-5" />
                      <span>{btn.label}</span>
                    </div>
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
