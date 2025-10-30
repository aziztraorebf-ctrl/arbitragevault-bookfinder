/**
 * Products Table Component
 * Displays drill-down products with ROI, velocity, price, BSR
 */

interface Product {
  asin: string
  title?: string
  roi_percent: number
  velocity_score: number
  recommendation: string
  current_price?: number
  bsr?: number
  category_name?: string
  fba_fees?: number
  estimated_profit?: number
}

interface ProductsTableProps {
  products: Product[]
  title?: string
}

export function ProductsTable({ products, title = 'Produits Trouvés' }: ProductsTableProps) {
  if (products.length === 0) {
    return null
  }

  // Recommendation badge colors
  const getRecommendationBadge = (recommendation: string) => {
    const badges: Record<string, { label: string; color: string }> = {
      STRONG_BUY: { label: 'Achat Fort', color: 'bg-green-600 text-white' },
      BUY: { label: 'Acheter', color: 'bg-green-500 text-white' },
      CONSIDER: { label: 'Considérer', color: 'bg-yellow-500 text-white' },
      SKIP: { label: 'Passer', color: 'bg-red-500 text-white' },
    }
    return badges[recommendation] || { label: recommendation, color: 'bg-gray-500 text-white' }
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>📊</span>
          <span>{title}</span>
          <span className="text-sm font-normal text-gray-600">
            ({products.length} produits)
          </span>
        </h3>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                ASIN / Titre
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                ROI
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Vélocité
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Prix
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                BSR
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Recommandation
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {products.map((product) => {
              const badge = getRecommendationBadge(product.recommendation)
              return (
                <tr
                  key={product.asin}
                  className="hover:bg-gray-50 transition-colors"
                >
                  {/* ASIN / Title */}
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {product.title || product.asin}
                      </p>
                      <p className="text-xs text-gray-500 font-mono">
                        {product.asin}
                      </p>
                      {product.category_name && (
                        <p className="text-xs text-gray-400 mt-1">
                          {product.category_name}
                        </p>
                      )}
                    </div>
                  </td>

                  {/* ROI */}
                  <td className="px-6 py-4 text-center">
                    <span className="text-lg font-bold text-green-600">
                      {product.roi_percent.toFixed(1)}%
                    </span>
                    {product.estimated_profit !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        ${product.estimated_profit.toFixed(2)} profit
                      </p>
                    )}
                  </td>

                  {/* Velocity */}
                  <td className="px-6 py-4 text-center">
                    <span className="text-lg font-bold text-blue-600">
                      {product.velocity_score.toFixed(0)}
                    </span>
                  </td>

                  {/* Price */}
                  <td className="px-6 py-4 text-center">
                    {product.current_price !== undefined ? (
                      <div>
                        <span className="text-sm font-semibold text-gray-900">
                          ${product.current_price.toFixed(2)}
                        </span>
                        {product.fba_fees !== undefined && (
                          <p className="text-xs text-gray-500">
                            FBA: ${product.fba_fees.toFixed(2)}
                          </p>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400 text-sm">N/A</span>
                    )}
                  </td>

                  {/* BSR */}
                  <td className="px-6 py-4 text-center">
                    {product.bsr !== undefined ? (
                      <span className="text-sm text-gray-700 font-mono">
                        #{product.bsr.toLocaleString()}
                      </span>
                    ) : (
                      <span className="text-gray-400 text-sm">N/A</span>
                    )}
                  </td>

                  {/* Recommendation */}
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${badge.color}`}
                    >
                      {badge.label}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>Total: {products.length} produits</span>
          <div className="flex gap-6">
            <span>
              ROI moyen:{' '}
              <strong className="text-green-600">
                {(
                  products.reduce((sum, p) => sum + p.roi_percent, 0) / products.length
                ).toFixed(1)}
                %
              </strong>
            </span>
            <span>
              Vélocité moyenne:{' '}
              <strong className="text-blue-600">
                {(
                  products.reduce((sum, p) => sum + p.velocity_score, 0) /
                  products.length
                ).toFixed(0)}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
