import { useState, useEffect } from 'react'
import AutoSourcingJobModal from '../components/AutoSourcingJobModal'
import { TokenErrorAlert } from '../components/TokenErrorAlert'
import { parseTokenError } from '../utils/tokenErrorHandler'

interface JobConfigFormData {
  profile_name: string;
  discovery_config: {
    categories: string[];
    bsr_range: [number, number];
    price_range?: [number, number];
    max_results: number;
  };
  scoring_config: {
    roi_min: number;
    velocity_min: number;
    confidence_min: number;
    rating_required: string;
    max_results: number;
  };
}

interface JobPick {
  id: string;
  asin: string;
  title: string;
  roi_percentage: number;
  velocity_score: number;
  stability_score: number;
  confidence_score: number;
  overall_rating: string;
  action_status: string;
}

interface Job {
  id: string;
  profile_name: string;
  launched_at: string;
  status: string;
  total_tested: number;
  total_selected: number;
  picks: JobPick[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://arbitragevault-backend-v2.onrender.com';

export default function AutoSourcing() {
  const [error, setError] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [tokenError, setTokenError] = useState<ReturnType<typeof parseTokenError> | null>(null)

  useEffect(() => {
    fetchRecentJobs()
  }, [])

  const fetchRecentJobs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/jobs?limit=10`)
      if (response.ok) {
        const data = await response.json()
        setJobs(data)
      }
    } catch (err) {
      console.error('Error fetching jobs:', err)
    }
  }

  const handleSubmitJob = async (data: JobConfigFormData) => {
    setError(null)
    setTokenError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/run-custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      // Handle HTTP 429 - Token insuffisants
      if (response.status === 429) {
        const tokenErrorInfo = parseTokenError(response)
        setTokenError(tokenErrorInfo)
        const errorData = await response.json()
        const detail = errorData.detail
        if (typeof detail === 'object') {
          throw { response: { status: 429, data: errorData } }
        }
        throw new Error('Tokens Keepa insuffisants')
      }

      // Handle HTTP 400 - JOB_TOO_EXPENSIVE
      if (response.status === 400) {
        const errorData = await response.json()
        throw { response: { status: 400, data: errorData } }
      }

      // Handle HTTP 408 - Timeout
      if (response.status === 408) {
        const errorData = await response.json()
        throw { response: { status: 408, data: errorData } }
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`)
      }

      const newJob = await response.json()
      setJobs([newJob, ...jobs])
      setSelectedJob(newJob)
      setIsModalOpen(false) // Close modal on success
    } catch (err) {
      // Re-throw the error to be handled by the modal
      throw err
    }
  }

  const handleViewJobResults = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/jobs/${jobId}`)
      if (response.ok) {
        const job = await response.json()
        setSelectedJob(job)
      }
    } catch (err) {
      console.error('Error fetching job details:', err)
    }
  }

  return (
    <div className="min-h-screen bg-vault-bg">
      <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-semibold text-vault-text">AutoSourcing</h1>
            <p className="text-vault-text-secondary mt-1">
              Decouverte automatique de produits via jobs personnalises
            </p>
            <p className="text-sm text-vault-text-muted mt-2">
              Pour analyser des ASINs manuellement, utilisez{' '}
              <a href="/analyse" className="text-vault-accent hover:underline">
                Analyse Manuelle
              </a>
            </p>
          </div>
        </div>

        {tokenError && (
          <TokenErrorAlert
            error={{ status: 429, data: tokenError }}
          />
        )}

        {error && (
          <div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
            <p className="text-vault-danger text-sm">{error}</p>
          </div>
        )}

        <div className="flex justify-between items-center">
          <h2 className="text-xl font-display font-semibold text-vault-text">Jobs Recents</h2>
          <button
            onClick={() => setIsModalOpen(true)}
            data-testid="new-job-button"
            className="px-6 py-3 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover font-medium transition-colors"
          >
            Nouvelle Recherche Personnalisee
          </button>
        </div>

        <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
          <div className="p-6">
            {jobs.length === 0 ? (
              <div data-testid="empty-jobs" className="text-center py-12">
                <p className="text-vault-text-secondary">Aucun job trouve. Creez votre premiere recherche!</p>
              </div>
            ) : (
              <div data-testid="jobs-list" className="space-y-4">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    data-testid="job-card"
                    className="border border-vault-border rounded-xl p-4 hover:bg-vault-hover cursor-pointer transition-colors"
                    onClick={() => handleViewJobResults(job.id)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 data-testid="job-name" className="font-semibold text-vault-text">
                          {job.profile_name}
                        </h3>
                        <p data-testid="job-id" className="text-sm text-vault-text-muted">
                          ID: {job.id}
                        </p>
                        <p data-testid="job-date" className="text-sm text-vault-text-muted">
                          {new Date(job.launched_at).toLocaleString('fr-FR')}
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          data-testid="job-status"
                          className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                            job.status === 'COMPLETED'
                              ? 'bg-vault-success-light text-vault-success'
                              : job.status === 'RUNNING'
                              ? 'bg-vault-accent-light text-vault-accent'
                              : 'bg-vault-hover text-vault-text-muted'
                          }`}
                        >
                          {job.status}
                        </span>
                        <p className="text-sm text-vault-text-secondary mt-2">
                          {job.total_selected} picks / {job.total_tested} testes
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {selectedJob && selectedJob.picks && selectedJob.picks.length > 0 && (
          <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
            <div className="p-6 border-b border-vault-border">
              <h2 className="text-xl font-display font-semibold text-vault-text">
                Resultats: {selectedJob.profile_name}
              </h2>
            </div>
            <div className="p-6">
              <div data-testid="picks" className="space-y-4">
                {selectedJob.picks.map((pick) => (
                  <div
                    key={pick.id}
                    data-testid="pick"
                    className="border border-vault-border rounded-xl p-4"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 data-testid="pick-title" className="font-semibold text-vault-text">
                          {pick.title}
                        </h4>
                        <p data-testid="pick-asin" className="text-sm text-vault-text-muted">
                          ASIN: {pick.asin}
                        </p>
                      </div>
                      <div className="text-right space-y-1">
                        <p data-testid="pick-roi" className="text-sm">
                          <span className="font-medium text-vault-text">ROI:</span>{' '}
                          <span className="text-vault-success">{pick.roi_percentage.toFixed(1)}%</span>
                        </p>
                        <p data-testid="pick-velocity" className="text-sm">
                          <span className="font-medium text-vault-text">Velocity:</span>{' '}
                          <span className="text-vault-accent">{pick.velocity_score}</span>
                        </p>
                        <p data-testid="pick-confidence" className="text-sm">
                          <span className="font-medium text-vault-text">Confidence:</span>{' '}
                          <span className="text-vault-accent">{pick.confidence_score}</span>
                        </p>
                        <p data-testid="pick-rating" className="text-sm">
                          <span className="font-medium text-vault-text">Rating:</span>{' '}
                          <span className="text-vault-text-secondary">{pick.overall_rating}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <AutoSourcingJobModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSubmitJob}
      />
    </div>
  )
}
