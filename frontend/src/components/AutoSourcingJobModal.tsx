import React, { useState } from 'react';
import { z } from 'zod';

const jobConfigSchema = z.object({
  profile_name: z.string().min(3, 'Le nom doit contenir au moins 3 caractères'),
  discovery_config: z.object({
    categories: z.array(z.string()).min(1, 'Sélectionnez au moins une catégorie'),
    bsr_range: z.tuple([z.number().min(1), z.number().min(1)]),
    price_range: z.tuple([z.number().min(0), z.number().min(0)]).optional(),
    max_results: z.number().min(5).max(200),
  }),
  scoring_config: z.object({
    roi_min: z.number().min(0).max(200),
    velocity_min: z.number().min(0).max(100),
    confidence_min: z.number().min(0).max(100),
    rating_required: z.enum(['EXCELLENT', 'GOOD', 'FAIR', 'ANY']),
    max_results: z.number().min(1).max(100),
  }),
});

type JobConfigFormData = z.infer<typeof jobConfigSchema>;

interface CostEstimate {
  estimated_tokens: number;
  current_balance: number;
  safe_to_proceed: boolean;
  max_allowed: number;
  warning_message?: string;
  suggestion?: string;
}

interface AutoSourcingJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: JobConfigFormData) => Promise<void>;
}

const CATEGORIES = [
  'Books',
  'Electronics',
  'Home & Kitchen',
  'Sports & Outdoors',
  'Toys & Games',
  'Health & Personal Care',
];

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://arbitragevault-backend-v2.onrender.com';

