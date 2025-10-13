/**
 * AmazonBadges Component - Phase 2.5A
 *
 * Displays Amazon presence indicators for products:
 * - Blue badge: Amazon has an offer on the listing
 * - Red badge: Amazon currently owns the Buy Box (high competition)
 *
 * Used in product tables, cards, and detail views.
 */

export interface AmazonBadgesProps {
  amazonOnListing: boolean;
  amazonBuybox: boolean;
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
}

export function AmazonBadges({
  amazonOnListing,
  amazonBuybox,
  size = 'md',
  showTooltip = true
}: AmazonBadgesProps) {
  // Show "No Amazon" text when no Amazon presence
  if (!amazonOnListing && !amazonBuybox) {
    return (
      <span className="inline-flex items-center text-sm text-gray-500">
        ❌ No Amazon
      </span>
    );
  }

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  };

  const sizeClass = sizeClasses[size];

  return (
    <div className="flex items-center gap-2">
      {amazonOnListing && (
        <span
          className={`inline-flex items-center rounded-full bg-blue-100 text-blue-800 font-medium ${sizeClass}`}
          title={showTooltip ? 'Amazon has an offer on this product' : undefined}
        >
          <svg
            className="w-3 h-3 mr-1"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          Amazon Listed
        </span>
      )}

      {amazonBuybox && (
        <span
          className={`inline-flex items-center rounded-full bg-red-100 text-red-800 font-medium ${sizeClass}`}
          title={showTooltip ? 'Amazon owns the Buy Box - High competition' : undefined}
        >
          <svg
            className="w-3 h-3 mr-1"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          Buy Box
        </span>
      )}
    </div>
  );
}

/**
 * Compact version - just icons without text
 */
export function AmazonBadgesCompact({
  amazonOnListing,
  amazonBuybox,
  showTooltip = true
}: Omit<AmazonBadgesProps, 'size'>) {
  if (!amazonOnListing && !amazonBuybox) {
    return null;
  }

  return (
    <div className="flex items-center gap-1">
      {amazonOnListing && (
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800"
          title={showTooltip ? 'Amazon Listed' : undefined}
        >
          <svg
            className="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      )}

      {amazonBuybox && (
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-100 text-red-800"
          title={showTooltip ? 'Amazon Buy Box - High competition' : undefined}
        >
          <svg
            className="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </span>
      )}
    </div>
  );
}

export default AmazonBadges;
