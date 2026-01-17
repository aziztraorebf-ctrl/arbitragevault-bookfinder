/**
 * AccordionContent - Expandable container for detailed product analysis
 * Displays condition breakdown (when available) and ROI/Velocity/Recommendation sections
 */

import React from 'react'
import type { AccordionContentProps } from './types.js'
import { ConditionBreakdown } from './ConditionBreakdown.js'
import { RecommendationSection } from './RecommendationSection.js'
import { RoiDetailsSection } from './RoiDetailsSection.js'
import { VelocityDetailsSection } from './VelocityDetailsSection.js'

const CARD_STYLES = 'bg-white rounded-lg border border-gray-200'

export function AccordionContent({ product, isExpanded }: AccordionContentProps): React.ReactElement {
  const byCondition = product.pricing?.by_condition
  const hasConditionPricing = byCondition !== undefined && Object.keys(byCondition).length > 0

  const expandedStyles = isExpanded
    ? 'max-h-[1200px] opacity-100'
    : 'max-h-0 opacity-0'

  return (
    <div className={`transition-all duration-300 ease-in-out overflow-hidden ${expandedStyles}`}>
      <div className="bg-gray-50 border-t border-gray-200 p-4 space-y-4">
        {hasConditionPricing && (
          <div className={`${CARD_STYLES} p-4`}>
            <ConditionBreakdown
              analysis={product}
              sourcePrice={product.pricing?.source_price}
            />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className={`${CARD_STYLES} p-3`}>
            <RoiDetailsSection product={product} />
          </div>

          <div className={`${CARD_STYLES} p-3`}>
            <VelocityDetailsSection product={product} />
          </div>

          <div className={`${CARD_STYLES} p-3`}>
            <RecommendationSection product={product} />
          </div>
        </div>
      </div>
    </div>
  )
}