const AutoSourcingJobModal: React.FC<AutoSourcingJobModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState<JobConfigFormData>({
    profile_name: '',
    discovery_config: {
      categories: ['Books'],
      bsr_range: [10000, 100000],
      price_range: [10, 50],
      max_results: 50,
    },
    scoring_config: {
      roi_min: 30,
      velocity_min: 70,
      confidence_min: 70,
      rating_required: 'GOOD',
      max_results: 20,
    },
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [isEstimating, setIsEstimating] = useState(false);
  const [safeguardError, setSafeguardError] = useState<string | null>(null);

  const handleEstimateCost = async () => {
    setIsEstimating(true);
    setSafeguardError(null);
    setCostEstimate(null);

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/autosourcing/estimate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          discovery_config: formData.discovery_config,
        }),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'estimation');
      }

      const data = await response.json();
      setCostEstimate(data);
    } catch (error) {
      console.error('Cost estimation error:', error);
      setSafeguardError('Impossible d\'estimer le cout du job');
    } finally {
      setIsEstimating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSafeguardError(null);

    try {
      const validated = jobConfigSchema.parse(formData);
      setIsSubmitting(true);
      await onSubmit(validated);
      onClose();
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        error.issues.forEach((err: z.ZodIssue) => {
          const path = err.path.join('.');
          fieldErrors[path] = err.message;
        });
        setErrors(fieldErrors);
      } else if (error && typeof error === 'object' && 'response' in error) {
        const responseError = error as { response?: { status?: number; data?: { detail?: { error?: string; estimated_tokens?: number; max_allowed?: number; suggestion?: string; balance?: number; required?: number } | string } } };

        if (responseError.response?.status === 400) {
          const detail = responseError.response.data?.detail;
          if (typeof detail === 'object' && detail.error === 'JOB_TOO_EXPENSIVE') {
            setSafeguardError(`Job trop couteux: ${detail.estimated_tokens} tokens requis (limite: ${detail.max_allowed}). ${detail.suggestion || ''}`);
          } else {
            setSafeguardError('Configuration du job invalide');
          }
        } else if (responseError.response?.status === 429) {
          const detail = responseError.response.data?.detail;
          if (typeof detail === 'object') {
            setSafeguardError(`Tokens insuffisants: ${detail.balance}/${detail.required} disponibles`);
          } else {
            setSafeguardError('Tokens Keepa insuffisants');
          }
        } else if (responseError.response?.status === 408) {
          setSafeguardError('Timeout du job - reduire la portee de recherche');
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Nouvelle Recherche Personnalisée</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              data-testid="close-modal"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} data-testid="job-config-form">
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom du Profil
              </label>
              <input
                type="text"
                data-testid="profile-name"
                value={formData.profile_name}
                onChange={(e) => setFormData({ ...formData, profile_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ex: Livres Techniques 20-50$"
              />
              {errors.profile_name && (
                <p className="mt-1 text-sm text-red-600">{errors.profile_name}</p>
              )}
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Découverte</h3>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Catégories
                </label>
                <select
                  multiple
                  data-testid="categories"
                  value={formData.discovery_config.categories}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, (option) => option.value);
                    setFormData({
                      ...formData,
                      discovery_config: { ...formData.discovery_config, categories: selected },
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  size={4}
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                {errors['discovery_config.categories'] && (
                  <p className="mt-1 text-sm text-red-600">{errors['discovery_config.categories']}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    BSR Min
                  </label>
                  <input
                    type="number"
                    data-testid="bsr-min"
                    value={formData.discovery_config.bsr_range[0]}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        discovery_config: {
                          ...formData.discovery_config,
                          bsr_range: [Number(e.target.value), formData.discovery_config.bsr_range[1]],
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    BSR Max
                  </label>
                  <input
                    type="number"
                    data-testid="bsr-max"
                    value={formData.discovery_config.bsr_range[1]}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        discovery_config: {
                          ...formData.discovery_config,
                          bsr_range: [formData.discovery_config.bsr_range[0], Number(e.target.value)],
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Prix Min ($)
                  </label>
                  <input
                    type="number"
                    data-testid="price-min"
                    value={formData.discovery_config.price_range?.[0] || 0}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        discovery_config: {
                          ...formData.discovery_config,
                          price_range: [Number(e.target.value), formData.discovery_config.price_range?.[1] || 100],
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Prix Max ($)
                  </label>
                  <input
                    type="number"
                    data-testid="price-max"
                    value={formData.discovery_config.price_range?.[1] || 100}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        discovery_config: {
                          ...formData.discovery_config,
                          price_range: [formData.discovery_config.price_range?.[0] || 0, Number(e.target.value)],
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Résultats Max
                </label>
                <input
                  type="number"
                  data-testid="max-results-discovery"
                  value={formData.discovery_config.max_results}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      discovery_config: { ...formData.discovery_config, max_results: Number(e.target.value) },
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="mt-4">
                <button
                  type="button"
                  onClick={handleEstimateCost}
                  disabled={isEstimating}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isEstimating ? 'Estimation...' : 'Estimer le Cout'}
                </button>
              </div>

              {costEstimate && (
                <div className={`mt-4 p-4 rounded-md ${costEstimate.safe_to_proceed ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                  <h4 className="font-semibold text-gray-900 mb-2">Estimation du Cout</h4>
                  <div className="space-y-1 text-sm">
                    <p>Tokens estimes: <span className="font-semibold">{costEstimate.estimated_tokens}</span></p>
                    <p>Balance actuelle: <span className="font-semibold">{costEstimate.current_balance}</span></p>
                    <p>Limite max: <span className="font-semibold">{costEstimate.max_allowed}</span></p>
                    {costEstimate.warning_message && (
                      <p className="text-yellow-700 mt-2">{costEstimate.warning_message}</p>
                    )}
                    {costEstimate.suggestion && (
                      <p className="text-blue-700 mt-2">{costEstimate.suggestion}</p>
                    )}
                  </div>
                </div>
              )}

              {safeguardError && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-700">{safeguardError}</p>
                </div>
              )}
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Scoring</h3>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ROI Min (%)
                  </label>
                  <input
                    type="number"
                    data-testid="roi-min"
                    value={formData.scoring_config.roi_min}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scoring_config: { ...formData.scoring_config, roi_min: Number(e.target.value) },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Velocity Min
                  </label>
                  <input
                    type="number"
                    data-testid="velocity-min"
                    value={formData.scoring_config.velocity_min}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scoring_config: { ...formData.scoring_config, velocity_min: Number(e.target.value) },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confidence Min
                  </label>
                  <input
                    type="number"
                    data-testid="confidence-min"
                    value={formData.scoring_config.confidence_min}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scoring_config: { ...formData.scoring_config, confidence_min: Number(e.target.value) },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rating Requis
                  </label>
                  <select
                    data-testid="rating-required"
                    value={formData.scoring_config.rating_required}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        scoring_config: {
                          ...formData.scoring_config,
                          rating_required: e.target.value as 'EXCELLENT' | 'GOOD' | 'FAIR' | 'ANY',
                        },
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="EXCELLENT">Excellent</option>
                    <option value="GOOD">Good</option>
                    <option value="FAIR">Fair</option>
                    <option value="ANY">Any</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Picks Max
                </label>
                <input
                  type="number"
                  data-testid="max-results-scoring"
                  value={formData.scoring_config.max_results}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scoring_config: { ...formData.scoring_config, max_results: Number(e.target.value) },
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Annuler
              </button>
              <button
                type="submit"
                data-testid="submit-job"
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Lancement...' : 'Lancer Recherche'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AutoSourcingJobModal;
