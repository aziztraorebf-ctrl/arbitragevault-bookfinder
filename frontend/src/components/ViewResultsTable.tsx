/**
 * ViewResultsTable - Phase 2 View-Specific Scoring Results
 *
 * Displays scored products from view endpoints with:
 * - View-specific scores and weights
 * - Amazon Check badges (Phase 2.5A)
 * - Filtering by Amazon presence
 * - Sorting by score, ROI, velocity
 *
 * Usage:
 *   <ViewResultsTable
 *     products={scoreResponse.products}
 *     metadata={scoreResponse.metadata}
 *   />
 */

import { useState, useMemo } from 'react';
import type { ProductScore, ViewScoreMetadata } from '../types/views';
import { AmazonBadges } from './AmazonBadges';
import { Tooltip, InfoIcon } from './Tooltip';
import { ROITooltip } from './tooltips/ROITooltip';
import { VelocityTooltip } from './tooltips/VelocityTooltip';
import { MaxBuyTooltip } from './tooltips/MaxBuyTooltip';

interface ViewResultsTableProps {
  products: ProductScore[];
  metadata: ViewScoreMetadata;
  onExport?: () => void;
}

export function ViewResultsTable({ products, metadata, onExport }: ViewResultsTableProps) {
  // Filter states
  const [filterAmazonListed, setFilterAmazonListed] = useState(false);
  const [filterAmazonBuybox, setFilterAmazonBuybox] = useState(false);
  const [filterMinScore, setFilterMinScore] = useState(0);
  const [sortBy, setSortBy] = useState<'score' | 'rank' | 'roi' | 'velocity'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Process and filter products
  const processedProducts = useMemo(() => {
    let filtered = [...products];

    // Filter by Amazon presence
    if (filterAmazonListed) {
      filtered = filtered.filter(p => p.amazon_on_listing);
    }
    if (filterAmazonBuybox) {
      filtered = filtered.filter(p => p.amazon_buybox);
    }

    // Filter by minimum score
    if (filterMinScore > 0) {
      filtered = filtered.filter(p => p.score >= filterMinScore);
    }

    // Sort
    filtered.sort((a, b) => {
      let compareValue = 0;

      switch (sortBy) {
        case 'score':
          compareValue = (a.score ?? 0) - (b.score ?? 0);
          break;
        case 'rank':
          compareValue = a.rank - b.rank;
          break;
        case 'roi':
          compareValue = (a.raw_metrics?.roi_pct ?? 0) - (b.raw_metrics?.roi_pct ?? 0);
          break;
        case 'velocity':
          compareValue = (a.raw_metrics?.velocity_score ?? 0) - (b.raw_metrics?.velocity_score ?? 0);
          break;
      }

      return sortOrder === 'desc' ? -compareValue : compareValue;
    });

    return filtered;
  }, [products, filterAmazonListed, filterAmazonBuybox, filterMinScore, sortBy, sortOrder]);

  // Stats
  const totalProducts = products.length;
  const withAmazon = products.filter(p => p.amazon_on_listing).length;
  const withBuybox = products.filter(p => p.amazon_buybox).length;
  const avgScore = metadata.avg_score;

  const handleExportCSV = () => {
    // Create CSV content with BOM for Excel FR/EU compatibility
    const BOM = '\uFEFF';
    const headers = [
      'RANK', 'ASIN', 'TITLE', 'SCORE', 'ROI', 'VELOCITY', 'ESTIMATED_SALES_30D',
      'MAX_BUY_35PCT', 'MARKET_SELL', 'MARKET_BUY', 'AMAZON_LISTED', 'AMAZON_BUYBOX'
    ];
    const rows = processedProducts.map(p => [
      p.rank,
      p.asin,
      `"${p.title || 'N/A'}"`,
      (p.score ?? 0).toFixed(2),
      `${(p.raw_metrics?.roi_pct ?? 0).toFixed(2)}%`,
      (p.raw_metrics?.velocity_score ?? 0).toFixed(0),
      p.velocity_breakdown?.estimated_sales_30d || 0,
      `$${(p.max_buy_price_35pct ?? 0).toFixed(2)}`,
      `$${(p.market_sell_price ?? 0).toFixed(2)}`,
      `$${(p.market_buy_price ?? 0).toFixed(2)}`,
      p.amazon_on_listing ? 'Yes' : 'No',
      p.amazon_buybox ? 'Yes' : 'No'
    ]);

    const csvContent = BOM + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `view_results_${metadata.view_type}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    if (onExport) onExport();
  };

  if (products.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8 text-center">
        <div className="text-4xl mb-4">📊</div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          Aucun produit à afficher
        </h3>
        <p className="text-sm text-gray-500">
          Lancez une analyse pour voir les résultats ici.
        </p>
      </div>
    );
  }

  // No results after filtering
  if (processedProducts.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-8">
        <div className="text-center">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Aucun résultat ne correspond aux filtres
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            {totalProducts} produits analysés, mais aucun ne correspond aux critères sélectionnés.
          </p>
          <button
            onClick={() => {
              setFilterAmazonListed(false);
              setFilterAmazonBuybox(false);
              setFilterMinScore(0);
            }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Réinitialiser les filtres
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden">
      {/* Header with stats */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {metadata.view_type.replace('_', ' ').toUpperCase()} - Résultats
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {totalProducts} produits • Score moyen: {avgScore.toFixed(1)} •
              {withAmazon} avec Amazon • {withBuybox} Buy Box
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

        {/* Filters */}
        <div className="flex gap-4 flex-wrap items-end">
          {/* Amazon Filters */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">Filtres Amazon</label>
            <div className="flex gap-2">
              <label className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={filterAmazonListed}
                  onChange={(e) => setFilterAmazonListed(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>Amazon Listed</span>
              </label>
              <label className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={filterAmazonBuybox}
                  onChange={(e) => setFilterAmazonBuybox(e.target.checked)}
                  className="rounded text-green-600 focus:ring-green-500"
                />
                <span>Buy Box</span>
              </label>
            </div>
          </div>

          {/* Min Score Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Score min</label>
            <input
              type="number"
              value={filterMinScore}
              onChange={(e) => setFilterMinScore(Number(e.target.value))}
              className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
              placeholder="0"
              min="0"
              max="100"
            />
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Trier par</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="score">Score</option>
              <option value="rank">Rank</option>
              <option value="roi">ROI</option>
              <option value="velocity">Velocity</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Ordre</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as typeof sortOrder)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="desc">Décroissant</option>
              <option value="asc">Croissant</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rank
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ASIN
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                ROI
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Velocity
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Max Buy (35%)
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Market Sell
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Market Buy
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amazon
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {processedProducts.map((product) => {
              // Defensive extraction of values with fallbacks
              const roiPct = product.raw_metrics?.roi_pct ?? 0;
              const velocityScore = product.raw_metrics?.velocity_score ?? 0;
              const marketSellPrice = product.market_sell_price ?? 0;
              const marketBuyPrice = product.market_buy_price ?? 0;
              const maxBuyPrice35pct = product.max_buy_price_35pct ?? 0;
              const productScore = product.score ?? 0;

              return (
                <tr key={product.asin} className="hover:bg-gray-50">
                  {/* Rank */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{product.rank}
                  </td>

                  {/* ASIN */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                    {product.asin}
                  </td>

                  {/* Title */}
                  <td className="px-6 py-4 text-sm text-gray-700">
                    <div className="max-w-xs truncate" title={product.title || ''}>
                      {product.title || 'N/A'}
                    </div>
                  </td>

                  {/* Score */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <span className="font-semibold text-blue-600">
                      {productScore.toFixed(1)}
                    </span>
                  </td>

                  {/* ROI with tooltip */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <div className="flex items-center justify-center gap-1">
                      <span className={`font-semibold ${
                        roiPct >= 30 ? 'text-green-600' :
                        roiPct >= 15 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {roiPct.toFixed(1)}%
                      </span>
                      <Tooltip
                        content={
                          <ROITooltip
                            currentROI={roiPct}
                            marketSellPrice={marketSellPrice}
                            marketBuyPrice={marketBuyPrice}
                          />
                        }
                      >
                        <InfoIcon />
                      </Tooltip>
                    </div>
                  </td>

                  {/* Velocity with tooltip */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="flex flex-col items-center">
                        <span className="font-semibold">{velocityScore.toFixed(0)}</span>
                        <div className="w-16 bg-gray-200 rounded-full h-1.5 mt-1">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full"
                            style={{ width: `${Math.min(velocityScore, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                      <Tooltip
                        content={
                          <VelocityTooltip
                            score={velocityScore}
                            breakdown={product.velocity_breakdown}
                          />
                        }
                      >
                        <InfoIcon />
                      </Tooltip>
                    </div>
                  </td>

                  {/* Max Buy (35%) with tooltip */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <div className="flex items-center justify-center gap-1">
                      <span className="font-semibold text-green-600">
                        ${maxBuyPrice35pct.toFixed(2)}
                      </span>
                      <Tooltip
                        content={
                          <MaxBuyTooltip
                            maxBuyPrice={maxBuyPrice35pct}
                            marketSellPrice={marketSellPrice}
                            targetROI={35}
                          />
                        }
                      >
                        <InfoIcon />
                      </Tooltip>
                    </div>
                  </td>

                  {/* Market Sell */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <span className="text-gray-700">
                      ${marketSellPrice.toFixed(2)}
                    </span>
                  </td>

                  {/* Market Buy */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <span className="text-gray-700">
                      ${marketBuyPrice.toFixed(2)}
                    </span>
                  </td>

                  {/* Amazon Badges */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <AmazonBadges
                      amazonOnListing={product.amazon_on_listing}
                      amazonBuybox={product.amazon_buybox}
                      size="sm"
                    />
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <button
                      className="text-blue-600 hover:text-blue-800 font-medium"
                      onClick={() => window.open(`https://www.amazon.com/dp/${product.asin}`, '_blank')}
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

      {/* Footer with weights info */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div>
            <span className="font-medium">Poids utilisés:</span> ROI {metadata.weights_used.roi} •
            Velocity {metadata.weights_used.velocity} • Stability {metadata.weights_used.stability}
          </div>
          {metadata.strategy_requested && (
            <div>
              <span className="font-medium">Stratégie:</span> {metadata.strategy_requested}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ViewResultsTable;
