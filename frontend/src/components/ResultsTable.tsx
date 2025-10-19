import { useState, useMemo } from 'react';
import type { BatchResultItem, IngestResponse } from '../types/keepa';
import { keepaService } from '../services/keepaService';

interface ResultsTableProps {
  data: IngestResponse | null;
  onExport?: () => void;
}

export default function ResultsTable({ data, onExport }: ResultsTableProps) {
  const [filterRating, setFilterRating] = useState<string>('all');
  const [filterMinROI, setFilterMinROI] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'roi' | 'roi_used' | 'bsr' | 'velocity'>('roi_used');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filtrer et trier les résultats
  const processedResults = useMemo(() => {
    if (!data) return [];

    console.log('ResultsTable - données reçues:', data);
    console.log('ResultsTable - nombre de résultats:', data.results?.length);

    let filtered = data.results.filter(r =>
      r.status === 'success' &&
      r.analysis !== null
    );

    console.log('ResultsTable - résultats avec succès:', filtered.length);
    console.log('ResultsTable - premier résultat:', filtered[0]);

    // Filtre par rating
    if (filterRating !== 'all') {
      filtered = filtered.filter(r => r.analysis?.overall_rating === filterRating);
    }

    // Filtre par ROI minimum
    filtered = filtered.filter(r => {
      const roi = r.analysis?.roi;
      if (roi && 'roi_percentage' in roi) {
        const roiValue = parseFloat(roi.roi_percentage);
        console.log(`ROI pour ${r.asin}: ${roiValue}%, filtre: ${filterMinROI}%`);
        return roiValue >= filterMinROI;
      }
      return false;
    });

    // Tri
    filtered.sort((a, b) => {
      const aVal = a.analysis!;
      const bVal = b.analysis!;
      let compareValue = 0;

      switch (sortBy) {
        case 'roi':
          const aROI = 'roi_percentage' in aVal.roi ? parseFloat(aVal.roi.roi_percentage) : -999;
          const bROI = 'roi_percentage' in bVal.roi ? parseFloat(bVal.roi.roi_percentage) : -999;
          compareValue = aROI - bROI;
          break;
        case 'roi_used':
          const aROIUsed = aVal.pricing?.used?.roi_percentage ?? -999;
          const bROIUsed = bVal.pricing?.used?.roi_percentage ?? -999;
          compareValue = aROIUsed - bROIUsed;
          break;
        case 'bsr':
          compareValue = (aVal.current_bsr || 999999) - (bVal.current_bsr || 999999);
          break;
        case 'velocity':
          compareValue = aVal.velocity_score - bVal.velocity_score;
          break;
      }

      return sortOrder === 'desc' ? -compareValue : compareValue;
    });

    return filtered;
  }, [data, filterRating, filterMinROI, sortBy, sortOrder]);

  const getRatingBadge = (rating: string) => {
    const badges = {
      'EXCELLENT': { bg: 'bg-green-100', text: 'text-green-800', icon: '🟢' },
      'GOOD': { bg: 'bg-blue-100', text: 'text-blue-800', icon: '🔵' },
      'FAIR': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '🟡' },
      'PASS': { bg: 'bg-red-100', text: 'text-red-800', icon: '🔴' },
      'ERROR': { bg: 'bg-gray-100', text: 'text-gray-800', icon: '⚠️' }
    };
    const badge = badges[rating as keyof typeof badges] || badges.ERROR;

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.icon} {rating}
      </span>
    );
  };

  // @ts-ignore - formatROI unused but kept for reference
  const _formatROI = (roi: any) => {
    if (!roi || 'error' in roi) return 'N/A';
    const percentage = parseFloat(roi.roi_percentage);
    const color = percentage >= 30 ? 'text-green-600' : percentage >= 0 ? 'text-yellow-600' : 'text-red-600';
    return <span className={`font-semibold ${color}`}>{percentage.toFixed(1)}%</span>;
  };

  const handleExportCSV = () => {
    if (!data) return;
    const csvContent = keepaService.exportToCSV(data);
    const filename = `analyse_${new Date().toISOString().split('T')[0]}.csv`;
    keepaService.downloadCSV(csvContent, filename);
    if (onExport) onExport();
  };

  if (!data) {
    return null;
  }

  // Si aucun résultat après filtrage, afficher un message
  if (processedResults.length === 0 && data.results.length > 0) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Aucun résultat ne correspond aux filtres
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            {data.results.length} produits analysés, mais aucun ne correspond aux critères :
          </p>
          <ul className="text-sm text-gray-600 text-left max-w-md mx-auto">
            <li>• ROI minimum : {filterMinROI}%</li>
            {filterRating !== 'all' && <li>• Rating : {filterRating}</li>}
          </ul>
          <button
            onClick={() => {
              setFilterMinROI(0);
              setFilterRating('all');
            }}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Réinitialiser les filtres
          </button>
        </div>
      </div>
    );
  }

  const successCount = data.results.filter(r => r.status === 'success').length;
  const opportunityCount = processedResults.filter(r => {
    const roi = r.analysis?.roi;
    return roi && 'roi_percentage' in roi && parseFloat(roi.roi_percentage) >= 30;
  }).length;

  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden">
      {/* En-tête avec statistiques */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Résultats d'analyse</h2>
            <p className="text-sm text-gray-600 mt-1">
              {successCount} produits analysés • {opportunityCount} opportunités détectées
            </p>
          </div>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <span>📥</span>
            <span>Export CSV</span>
          </button>
        </div>

        {/* Filtres */}
        <div className="flex gap-4 flex-wrap">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Rating</label>
            <select
              value={filterRating}
              onChange={(e) => setFilterRating(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="all">Tous</option>
              <option value="EXCELLENT">Excellent</option>
              <option value="GOOD">Good</option>
              <option value="FAIR">Fair</option>
              <option value="PASS">Pass</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">ROI min (%)</label>
            <input
              type="number"
              value={filterMinROI}
              onChange={(e) => setFilterMinROI(Number(e.target.value))}
              className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Trier par</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'roi' | 'roi_used' | 'bsr' | 'velocity')}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="roi_used">ROI USED (recommandé)</option>
              <option value="roi">ROI Legacy</option>
              <option value="bsr">BSR</option>
              <option value="velocity">Velocity</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Ordre</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="desc">Décroissant</option>
              <option value="asc">Croissant</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tableau */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ASIN
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Titre
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Prix Vente
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                BSR
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                💚 Prix USED
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                ROI USED
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Velocity
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rating
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {processedResults.map((result: BatchResultItem) => {
              const analysis = result.analysis!;
              return (
                <tr key={result.asin} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {analysis.asin}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    <div className="max-w-xs truncate" title={analysis.title || ''}>
                      {analysis.title || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-700">
                    ${analysis.current_price?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-700">
                    {analysis.current_bsr ? `#${analysis.current_bsr.toLocaleString()}` : 'N/A'}
                  </td>
                  {/* Prix USED Column */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    {analysis.pricing?.used?.available && analysis.pricing.used.current_price !== null ? (
                      <span className="font-semibold text-blue-700">
                        ${analysis.pricing.used.current_price.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-xs">Non dispo</span>
                    )}
                  </td>
                  {/* ROI USED Column */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    {analysis.pricing?.used?.roi_percentage !== null && analysis.pricing?.used?.roi_percentage !== undefined ? (
                      <span className={`font-semibold ${
                        analysis.pricing.used.roi_percentage >= 30 ? 'text-green-600' :
                        analysis.pricing.used.roi_percentage >= 15 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {analysis.pricing.used.roi_percentage >= 0 ? '+' : ''}{analysis.pricing.used.roi_percentage.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <div className="flex flex-col items-center">
                      <span className="font-semibold">{analysis.velocity_score}</span>
                      <div className="w-16 bg-gray-200 rounded-full h-1.5 mt-1">
                        <div
                          className="bg-blue-500 h-1.5 rounded-full"
                          style={{ width: `${analysis.velocity_score}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    {getRatingBadge(analysis.overall_rating)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <button
                      className="text-blue-600 hover:text-blue-800 font-medium"
                      onClick={() => window.open(`https://www.amazon.com/dp/${analysis.asin}`, '_blank')}
                    >
                      Voir
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}