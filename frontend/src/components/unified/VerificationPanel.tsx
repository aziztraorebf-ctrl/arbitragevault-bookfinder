/**
 * VerificationPanel - Reusable component for product verification display
 * Used with UnifiedProductTable across all modules
 */

import type { VerificationResponse, VerificationStatus } from '../../services/verificationService'

interface VerificationPanelProps {
  result: VerificationResponse
}

const STATUS_BADGES: Record<VerificationStatus, { label: string; color: string; borderColor: string }> = {
  ok: { label: 'OK', color: 'text-green-700 bg-green-100', borderColor: 'border-green-500' },
  changed: { label: 'Modifie', color: 'text-yellow-700 bg-yellow-100', borderColor: 'border-yellow-500' },
  avoid: { label: 'Eviter', color: 'text-red-700 bg-red-100', borderColor: 'border-red-500' },
}

export function VerificationPanel({ result }: VerificationPanelProps) {
  const statusBadge = STATUS_BADGES[result.status] || STATUS_BADGES.avoid
  const buyOpportunities = result.buy_opportunities || []

  return (
    <div className={`border-l-4 ${statusBadge.borderColor} pl-4 py-3`}>
      {/* Status Badge and Message */}
      <div className="flex items-center gap-3 mb-3">
        <span className={`px-2 py-1 rounded text-xs font-semibold ${statusBadge.color}`}>
          {statusBadge.label}
        </span>
        <p className="text-sm font-medium text-gray-700">{result.message}</p>
      </div>

      {/* Current Data Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-3">
        {result.sell_price != null && (
          <div>
            <p className="text-xs text-gray-500">Prix vente NEW</p>
            <p className="text-sm font-semibold text-blue-600">${result.sell_price.toFixed(2)}</p>
          </div>
        )}
        {result.used_sell_price != null && (
          <div>
            <p className="text-xs text-gray-500">Prix vente USED</p>
            <p className="text-sm font-semibold text-purple-600">${result.used_sell_price.toFixed(2)}</p>
          </div>
        )}
        {result.current_bsr != null && (
          <div>
            <p className="text-xs text-gray-500">BSR actuel</p>
            <p className="text-sm font-semibold">#{result.current_bsr.toLocaleString()}</p>
          </div>
        )}
        {result.current_fba_count != null && result.current_fba_count >= 0 && (
          <div>
            <p className="text-xs text-gray-500">Vendeurs FBA</p>
            <p className="text-sm font-semibold">{result.current_fba_count}</p>
          </div>
        )}
        {buyOpportunities.length > 0 && (
          <div>
            <p className="text-xs text-gray-500">Opportunites</p>
            <p className="text-sm font-semibold text-green-600">{buyOpportunities.length} offres</p>
          </div>
        )}
      </div>

      {/* Amazon Warning */}
      {result.amazon_selling && (
        <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 mb-3">
          <p className="text-sm text-red-700 font-medium">
            Attention: Amazon vend ce produit directement
          </p>
        </div>
      )}

      {/* Buy Opportunities Table */}
      {buyOpportunities.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-gray-500 uppercase mb-2 font-semibold">
            Opportunites d'achat (Top {Math.min(buyOpportunities.length, 5)}):
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-2 py-1 text-left">Condition</th>
                  <th className="px-2 py-1 text-right">Prix Achat</th>
                  <th className="px-2 py-1 text-right">Livraison</th>
                  <th className="px-2 py-1 text-right">Total</th>
                  <th className="px-2 py-1 text-right">Vente</th>
                  <th className="px-2 py-1 text-right">Profit</th>
                  <th className="px-2 py-1 text-right">ROI</th>
                  <th className="px-2 py-1 text-center">FBA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {buyOpportunities.slice(0, 5).map((opp, idx) => {
                  const isNew = opp.is_new ?? opp.condition_code === 1
                  return (
                    <tr key={idx} className={idx === 0 ? 'bg-green-50' : ''}>
                      <td className="px-2 py-1.5">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-xs font-semibold ${
                            isNew ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                          }`}
                        >
                          {isNew ? 'NEW' : 'USED'}
                        </span>
                        <span className="ml-1 text-gray-500">{opp.condition}</span>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">${opp.price.toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right font-mono text-gray-500">
                        {opp.shipping > 0 ? `+$${opp.shipping.toFixed(2)}` : 'Gratuit'}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono font-semibold">
                        ${opp.total_cost.toFixed(2)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono font-semibold text-blue-600">
                        ${opp.sell_price.toFixed(2)}
                      </td>
                      <td
                        className={`px-2 py-1.5 text-right font-mono font-semibold ${
                          opp.profit > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        ${opp.profit.toFixed(2)}
                      </td>
                      <td
                        className={`px-2 py-1.5 text-right font-mono ${
                          opp.roi_percent > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {opp.roi_percent.toFixed(0)}%
                      </td>
                      <td className="px-2 py-1.5 text-center">
                        {opp.is_fba ? (
                          <span className="text-orange-600 font-semibold">FBA</span>
                        ) : (
                          <span className="text-gray-400">FBM</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {buyOpportunities.length > 0 && (
            <p className="text-xs text-gray-500 mt-2 italic">
              Meilleure offre: Acheter a ${buyOpportunities[0].total_cost.toFixed(2)} (
              {buyOpportunities[0].is_new ? 'NEW' : 'USED'}) -&gt; Vendre a $
              {buyOpportunities[0].sell_price.toFixed(2)} = ${buyOpportunities[0].profit.toFixed(2)} profit
            </p>
          )}
        </div>
      )}

      {/* No opportunities message */}
      {buyOpportunities.length === 0 && !result.amazon_selling && (
        <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-md px-3 py-2">
          <p className="text-xs text-yellow-700">
            Aucune opportunite d'achat profitable trouvee actuellement.
          </p>
        </div>
      )}

      {/* Changes List */}
      {result.changes.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-500 uppercase mb-1">Changements detectes:</p>
          <ul className="space-y-1">
            {result.changes.map((change, idx) => (
              <li
                key={idx}
                className={`text-xs px-2 py-1 rounded ${
                  change.severity === 'critical'
                    ? 'bg-red-50 text-red-700'
                    : change.severity === 'warning'
                    ? 'bg-yellow-50 text-yellow-700'
                    : 'bg-gray-50 text-gray-700'
                }`}
              >
                {change.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timestamp */}
      <p className="text-xs text-gray-400 mt-3">
        Verifie le: {new Date(result.verified_at).toLocaleString()}
      </p>
    </div>
  )
}
