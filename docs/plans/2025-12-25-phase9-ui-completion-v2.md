# Phase 9: UI Completion Implementation Plan v2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Completer les 4 pages frontend placeholder en les connectant aux endpoints backend existants.

**Architecture:** Chaque page suit le pattern etabli: React Query hooks pour data fetching, Zod schemas pour validation, Tailwind CSS pour styling. Tous les endpoints backend existent deja - c'est du travail purement frontend.

**Tech Stack:** React 18, TypeScript, React Query (TanStack), Zod, Tailwind CSS

**Prerequisites:**
- Backend endpoints verifies (voir inventaire ci-dessous)
- Frontend patterns etablis dans pages existantes (AnalyseManuelle, AutoSourcing, NicheDiscovery)
- Phase 8 auditee (25 Dec 2025)

---

## Inventaire Backend Endpoints

### Configuration (`/api/v1/config/*`)
| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/config/` | GET | Get effective config (domain_id, category) |
| `/api/v1/config/` | PUT | Update config (scope, config object) |
| `/api/v1/config/stats` | GET | Get config statistics |
| `/api/v1/config/preview` | POST | Preview config changes |

### Strategic Views (`/api/v1/strategic-views/*`)
| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/strategic-views/` | GET | Get all strategic views |
| `/api/v1/strategic-views/{view_type}` | GET | Get specific view (velocity, competition, etc.) |
| `/api/v1/strategic-views/{view_type}/target-prices` | GET | Get target prices for view |

### Stock Estimates (`/api/v1/products/*`)
| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/products/{asin}/stock-estimate` | GET | Get stock estimate for ASIN |

---

## Task 1: Configuration Page - Types et API

**Files:**
- Create: `frontend/src/types/config.ts`
- Modify: `frontend/src/services/api.ts` (add config endpoints)

### Step 1.1: Create TypeScript types

Create: `frontend/src/types/config.ts`

```typescript
/**
 * Configuration Types for Phase 9
 * Backend: /api/v1/config/*
 */
import { z } from 'zod';

// Business config schema - matches backend BusinessConfigSchema
export const BusinessConfigSchema = z.object({
  roi_thresholds: z.object({
    minimum: z.number(),
    target: z.number(),
    excellent: z.number(),
  }),
  bsr_limits: z.object({
    max_acceptable: z.number(),
    ideal_max: z.number(),
  }),
  pricing: z.object({
    min_profit_margin: z.number(),
    fee_estimate_percent: z.number(),
  }),
  velocity: z.object({
    min_score: z.number(),
    weight_in_scoring: z.number(),
  }),
});

export type BusinessConfig = z.infer<typeof BusinessConfigSchema>;

export const ConfigResponseSchema = z.object({
  scope: z.string(),
  config: BusinessConfigSchema,
  version: z.number(),
  effective_config: BusinessConfigSchema,
  sources: z.record(z.string()).optional(),
  updated_at: z.string(),
});

export type ConfigResponse = z.infer<typeof ConfigResponseSchema>;

export const ConfigStatsSchema = z.object({
  total_configs: z.number(),
  by_scope: z.record(z.number()),
  last_updated: z.string().nullable(),
  cache_status: z.string(),
});

export type ConfigStats = z.infer<typeof ConfigStatsSchema>;

export interface ConfigUpdateRequest {
  config: Partial<BusinessConfig>;
  description?: string;
}
```

### Step 1.2: Add config endpoints to API service

Modify: `frontend/src/services/api.ts`

Add imports at top:
```typescript
import type { ConfigResponse, ConfigStats, ConfigUpdateRequest } from '../types/config';
```

Add to apiService object (before closing brace):
```typescript
  // ===== Phase 9: Configuration Endpoints =====

  async getConfig(domainId: number = 1, category: string = 'books'): Promise<ConfigResponse> {
    const response = await api.get('/api/v1/config/', {
      params: { domain_id: domainId, category, force_refresh: false }
    });
    return response.data;
  },

  async updateConfig(scope: string, request: ConfigUpdateRequest): Promise<ConfigResponse> {
    const response = await api.put('/api/v1/config/', request, {
      params: { scope }
    });
    return response.data;
  },

  async getConfigStats(): Promise<ConfigStats> {
    const response = await api.get('/api/v1/config/stats');
    return response.data;
  },
