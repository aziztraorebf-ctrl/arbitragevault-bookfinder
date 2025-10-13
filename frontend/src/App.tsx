import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'

// Import des pages
import AnalyseManuelle from './pages/AnalyseManuelle'
import NicheDiscovery from './pages/NicheDiscovery'
import MesNiches from './pages/MesNiches'
import AutoScheduler from './pages/AutoScheduler'
import AutoSourcing from './pages/AutoSourcing'
import AnalyseStrategique from './pages/AnalyseStrategique'
import StockEstimates from './pages/StockEstimates'
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analyse" element={<AnalyseManuelle />} />
            <Route path="/niche-discovery" element={<NicheDiscovery />} />
            <Route path="/mes-niches" element={<MesNiches />} />
            <Route path="/autoscheduler" element={<AutoScheduler />} />
            <Route path="/autosourcing" element={<AutoSourcing />} />
            <Route path="/analyse-strategique" element={<AnalyseStrategique />} />
            <Route path="/stock-estimates" element={<StockEstimates />} />
            <Route path="/config" element={<Configuration />} />
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
      </Router>
    </QueryClientProvider>
  )
}

export default App