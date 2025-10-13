/**
 * AccordionContent - Phase 2.5A
 * Container principal pour les 3 sections d'analyse détaillée
 */

import type { AccordionContentProps } from './types'
import { RoiDetailsSection } from './RoiDetailsSection'
import { VelocityDetailsSection } from './VelocityDetailsSection'
import { RecommendationSection } from './RecommendationSection'

export function AccordionContent({ product, isExpanded }: AccordionContentProps) {
  return (
    <div
      className={`
        transition-all duration-300 ease-in-out overflow-hidden
        ${isExpanded ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'}
      `}
    >
      <div className="bg-gray-50 border-t border-gray-200 p-4">
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
