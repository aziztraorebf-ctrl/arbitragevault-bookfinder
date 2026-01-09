/**
 * AccordionContent - Expandable detail section for product rows
 * Shows additional product information when row is expanded
 */

import type { DisplayableProduct } from '../../types/unified'

interface AccordionContentProps {
  product: DisplayableProduct
  isExpanded: boolean
}

export function AccordionContent({ product, isExpanded }: AccordionContentProps) {
  if (!isExpanded) return null

  // Calculate profit estimate using correct property names
  const estimatedProfit = product.market_buy_price && product.market_sell_price
    ? product.market_sell_price - product.market_buy_price
    : null

  return (
    <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 animate-in slide-in-from-top-2 duration-200">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pricing Details */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Prix et Marges
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Prix d'achat:</span>
              <span className="font-medium text-gray-900">
                {product.market_buy_price ? `$${product.market_buy_price.toFixed(2)}` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Prix de vente:</span>
              <span className="font-medium text-gray-900">
                {product.market_sell_price ? `$${product.market_sell_price.toFixed(2)}` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Profit estime:</span>
              <span className={`font-semibold ${estimatedProfit && estimatedProfit > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {estimatedProfit ? `$${estimatedProfit.toFixed(2)}` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">ROI:</span>
              <span className={`font-semibold ${product.roi_percent >= 30 ? 'text-green-600' : product.roi_percent >= 15 ? 'text-yellow-600' : 'text-red-600'}`}>
                {product.roi_percent.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Performance
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">BSR:</span>
              <span className="font-medium text-gray-900">
                {product.bsr ? `#${product.bsr.toLocaleString()}` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Velocite:</span>
              <span className="font-medium text-gray-900">
                {product.velocity_score.toFixed(0)}/100
              </span>
            </div>
            {product.score !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Score global:</span>
                <span className="font-semibold text-purple-600">
                  {product.score.toFixed(1)}
                </span>
              </div>
            )}
            {product.stability_score !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Stabilite:</span>
                <span className="font-medium text-gray-900">
                  {product.stability_score.toFixed(0)}/100
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Amazon Status */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Statut Amazon
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Amazon sur listing:</span>
              {product.amazon_on_listing ? (
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded font-medium">
                  OUI
                </span>
              ) : (
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                  NON
                </span>
              )}
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Amazon BuyBox:</span>
              {product.amazon_buybox ? (
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">
                  OUI
                </span>
              ) : (
                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded font-medium">
                  NON
                </span>
              )}
            </div>
            {product.category_name && (
              <div className="flex justify-between">
                <span className="text-gray-500">Categorie:</span>
                <span className="font-medium text-gray-900 text-right max-w-[150px] truncate">
                  {product.category_name}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendation badge if present */}
      {product.recommendation && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Recommandation:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              product.recommendation === 'STRONG_BUY' ? 'bg-green-600 text-white' :
              product.recommendation === 'BUY' ? 'bg-green-500 text-white' :
              product.recommendation === 'CONSIDER' ? 'bg-yellow-500 text-white' :
              'bg-red-500 text-white'
            }`}>
              {product.recommendation === 'STRONG_BUY' ? 'Achat Fort' :
               product.recommendation === 'BUY' ? 'Acheter' :
               product.recommendation === 'CONSIDER' ? 'Considerer' :
               'Passer'}
            </span>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="mt-4 pt-4 border-t border-gray-200 flex gap-3">
        <a
          href={`https://www.amazon.com/dp/${product.asin}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
        >
          Voir sur Amazon
        </a>
        <a
          href={`https://keepa.com/#!product/1-${product.asin}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-purple-600 hover:text-purple-800 hover:underline"
        >
          Voir sur Keepa
        </a>
      </div>
    </div>
  )
}
