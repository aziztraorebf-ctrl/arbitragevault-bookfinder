/**
 * Types pour les composants Accordeon - Phase 2.5A
 * Affichage detaille des metriques ROI/Velocity/Recommendation
 */

import type { ProductScore } from '../../types/views'
import type { DisplayableProduct } from '../../types/unified'

/**
 * Base product type that works with both ProductScore and DisplayableProduct
 * Uses DisplayableProduct as it's the unified superset type
 */
export type AccordionProductType = DisplayableProduct | ProductScore

/**
 * Props communes pour tous les composants de section
 */
export interface AccordionSectionProps {
  product: AccordionProductType
}

/**
 * Props pour le contenu complet de l'accordeon
 */
export interface AccordionContentProps {
  product: AccordionProductType
  isExpanded: boolean
}
