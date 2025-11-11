import { useState, useEffect } from 'react';
import AutoSourcingJobModal from '../components/AutoSourcingJobModal';
import { TokenErrorAlert } from '../components/TokenErrorAlert';
import { parseTokenError } from '../utils/tokenErrorHandler';

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

export default function AutoSourcingJobs() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tokenError, setTokenError] = useState<ReturnType<typeof parseTokenError> | null>(null);

  useEffect(() => {
    fetchRecentJobs();
  }, []);

  const fetchRecentJobs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/jobs?limit=10`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      }
    } catch (err) {
      console.error('Error fetching jobs:', err);
    }
  };

  const handleSubmitJob = async (data: JobConfigFormData) => {
    setError(null);
    setTokenError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/run_custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.status === 429) {
        const tokenErrorInfo = parseTokenError(response);
        setTokenError(tokenErrorInfo);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const newJob = await response.json();
      setJobs([newJob, ...jobs]);
      setSelectedJob(newJob);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création du job');
    }
  };

  const handleViewJobResults = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/autosourcing/jobs/${jobId}`);
      if (response.ok) {
        const job = await response.json();
        setSelectedJob(job);
      }
    } catch (err) {
      console.error('Error fetching job details:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Jobs AutoSourcing</h1>
            <p className="text-gray-500 mt-1">
              Découverte automatique de produits avec critères personnalisés
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            data-testid="new-job-button"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Nouvelle Recherche Personnalisée
          </button>
        </div>

        {tokenError && (
          <TokenErrorAlert
            error={{ status: 429, data: tokenError }}
          />
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Jobs Récents</h2>
          </div>
          <div className="p-6">
            {jobs.length === 0 ? (
              <div data-testid="empty-jobs" className="text-center py-12">
                <p className="text-gray-500">Aucun job trouvé. Créez votre première recherche!</p>
              </div>
            ) : (
              <div data-testid="jobs-list" className="space-y-4">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    data-testid="job-card"
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleViewJobResults(job.id)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 data-testid="job-name" className="font-semibold text-gray-900">
                          {job.profile_name}
                        </h3>
                        <p data-testid="job-id" className="text-sm text-gray-500">
                          ID: {job.id}
                        </p>
                        <p data-testid="job-date" className="text-sm text-gray-500">
                          {new Date(job.launched_at).toLocaleString('fr-FR')}
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          data-testid="job-status"
                          className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                            job.status === 'COMPLETED'
                              ? 'bg-green-100 text-green-800'
                              : job.status === 'RUNNING'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {job.status}
                        </span>
                        <p className="text-sm text-gray-600 mt-2">
                          {job.total_selected} picks / {job.total_tested} testés
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
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Résultats: {selectedJob.profile_name}
              </h2>
            </div>
            <div className="p-6">
              <div data-testid="picks" className="space-y-4">
                {selectedJob.picks.map((pick) => (
                  <div
                    key={pick.id}
                    data-testid="pick"
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 data-testid="pick-title" className="font-semibold text-gray-900">
                          {pick.title}
                        </h4>
                        <p data-testid="pick-asin" className="text-sm text-gray-500">
                          ASIN: {pick.asin}
                        </p>
                      </div>
                      <div className="text-right space-y-1">
                        <p data-testid="pick-roi" className="text-sm">
                          <span className="font-medium">ROI:</span>{' '}
                          <span className="text-green-600">{pick.roi_percentage.toFixed(1)}%</span>
                        </p>
                        <p data-testid="pick-velocity" className="text-sm">
                          <span className="font-medium">Velocity:</span>{' '}
                          <span className="text-blue-600">{pick.velocity_score}</span>
                        </p>
                        <p data-testid="pick-confidence" className="text-sm">
                          <span className="font-medium">Confidence:</span>{' '}
                          <span className="text-purple-600">{pick.confidence_score}</span>
                        </p>
                        <p data-testid="pick-rating" className="text-sm">
                          <span className="font-medium">Rating:</span>{' '}
                          <span className="text-gray-700">{pick.overall_rating}</span>
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
  );
}
