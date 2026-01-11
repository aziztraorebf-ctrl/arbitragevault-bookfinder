import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/auth'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import { WelcomeWizard } from './components/onboarding/WelcomeWizard'
import { useOnboarding } from './hooks/useOnboarding'

// Import des pages
import AuthPage from './pages/Auth'
import AnalyseManuelle from './pages/AnalyseManuelle'
import NicheDiscovery from './pages/NicheDiscovery'
import MesNiches from './pages/MesNiches'
import AutoScheduler from './pages/AutoScheduler'
import AutoSourcing from './pages/AutoSourcing'
import Configuration from './pages/Configuration'
import MesRecherches from './pages/MesRecherches'
import RechercheDetail from './pages/RechercheDetail'

// Import documentation pages
import DocsIndex from './pages/docs/index'
import GettingStarted from './pages/docs/GettingStarted'
import SearchDocs from './pages/docs/SearchDocs'
import AnalysisDocs from './pages/docs/AnalysisDocs'
import SavedProductsDocs from './pages/docs/SavedProductsDocs'
import GlossaryDocs from './pages/docs/GlossaryDocs'
import TroubleshootingDocs from './pages/docs/TroubleshootingDocs'
import SchedulerDocs from './pages/docs/SchedulerDocs'
import SourcingDocs from './pages/docs/SourcingDocs'
import DailyReviewDocs from './pages/docs/DailyReviewDocs'

// Initialize React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function ProtectedAppContent() {
  const { showWizard, isLoading, completeOnboarding } = useOnboarding()

  if (isLoading) {
    return null
  }

  return (
    <>
      {showWizard && <WelcomeWizard onComplete={completeOnboarding} />}
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analyse" element={<AnalyseManuelle />} />
          <Route path="/niche-discovery" element={<NicheDiscovery />} />
          <Route path="/mes-niches" element={<MesNiches />} />
          <Route path="/autoscheduler" element={<AutoScheduler />} />
          <Route path="/autosourcing" element={<AutoSourcing />} />
          <Route path="/config" element={<Configuration />} />
          <Route path="/recherches" element={<MesRecherches />} />
          <Route path="/recherches/:id" element={<RechercheDetail />} />
          {/* Documentation routes */}
          <Route path="/docs" element={<DocsIndex />} />
          <Route path="/docs/getting-started" element={<GettingStarted />} />
          <Route path="/docs/search" element={<SearchDocs />} />
          <Route path="/docs/analysis" element={<AnalysisDocs />} />
          <Route path="/docs/saved-products" element={<SavedProductsDocs />} />
          <Route path="/docs/glossary" element={<GlossaryDocs />} />
          <Route path="/docs/troubleshooting" element={<TroubleshootingDocs />} />
          <Route path="/docs/scheduler" element={<SchedulerDocs />} />
          <Route path="/docs/sourcing" element={<SourcingDocs />} />
          <Route path="/docs/daily-review" element={<DailyReviewDocs />} />
          {/* Fallback route */}
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </Layout>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: 'bg-white shadow-lg border',
        }}
      />
    </>
  )
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public route - Auth page */}
      <Route path="/auth" element={<AuthPage />} />

      {/* Protected routes - everything else */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <ProtectedAppContent />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
