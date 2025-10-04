import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Error Boundary Component - Pattern React officiel
 * Capture les erreurs pendant le rendu et affiche un fallback UI
 * 
 * Usage:
 * <ErrorBoundary>
 *   <ComponentQuiPeutCrash />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Mise à jour du state pour afficher le fallback UI
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log l'erreur (développement) ou envoyer à service monitoring (production)
    if (import.meta.env.MODE === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }

    // Callback optionnel pour logging externe
    this.props.onError?.(error, errorInfo)

    this.setState({
      error,
      errorInfo
    })
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // Fallback UI custom ou par défaut
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full">
            <div className="bg-white rounded-lg shadow-lg border border-red-200 p-6">
              {/* Header */}
              <div className="flex items-center mb-4">
                <AlertTriangle className="w-8 h-8 text-red-500 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    Une erreur s'est produite
                  </h2>
                  <p className="text-sm text-gray-600">
                    L'application a rencontré un problème inattendu
                  </p>
                </div>
              </div>

              {/* Error Message */}
              {this.state.error && (
                <div className="mb-4 p-3 bg-red-50 rounded border border-red-200">
                  <p className="text-sm text-red-700 font-medium mb-1">
                    Message d'erreur :
                  </p>
                  <p className="text-sm text-red-600 font-mono">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              {/* Debug Info (Development Only) */}
              {import.meta.env.MODE === 'development' && this.state.errorInfo && (
                <details className="mb-4">
                  <summary className="text-sm text-gray-700 cursor-pointer hover:text-gray-900 mb-2">
                    Détails techniques (développement)
                  </summary>
                  <div className="p-3 bg-gray-100 rounded border border-gray-300 overflow-x-auto">
                    <pre className="text-xs text-gray-800">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </div>
                </details>
              )}

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={this.handleReset}
                  className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Réessayer
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
                >
                  Retour à l'accueil
                </button>
              </div>

              {/* Help Text */}
              <p className="mt-4 text-xs text-gray-500 text-center">
                Si le problème persiste, veuillez contacter le support ou vérifier votre connexion.
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