```

### Step 1.3: Verify types compile

Run:
```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors

### Step 1.4: Commit types and API

```bash
git add frontend/src/types/config.ts frontend/src/services/api.ts
git commit -m "feat(phase9): add Configuration types and API endpoints"
```

---

## Task 2: Configuration Page - Hook et Page

**Files:**
- Create: `frontend/src/hooks/useConfig.ts`
- Modify: `frontend/src/pages/Configuration.tsx`

### Step 2.1: Create React Query hook

Create: `frontend/src/hooks/useConfig.ts`

```typescript
/**
 * React Query hooks for Configuration
 * Phase 9 - UI Completion
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import type { ConfigResponse, ConfigStats, ConfigUpdateRequest } from '../types/config';

export const configKeys = {
  all: ['config'] as const,
  effective: (domainId: number, category: string) =>
    [...configKeys.all, 'effective', domainId, category] as const,
  stats: () => [...configKeys.all, 'stats'] as const,
};

export function useEffectiveConfig(domainId: number = 1, category: string = 'books') {
  return useQuery({
    queryKey: configKeys.effective(domainId, category),
    queryFn: () => apiService.getConfig(domainId, category),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useConfigStats() {
  return useQuery({
    queryKey: configKeys.stats(),
    queryFn: () => apiService.getConfigStats(),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useUpdateConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ scope, request }: { scope: string; request: ConfigUpdateRequest }) =>
      apiService.updateConfig(scope, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: configKeys.all });
    },
  });
}
```

### Step 2.2: Implement Configuration page

Replace: `frontend/src/pages/Configuration.tsx`

