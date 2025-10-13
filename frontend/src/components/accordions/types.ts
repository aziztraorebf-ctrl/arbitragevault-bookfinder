/**
 * Types pour les composants Accordéon - Phase 2.5A
 * Affichage détaillé des métriques ROI/Velocity/Recommendation
 */

import type { ProductScore } from '../../types/views'

/**
 * Props communes pour tous les composants de section
 */
export interface AccordionSectionProps {
  product: ProductScore
}

/**
 * Props pour le contenu complet de l'accordéon
 */
export interface AccordionContentProps {
  product: ProductScore
  isExpanded: boolean
}
