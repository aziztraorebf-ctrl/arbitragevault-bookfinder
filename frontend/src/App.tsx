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
import AutoScheduler from './pages/AutoScheduler'
import AutoSourcing from './pages/AutoSourcing'
import Configuration from './pages/Configuration'

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
          <Route path="/autoscheduler" element={<AutoScheduler />} />
          <Route path="/autosourcing" element={<AutoSourcing />} />
          <Route path="/config" element={<Configuration />} />
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
