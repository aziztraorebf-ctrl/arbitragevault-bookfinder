import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'

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
      <div className="min-h-screen bg-gray-50">
        <Layout>
          <Dashboard />
        </Layout>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            className: 'bg-white shadow-lg border',
          }}
        />
      </div>
    </QueryClientProvider>
  )
}

export default App