```typescript
import { useState } from 'react';
import { useEffectiveConfig, useConfigStats, useUpdateConfig } from '../hooks/useConfig';
import toast from 'react-hot-toast';

export default function Configuration() {
  const [domainId, setDomainId] = useState(1);
  const [category, setCategory] = useState('books');
  const [editMode, setEditMode] = useState(false);

  const { data: config, isLoading, error } = useEffectiveConfig(domainId, category);
  const { data: stats } = useConfigStats();
  const updateMutation = useUpdateConfig();

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-red-800 font-semibold">Erreur de chargement</h2>
          <p className="text-red-600 text-sm mt-1">
            Impossible de charger la configuration: {(error as Error).message}
          </p>
        </div>
      </div>
    );
  }

  const handleSave = async (sectionKey: string, newValues: Record<string, number>) => {
    try {
      await updateMutation.mutateAsync({
        scope: 'global',
        request: { config: { [sectionKey]: newValues }, description: 'Update from UI' }
      });
      toast.success('Configuration sauvegardee');
      setEditMode(false);
    } catch (err) {
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
        <button
          onClick={() => setEditMode(!editMode)}
          className={`px-4 py-2 rounded-lg font-medium ${
            editMode
              ? 'bg-gray-200 text-gray-700'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {editMode ? 'Annuler' : 'Modifier'}
        </button>
      </div>

      {/* Domain/Category selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domaine Amazon
            </label>
            <select
              value={domainId}
              onChange={(e) => setDomainId(Number(e.target.value))}
              className="border rounded-lg px-3 py-2"
            >
              <option value={1}>US (.com)</option>
              <option value={2}>UK (.co.uk)</option>
              <option value={3}>DE (.de)</option>
              <option value={4}>FR (.fr)</option>
              <option value={6}>CA (.ca)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categorie
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="border rounded-lg px-3 py-2"
            >
              <option value="books">Livres</option>
              <option value="electronics">Electronique</option>
              <option value="toys">Jouets</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats card */}
      {stats && (
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-blue-900 mb-2">Statistiques</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-blue-600">Configs totales:</span>{' '}
              <span className="font-semibold">{stats.total_configs}</span>
            </div>
            <div>
              <span className="text-blue-600">Cache:</span>{' '}
              <span className="font-semibold">{stats.cache_status}</span>
            </div>
            <div>
              <span className="text-blue-600">Derniere MAJ:</span>{' '}
              <span className="font-semibold">
                {stats.last_updated ? new Date(stats.last_updated).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Config sections */}
      {config?.effective_config && (
        <div className="space-y-6">
          <ConfigSection
            title="Seuils ROI"
            sectionKey="roi_thresholds"
            config={config.effective_config.roi_thresholds}
            fields={[
              { key: 'minimum', label: 'Minimum (%)', type: 'number' },
              { key: 'target', label: 'Cible (%)', type: 'number' },
              { key: 'excellent', label: 'Excellent (%)', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('roi_thresholds', values)}
          />

          <ConfigSection
            title="Limites BSR"
            sectionKey="bsr_limits"
            config={config.effective_config.bsr_limits}
            fields={[
              { key: 'max_acceptable', label: 'Max acceptable', type: 'number' },
              { key: 'ideal_max', label: 'Ideal max', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('bsr_limits', values)}
          />

          <ConfigSection
            title="Tarification"
            sectionKey="pricing"
            config={config.effective_config.pricing}
            fields={[
              { key: 'min_profit_margin', label: 'Marge min (%)', type: 'number' },
              { key: 'fee_estimate_percent', label: 'Estimation frais (%)', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('pricing', values)}
          />

          <ConfigSection
            title="Velocite"
            sectionKey="velocity"
            config={config.effective_config.velocity}
            fields={[
              { key: 'min_score', label: 'Score minimum', type: 'number' },
              { key: 'weight_in_scoring', label: 'Poids scoring', type: 'number' },
            ]}
            editMode={editMode}
            onSave={(values) => handleSave('velocity', values)}
          />
        </div>
      )}
    </div>
  );
}

// Config section component
interface ConfigSectionProps {
  title: string;
  sectionKey: string;
  config: Record<string, number>;
  fields: Array<{ key: string; label: string; type: string }>;
  editMode: boolean;
  onSave: (values: Record<string, number>) => void;
}

function ConfigSection({ title, config, fields, editMode, onSave }: ConfigSectionProps) {
  const [values, setValues] = useState<Record<string, number>>(config);

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: Number(value) }));
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {fields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm text-gray-600 mb-1">{field.label}</label>
              {editMode ? (
                <input
                  type={field.type}
                  value={values[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  className="w-full border rounded px-3 py-2 text-sm"
                />
              ) : (
                <div className="text-lg font-semibold text-gray-900">
                  {config[field.key]?.toLocaleString() ?? 'N/A'}
                </div>
              )}
            </div>
          ))}
        </div>
        {editMode && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => onSave(values)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Sauvegarder
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Step 2.3: Verify page compiles

Run:
```bash
cd frontend && npx tsc --noEmit
```

### Step 2.4: Commit Configuration page

```bash
git add frontend/src/hooks/useConfig.ts frontend/src/pages/Configuration.tsx
git commit -m "feat(phase9): implement Configuration page with edit mode"
```

---

## Task 3: Strategic Analysis Page - Types et API

**Files:**
- Create: `frontend/src/types/strategic.ts`
- Modify: `frontend/src/services/api.ts` (add strategic endpoints)

### Step 3.1: Create TypeScript types

Create: `frontend/src/types/strategic.ts`

```typescript
/**
 * Strategic Views Types for Phase 9
 * Backend: /api/v1/strategic-views/*
 */
import { z } from 'zod';

export type ViewType = 'velocity' | 'competition' | 'volatility' | 'consistency' | 'confidence';

export const StrategicMetricSchema = z.object({
  score: z.number(),
  label: z.string(),
  description: z.string(),
  color: z.enum(['green', 'yellow', 'red', 'gray']),
});

export type StrategicMetric = z.infer<typeof StrategicMetricSchema>;

export const StrategicViewResponseSchema = z.object({
  view_type: z.string(),
  metrics: z.record(StrategicMetricSchema).optional(),
  summary: z.object({
    total_products: z.number(),
    avg_score: z.number(),
    recommendation: z.string(),
  }),
  calculated_at: z.string(),
});

export type StrategicViewResponse = z.infer<typeof StrategicViewResponseSchema>;

export const TargetPriceProductSchema = z.object({
  asin: z.string(),
  title: z.string().optional().nullable(),
  current_price: z.number(),
  target_price: z.number(),
  expected_roi: z.number(),
  confidence: z.number(),
});

export const TargetPricesSchema = z.object({
  view_type: z.string(),
  products: z.array(TargetPriceProductSchema),
});

export type TargetPrices = z.infer<typeof TargetPricesSchema>;
```

### Step 3.2: Add strategic endpoints to API service

Add to `frontend/src/services/api.ts` imports:
```typescript
import type { StrategicViewResponse, TargetPrices } from '../types/strategic';
```

Add to apiService object:
```typescript
  // ===== Phase 9: Strategic Views Endpoints =====

  async getStrategicView(viewType: string, niches?: string[]): Promise<StrategicViewResponse> {
    const response = await api.get(`/api/v1/strategic-views/${viewType}`, {
      params: niches ? { niches: niches.join(',') } : {}
    });
    return response.data;
  },

  async getAllStrategicViews(): Promise<Record<string, StrategicViewResponse>> {
    const response = await api.get('/api/v1/strategic-views/');
    return response.data;
  },

  async getTargetPrices(viewType: string): Promise<TargetPrices> {
    const response = await api.get(`/api/v1/strategic-views/${viewType}/target-prices`);
    return response.data;
  },
```

### Step 3.3: Commit types and API

```bash
git add frontend/src/types/strategic.ts frontend/src/services/api.ts
git commit -m "feat(phase9): add Strategic Views types and API endpoints"
```

---

## Task 4: Strategic Analysis Page - Hook et Page

**Files:**
- Create: `frontend/src/hooks/useStrategicViews.ts`
- Modify: `frontend/src/pages/AnalyseStrategique.tsx`

### Step 4.1: Create React Query hook

Create: `frontend/src/hooks/useStrategicViews.ts`

```typescript
/**
 * React Query hooks for Strategic Views
 * Phase 9 - UI Completion
 */
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import type { StrategicViewResponse, TargetPrices, ViewType } from '../types/strategic';

export const strategicKeys = {
  all: ['strategic'] as const,
  view: (viewType: ViewType) => [...strategicKeys.all, 'view', viewType] as const,
  allViews: () => [...strategicKeys.all, 'all'] as const,
  targetPrices: (viewType: ViewType) => [...strategicKeys.all, 'targets', viewType] as const,
};

export function useStrategicView(viewType: ViewType, niches?: string[]) {
  return useQuery({
    queryKey: strategicKeys.view(viewType),
    queryFn: () => apiService.getStrategicView(viewType, niches),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useAllStrategicViews() {
  return useQuery({
    queryKey: strategicKeys.allViews(),
    queryFn: () => apiService.getAllStrategicViews(),
    staleTime: 2 * 60 * 1000,
  });
}

export function useTargetPrices(viewType: ViewType) {
  return useQuery({
    queryKey: strategicKeys.targetPrices(viewType),
    queryFn: () => apiService.getTargetPrices(viewType),
    staleTime: 5 * 60 * 1000,
    enabled: !!viewType,
  });
}
```

### Step 4.2: Implement AnalyseStrategique page

Replace: `frontend/src/pages/AnalyseStrategique.tsx`

```typescript
import { useState } from 'react';
import { useAllStrategicViews, useTargetPrices } from '../hooks/useStrategicViews';
import type { ViewType } from '../types/strategic';

const VIEW_LABELS: Record<ViewType, { label: string; description: string }> = {
  velocity: {
    label: 'Velocite',
    description: 'Vitesse de rotation des stocks basee sur BSR et ventes'
  },
  competition: {
    label: 'Competition',
    description: 'Niveau de competition (vendeurs, presence Amazon)'
  },
  volatility: {
    label: 'Volatilite',
    description: 'Stabilite des prix dans le temps'
  },
  consistency: {
    label: 'Consistance',
    description: 'Regularite de la demande'
  },
  confidence: {
    label: 'Confiance',
    description: 'Fiabilite des donnees et predictions'
  },
};

export default function AnalyseStrategique() {
  const [selectedView, setSelectedView] = useState<ViewType>('velocity');
  const { data: allViews, isLoading, error } = useAllStrategicViews();
  const { data: targetPrices } = useTargetPrices(selectedView);

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-red-800 font-semibold">Erreur de chargement</h2>
          <p className="text-red-600 text-sm mt-1">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600 bg-green-50';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Analyse Strategique</h1>

      {/* View selector cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {(Object.keys(VIEW_LABELS) as ViewType[]).map((viewType) => {
          const viewData = allViews?.[viewType];
          const info = VIEW_LABELS[viewType];
          const isSelected = selectedView === viewType;

          return (
            <button
              key={viewType}
              onClick={() => setSelectedView(viewType)}
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="font-semibold text-gray-900">{info.label}</div>
              {viewData?.summary && (
                <div className={`text-2xl font-bold mt-2 rounded px-2 py-1 inline-block ${getScoreColor(viewData.summary.avg_score)}`}>
                  {(viewData.summary.avg_score * 100).toFixed(0)}%
                </div>
              )}
              <div className="text-xs text-gray-500 mt-1">
                {viewData?.summary?.total_products ?? 0} produits
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected view details */}
      {allViews?.[selectedView] && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              {VIEW_LABELS[selectedView].label}
            </h2>
            <p className="text-sm text-gray-600">{VIEW_LABELS[selectedView].description}</p>
          </div>

          <div className="p-6">
            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-sm text-gray-600">Score moyen</div>
                  <div className={`text-3xl font-bold ${getScoreColor(allViews[selectedView].summary.avg_score)}`}>
                    {(allViews[selectedView].summary.avg_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Produits analyses</div>
                  <div className="text-3xl font-bold text-gray-900">
                    {allViews[selectedView].summary.total_products}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Recommandation</div>
                  <div className="text-sm font-medium text-gray-700 mt-2">
                    {allViews[selectedView].summary.recommendation}
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics breakdown */}
            {allViews[selectedView].metrics && Object.keys(allViews[selectedView].metrics).length > 0 && (
              <div className="space-y-3">
                <h3 className="font-medium text-gray-900">Details des metriques</h3>
                {Object.entries(allViews[selectedView].metrics!).map(([key, metric]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium text-gray-900">{metric.label}</div>
                      <div className="text-sm text-gray-600">{metric.description}</div>
                    </div>
                    <div className={`px-3 py-1 rounded-full font-semibold ${
                      metric.color === 'green' ? 'bg-green-100 text-green-700' :
                      metric.color === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                      metric.color === 'red' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {(metric.score * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Target prices table */}
            {targetPrices?.products && targetPrices.products.length > 0 && (
              <div className="mt-6">
                <h3 className="font-medium text-gray-900 mb-3">Prix cibles recommandes</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">ASIN</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Titre</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Prix actuel</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Prix cible</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">ROI attendu</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {targetPrices.products.slice(0, 10).map((product) => (
                        <tr key={product.asin}>
                          <td className="px-4 py-2 text-sm font-mono text-blue-600">{product.asin}</td>
                          <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">
                            {product.title || '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-right">${product.current_price.toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm text-right font-semibold text-green-600">
                            ${product.target_price.toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-sm text-right">{product.expected_roi.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          <div className="px-6 py-3 bg-gray-50 text-xs text-gray-500 rounded-b-lg">
            Calcule le: {new Date(allViews[selectedView].calculated_at).toLocaleString()}
          </div>
        </div>
      )}

      {/* Empty state if no views */}
      {(!allViews || Object.keys(allViews).length === 0) && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900">Aucune donnee strategique</h3>
          <p className="text-gray-600 mt-1">Analysez des produits pour voir les vues strategiques</p>
        </div>
      )}
    </div>
  );
}
```

### Step 4.3: Commit Strategic page

```bash
git add frontend/src/hooks/useStrategicViews.ts frontend/src/pages/AnalyseStrategique.tsx
git commit -m "feat(phase9): implement AnalyseStrategique page with 5 views"
```

---

## Task 5: Stock Estimates Page

**Files:**
- Create: `frontend/src/types/stock.ts`
- Create: `frontend/src/hooks/useStockEstimate.ts`
- Modify: `frontend/src/services/api.ts` (add stock endpoint)
- Modify: `frontend/src/pages/StockEstimates.tsx`

### Step 5.1: Create types and hook

Create: `frontend/src/types/stock.ts`

```typescript
/**
 * Stock Estimate Types for Phase 9
 * Backend: /api/v1/products/{asin}/stock-estimate
 */
import { z } from 'zod';

export const StockEstimateSchema = z.object({
  asin: z.string(),
  fba_offers: z.number(),
  mfn_offers: z.number(),
  total_offers: z.number(),
  availability_estimate: z.enum(['high', 'medium', 'low', 'out_of_stock']),
  lowest_fba_price: z.number().nullable(),
  lowest_mfn_price: z.number().nullable(),
  buy_box_price: z.number().nullable(),
  buy_box_seller: z.string().nullable(),
  source: z.enum(['cache', 'api', 'error']),
  cached_at: z.string().nullable(),
  error: z.string().optional(),
});

export type StockEstimate = z.infer<typeof StockEstimateSchema>;
```

Add to `frontend/src/services/api.ts`:
```typescript
import type { StockEstimate } from '../types/stock';

// In apiService object:
  // ===== Phase 9: Stock Estimate Endpoint =====

  async getStockEstimate(asin: string, priceTarget?: number): Promise<StockEstimate> {
    const response = await api.get(`/api/v1/products/${asin}/stock-estimate`, {
      params: priceTarget ? { price_target: priceTarget } : {}
    });
    return response.data;
  },
```

Create: `frontend/src/hooks/useStockEstimate.ts`

```typescript
/**
 * React Query hook for Stock Estimates
 * Phase 9 - UI Completion
 */
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';

export const stockKeys = {
  all: ['stock'] as const,
  estimate: (asin: string) => [...stockKeys.all, 'estimate', asin] as const,
};

export function useStockEstimate(asin: string | null, priceTarget?: number) {
  return useQuery({
    queryKey: stockKeys.estimate(asin ?? ''),
    queryFn: () => apiService.getStockEstimate(asin!, priceTarget),
    enabled: !!asin && asin.length >= 10,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}
```

### Step 5.2: Implement StockEstimates page

Replace: `frontend/src/pages/StockEstimates.tsx`

```typescript
import { useState } from 'react';
import { useStockEstimate } from '../hooks/useStockEstimate';
import toast from 'react-hot-toast';

export default function StockEstimates() {
  const [asinInput, setAsinInput] = useState('');
  const [searchAsin, setSearchAsin] = useState<string | null>(null);
  const [priceTarget, setPriceTarget] = useState<number | undefined>(undefined);

  const { data: estimate, isLoading, error, refetch } = useStockEstimate(searchAsin, priceTarget);

  const handleSearch = () => {
    const cleanAsin = asinInput.trim().toUpperCase();
    if (cleanAsin.length < 10) {
      toast.error('ASIN invalide (minimum 10 caracteres)');
      return;
    }
    setSearchAsin(cleanAsin);
  };

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case 'high': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-orange-100 text-orange-800';
      case 'out_of_stock': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAvailabilityLabel = (availability: string) => {
    switch (availability) {
      case 'high': return 'Stock eleve';
      case 'medium': return 'Stock moyen';
      case 'low': return 'Stock faible';
      case 'out_of_stock': return 'Rupture de stock';
      default: return 'Inconnu';
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Estimation de Stock</h1>

      {/* Search form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ASIN
            </label>
            <input
              type="text"
              value={asinInput}
              onChange={(e) => setAsinInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Ex: B08N5WRWNW"
              className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="w-40">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prix cible ($)
            </label>
            <input
              type="number"
              value={priceTarget ?? ''}
              onChange={(e) => setPriceTarget(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="Optionnel"
              className="w-full border rounded-lg px-4 py-2"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Chargement...' : 'Analyser'}
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <h3 className="text-red-800 font-semibold">Erreur</h3>
          <p className="text-red-600 text-sm">{(error as Error).message}</p>
        </div>
      )}

      {/* Results */}
      {estimate && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                ASIN: <span className="font-mono text-blue-600">{estimate.asin}</span>
              </h2>
              <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium ${getAvailabilityColor(estimate.availability_estimate)}`}>
                {getAvailabilityLabel(estimate.availability_estimate)}
              </span>
            </div>
            <button
              onClick={() => refetch()}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Rafraichir
            </button>
          </div>

          <div className="p-6">
            {/* Offers summary */}
            <div className="grid grid-cols-3 gap-6 mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-900">{estimate.total_offers}</div>
                <div className="text-sm text-gray-600">Offres totales</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600">{estimate.fba_offers}</div>
                <div className="text-sm text-gray-600">Offres FBA</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl font-bold text-purple-600">{estimate.mfn_offers}</div>
                <div className="text-sm text-gray-600">Offres MFN</div>
              </div>
            </div>

            {/* Prices */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Prix</h3>
              <div className="grid grid-cols-3 gap-4">
                {estimate.buy_box_price != null && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-gray-600">Buy Box</div>
                    <div className="text-xl font-bold text-green-600">
                      ${estimate.buy_box_price.toFixed(2)}
                    </div>
                    {estimate.buy_box_seller && (
                      <div className="text-xs text-gray-500 mt-1">
                        {estimate.buy_box_seller === 'Amazon' ? 'Amazon' : 'Vendeur tiers'}
                      </div>
                    )}
                  </div>
                )}
                {estimate.lowest_fba_price != null && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-gray-600">Plus bas FBA</div>
                    <div className="text-xl font-bold text-blue-600">
                      ${estimate.lowest_fba_price.toFixed(2)}
                    </div>
                  </div>
                )}
                {estimate.lowest_mfn_price != null && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-gray-600">Plus bas MFN</div>
                    <div className="text-xl font-bold text-purple-600">
                      ${estimate.lowest_mfn_price.toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Source info */}
            <div className="mt-6 pt-4 border-t text-xs text-gray-500">
              <span className="mr-4">Source: {estimate.source}</span>
              {estimate.cached_at && (
                <span>Cache: {new Date(estimate.cached_at).toLocaleString()}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!estimate && !isLoading && !error && (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <div className="text-gray-400 text-5xl mb-4">...</div>
          <h3 className="text-lg font-medium text-gray-900">Aucune recherche</h3>
          <p className="text-gray-600 mt-1">Entrez un ASIN pour estimer la disponibilite du stock</p>
        </div>
      )}
    </div>
  );
}
```

### Step 5.3: Commit Stock page

```bash
git add frontend/src/types/stock.ts frontend/src/hooks/useStockEstimate.ts frontend/src/services/api.ts frontend/src/pages/StockEstimates.tsx
git commit -m "feat(phase9): implement StockEstimates page with ASIN search"
```

---

## Task 6: AutoScheduler Page (Future Feature Concept)

**Files:**
- Modify: `frontend/src/pages/AutoScheduler.tsx`

### Step 6.1: Implement AutoScheduler concept UI

Replace: `frontend/src/pages/AutoScheduler.tsx`

```typescript
import { useState } from 'react';
import toast from 'react-hot-toast';

interface ScheduledJob {
  id: string;
  name: string;
  type: 'discovery' | 'analysis' | 'sourcing';
  schedule: string;
  lastRun: string | null;
  nextRun: string;
  status: 'active' | 'paused' | 'error';
}

// Demo data
const DEMO_JOBS: ScheduledJob[] = [
  {
    id: '1',
    name: 'Discovery quotidien - Livres US',
    type: 'discovery',
    schedule: '0 8 * * *',
    lastRun: '2025-12-14T08:00:00Z',
    nextRun: '2025-12-15T08:00:00Z',
    status: 'active',
  },
  {
    id: '2',
    name: 'Analyse niches sauvegardees',
    type: 'analysis',
    schedule: '0 12 * * 1',
    lastRun: '2025-12-09T12:00:00Z',
    nextRun: '2025-12-16T12:00:00Z',
    status: 'active',
  },
];

export default function AutoScheduler() {
  const [jobs] = useState<ScheduledJob[]>(DEMO_JOBS);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'discovery': return 'Discovery';
      case 'analysis': return 'Analyse';
      case 'sourcing': return 'Sourcing';
      default: return type;
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AutoScheduler</h1>
          <p className="text-gray-600 mt-1">Planifiez vos analyses et discoveries automatiques</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <span>+</span> Nouveau job
        </button>
      </div>

      {/* Feature notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl">...</span>
          <div>
            <h3 className="font-semibold text-amber-800">Fonctionnalite en developpement</h3>
            <p className="text-amber-700 text-sm mt-1">
              L'AutoScheduler est en cours de developpement. L'interface ci-dessous montre
              le concept prevu. Les jobs planifies seront disponibles dans une prochaine version.
            </p>
          </div>
        </div>
      </div>

      {/* Jobs list */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Jobs planifies (demo)</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {jobs.map((job) => (
            <div key={job.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold">
                    {getTypeLabel(job.type)[0]}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{job.name}</div>
                    <div className="text-sm text-gray-600">
                      Schedule: <code className="bg-gray-100 px-1 rounded">{job.schedule}</code>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right text-sm">
                    <div className="text-gray-500">Prochaine execution</div>
                    <div className="font-medium">
                      {new Date(job.nextRun).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(job.status)}`}>
                    {job.status}
                  </span>
                  <button
                    onClick={() => toast('Actions bientot disponibles')}
                    className="p-2 text-gray-400 hover:text-gray-600"
                  >
                    ...
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Planned features */}
      <div className="mt-8 grid grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Discovery automatique</h3>
          <p className="text-sm text-gray-600">
            Lancez des recherches de niches a intervalles reguliers
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Analyse planifiee</h3>
          <p className="text-sm text-gray-600">
            Re-analysez vos niches sauvegardees automatiquement
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Notifications</h3>
          <p className="text-sm text-gray-600">
            Recevez des alertes sur les opportunites detectees
          </p>
        </div>
      </div>

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Nouveau job planifie</h3>
            </div>
            <div className="p-6">
              <p className="text-gray-600 mb-4">
                Cette fonctionnalite sera disponible prochainement.
              </p>
            </div>
            <div className="px-6 py-4 bg-gray-50 flex justify-end gap-3 rounded-b-lg">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Step 6.2: Commit AutoScheduler page

```bash
git add frontend/src/pages/AutoScheduler.tsx
git commit -m "feat(phase9): implement AutoScheduler concept UI (future feature)"
```

---

## Task 7: Type Exports et Integration

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/hooks/index.ts`

### Step 7.1: Update type exports

Add to `frontend/src/types/index.ts`:
```typescript
export * from './config';
export * from './strategic';
export * from './stock';
```

### Step 7.2: Update hooks exports

Add to `frontend/src/hooks/index.ts`:
```typescript
export * from './useConfig';
export * from './useStrategicViews';
export * from './useStockEstimate';
```

### Step 7.3: Verify build

Run:
```bash
cd frontend && npm run build
```

Expected: Build succeeds

### Step 7.4: Commit exports

```bash
git add frontend/src/types/index.ts frontend/src/hooks/index.ts
git commit -m "feat(phase9): add type and hook exports"
```

---

## Task 8: Verification Finale

### Step 8.1: Run full build

```bash
cd frontend && npm run build
```

### Step 8.2: Run type check

```bash
cd frontend && npx tsc --noEmit
```

### Step 8.3: Test pages locally

```bash
cd frontend && npm run dev
```

Visit each page:
- http://localhost:5173/config
- http://localhost:5173/analyse-strategique
- http://localhost:5173/stock-estimates
- http://localhost:5173/autoscheduler

### Step 8.4: Final commit

```bash
git add -A
git commit -m "feat(phase9): complete UI implementation

Phase 9 UI Completion - All 4 placeholder pages now functional:
- Configuration: Business config with edit mode
- AnalyseStrategique: 5 strategic views
- StockEstimates: ASIN stock checker
- AutoScheduler: Future feature concept

New files:
- types: config.ts, strategic.ts, stock.ts
- hooks: useConfig.ts, useStrategicViews.ts, useStockEstimate.ts

All connected to existing backend endpoints.

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

| Task | Description | Files | Commits |
|------|-------------|-------|---------|
| 1 | Config types + API | 2 | 1 |
| 2 | Config hook + page | 2 | 1 |
| 3 | Strategic types + API | 2 | 1 |
| 4 | Strategic hook + page | 2 | 1 |
| 5 | Stock types + hook + API + page | 4 | 1 |
| 6 | AutoScheduler page | 1 | 1 |
| 7 | Type/hook exports | 2 | 1 |
| 8 | Verification | 0 | 1 |

**Total: 8 tasks, ~15 files, 8 commits**

**Estimated time: 2-3 heures**

---

## Verification Checklist

- [ ] Configuration page loads with config data
- [ ] AnalyseStrategique shows 5 view types
- [ ] StockEstimates accepts ASIN and shows results
- [ ] AutoScheduler shows concept UI
- [ ] No "Page en construction..." visible
- [ ] Frontend builds without errors
- [ ] TypeScript compiles without errors
