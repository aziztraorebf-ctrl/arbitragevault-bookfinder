import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronLeft, Search, TrendingUp, BookOpen, X } from 'lucide-react'

interface WelcomeWizardProps {
  onComplete: () => void
}

interface Step {
  title: string
  description: string
  icon: React.ReactNode
  action?: {
    label: string
    href: string
  }
}

const steps: Step[] = [
  {
    title: 'Bienvenue sur ArbitrageVault',
    description: 'Decouvrez des opportunites de livres rentables en quelques clics. Ce guide vous montre comment utiliser les fonctionnalites principales.',
    icon: <BookOpen className="w-16 h-16 text-blue-500" />,
  },
  {
    title: 'Decouvrez des Niches',
    description: 'Utilisez Niche Discovery pour trouver des categories de livres avec un bon potentiel de profit. Filtrez par ROI, velocite et prix.',
    icon: <Search className="w-16 h-16 text-purple-500" />,
    action: {
      label: 'Aller a Niche Discovery',
      href: '/niche-discovery',
    },
  },
  {
    title: 'Analysez vos Resultats',
    description: 'Consultez vos recherches sauvegardees dans Mes Recherches. Verifiez les produits interessants avant de les sourcer.',
    icon: <TrendingUp className="w-16 h-16 text-green-500" />,
    action: {
      label: 'Voir Mes Recherches',
      href: '/recherches',
    },
  },
]

export function WelcomeWizard({ onComplete }: WelcomeWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const isLastStep = currentStep === steps.length - 1
  const step = steps[currentStep]

  const handleNext = () => {
    if (isLastStep) {
      onComplete()
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(0, prev - 1))
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <span className="text-sm text-gray-500">
            Etape {currentStep + 1} / {steps.length}
          </span>
          <button
            onClick={onComplete}
            className="text-gray-400 hover:text-gray-600 p-1"
            aria-label="Passer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-8 text-center">
          <div className="flex justify-center mb-6">
            {step.icon}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {step.title}
          </h2>
          <p className="text-gray-600 mb-6">
            {step.description}
          </p>
          {step.action && (
            <Link
              to={step.action.href}
              onClick={onComplete}
              className="inline-block px-6 py-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors mb-4"
            >
              {step.action.label}
            </Link>
          )}
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 pb-4">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentStep ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center gap-1 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Retour
          </button>
          <button
            onClick={onComplete}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Passer
          </button>
          <button
            onClick={handleNext}
            className="flex items-center gap-1 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            {isLastStep ? 'Commencer' : 'Suivant'}
            {!isLastStep && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  )
}
