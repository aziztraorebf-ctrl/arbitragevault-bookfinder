/**
 * AccordionContent - Phase 2.5A with Phase 5 Condition Breakdown
 * Container principal pour les 3 sections d'analyse détaillée + nouvelle section pricing by condition
 */

import type { AccordionContentProps } from './types'
import { RoiDetailsSection } from './RoiDetailsSection'
import { VelocityDetailsSection } from './VelocityDetailsSection'
import { RecommendationSection } from './RecommendationSection'
import { ConditionBreakdown } from './ConditionBreakdown'

export function AccordionContent({ product, isExpanded }: AccordionContentProps) {
  // Check if product has Phase 5 by_condition pricing
  const hasConditionPricing = product.pricing?.by_condition && Object.keys(product.pricing.by_condition).length > 0

  return (
    <div
      className={`
        transition-all duration-300 ease-in-out overflow-hidden
        ${isExpanded ? 'max-h-[1200px] opacity-100' : 'max-h-0 opacity-0'}
      `}
    >
      <div className="bg-gray-50 border-t border-gray-200 p-4 space-y-4">
        {/* Phase 5: Condition Breakdown - Full width if available */}
        {hasConditionPricing && (
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <ConditionBreakdown
              analysis={product}
              sourcePrice={product.pricing?.source_price}
            />
          </div>
        )}

        {/* Original 3-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Section ROI */}
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <RoiDetailsSection product={product} />
          </div>

          {/* Section Velocity */}
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <VelocityDetailsSection product={product} />
          </div>

          {/* Section Recommendation */}
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <RecommendationSection product={product} />
          </div>
        </div>
      </div>
    </div>
  )
}
