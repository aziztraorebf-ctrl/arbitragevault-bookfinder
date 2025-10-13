/**
 * Tooltip - Reusable tooltip component with info icon
 *
 * Displays detailed information on hover or click (mobile-friendly)
 *
 * Usage:
 *   <Tooltip content={<div>Detailed explanation...</div>}>
 *     <InfoIcon className="w-4 h-4" />
 *   </Tooltip>
 */

import { useState, useRef, useEffect, type ReactNode } from 'react';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Hide tooltip when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(event.target as Node)) {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isVisible]);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  };

  return (
    <div className="relative inline-block" ref={tooltipRef}>
      {/* Trigger */}
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
        className="cursor-help inline-flex items-center"
      >
        {children}
      </div>

      {/* Tooltip content */}
      {isVisible && (
        <div
          className={`
            absolute z-50 ${positionClasses[position]}
            bg-gray-900 text-white text-xs rounded-lg shadow-xl
            py-3 px-4 min-w-[300px] max-w-[400px]
            max-h-[80vh] overflow-y-auto
            pointer-events-auto
          `}
          style={{ whiteSpace: 'pre-line' }}
        >
          {/* Arrow */}
          <div
            className={`
              absolute w-2 h-2 bg-gray-900 transform rotate-45
              ${position === 'top' ? 'bottom-[-4px] left-1/2 -translate-x-1/2' : ''}
              ${position === 'bottom' ? 'top-[-4px] left-1/2 -translate-x-1/2' : ''}
              ${position === 'left' ? 'right-[-4px] top-1/2 -translate-y-1/2' : ''}
              ${position === 'right' ? 'left-[-4px] top-1/2 -translate-y-1/2' : ''}
            `}
          />

          {/* Content */}
          <div className="relative z-10">
            {content}
          </div>
        </div>
      )}
    </div>
  );
}

// Info icon component for tooltip trigger
export function InfoIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg
      className={`${className} text-gray-400 hover:text-blue-500 transition-colors`}
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
        clipRule="evenodd"
      />
    </svg>
  );
}
